from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework import status
import cv2
import numpy as np
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
import aiohttp
import aiofiles
import asyncio
from asgiref.sync import sync_to_async, async_to_sync
import datetime
import time
import imageio
import cv2
import uuid
import numpy as np
import torch
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('video_processing_debug.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

from .get_weather_data import get_weather_data
from .video_utils import download_video_from_url
from .image_processing_utils import grayscale, canny, gaussian_blur, region_of_interest, draw_fit_line, hough_lines, weighted_img, get_fitline

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('video_processing_debug.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def clean_up_directory(directory, keep_file):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) and file_path != keep_file:
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

class WeatherAPIView(APIView):
    def get(self, request):
        # 날씨 데이터 가져오기
        # weather_data = get_weather_data()
        return Response("weather_data")

class OpenCVAPIView(APIView):
    def get(self, request):
        video_url = request.query_params.get('video_url')
        result = process_video(video_url)
        return Response(result)

class ProcessVideoUpload(View):
    async def post(self, request):
        # 현재 실행 중인 이벤트 루프를 가져오거나 없으면 새로 만듭니다.
        loop = asyncio.get_event_loop()

        video_files = request.FILES.getlist('videoFiles')
        video_urls = request.POST.getlist('videoUrls')

        username = await get_username(request)

        total_chunks = 0  # 청크 개수를 저장할 변수 초기화

        tasks = []
        for video_file in video_files:
            if video_file:
                task = loop.create_task(self.handle_video_file(video_file, username))
                tasks.append(task)
                total_chunks += sum(1 for _ in video_file.chunks()) // 50  # 청크 개수를 50으로 나눕니다.

        for video_url in video_urls:
            if video_url.strip():
                task = loop.create_task(self.handle_video_url(video_url.strip(), username))
                tasks.append(task)

        # 모든 비동기 작업이 완료될 때까지 기다립니다.
        completed_tasks = await asyncio.gather(*tasks)

        # ThreadPoolExecutor를 사용하여 비디오 프레임 처리를 별도의 스레드에서 실행합니다.
        executor = ThreadPoolExecutor()
        executor.submit(self.run_process_video_frames, f'static/tmp/{username}/{self.random_filename}', self.random_filename, username)

        # 응답을 즉시 반환합니다. 프레임 처리는 백그라운드에서 계속 진행됩니다.
        response_data = {
            'username': username,
            'tasks' : len(completed_tasks),
            'videoFilename': self.random_filename,
            'totalChunks': total_chunks  # 청크 개수를 응답 데이터에 추가
        }
        return JsonResponse(response_data)

    async def handle_video_file(self, video_file, username):
        self.random_filename = f"{uuid.uuid4()}{os.path.splitext(video_file.name)[1]}"  # 확장자를 유지하면서 랜덤한 파일 이름 생성
        user_dir = f'static/tmp/{username}/{self.random_filename}'
        os.makedirs(user_dir, exist_ok=True)  # 디렉토리가 이미 존재해도 오류를 발생시키지 않음
        file_path = f'{user_dir}/{self.random_filename}'
        async with aiofiles.open(file_path, 'wb+') as f:
            for chunk in video_file.chunks():  # 동기적으로 청크 읽기
                await f.write(chunk)  # 비동기적으로 파일 쓰기
        return file_path  # 파일 경로 반환

    async def handle_video_url(self, video_url, username):
        user_dir = f'tmp/{username}/{video_url.split("/")[-1]}/{video_url.split("/")[-1]}'
        os.makedirs(user_dir, exist_ok=True)  # 디렉토리가 이미 존재해도 오류를 발생시키지 않음
        output_path = f'{user_dir}/{video_url.split("/")[-1]}'
        await download_video_from_url(video_url, output_path)  # 가정: 비디오 다운로드 함수
        video_url = await self.process_video_frames(output_path)
        return video_url  # 이미지 URL 목록 반환

    def run_process_video_frames(self, path, filename, username):
        # 새 이벤트 루프를 생성하고 코루틴을 실행합니다.
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            new_loop.run_until_complete(self.process_video_frames(path, filename, username))
        finally:
            new_loop.close()

    async def process_video_frames(self, user_dir, filename, username):
        try:
            logger.debug(f"Processing video frames for {filename} in directory {user_dir}")

            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
            model.eval()

            reader = imageio.get_reader(f'{user_dir}/{filename}')
            fps = reader.get_meta_data()['fps']
            writer = imageio.get_writer(f'{user_dir}/{filename}_output.mp4', fps=fps)
            image_index = 0
            for i, frame in enumerate(reader):
                try:
                    frame_save_path = f'{user_dir}/{filename}_{image_index}.jpg'
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # imageio로 읽은 이미지를 cv2 처리 가능한 BGR 포맷으로 변환
                    height, width = frame.shape[:2]
                    gray_img = grayscale(frame)
                    blur_img = gaussian_blur(gray_img, 3)
                    canny_img = canny(blur_img, 70, 210)
                    vertices = np.array([[(0, height), (width / 2, height / 2 +100), (width / 2, height / 2 +100), (width, height)]], dtype=np.int32)
                    ROI_img = region_of_interest(canny_img, vertices)
                    line_arr = hough_lines(ROI_img, 1, 1 * np.pi / 180, 30, 10, 20)
                    line_arr = np.squeeze(line_arr)
                    slope_degree = (np.arctan2(line_arr[:, 1] - line_arr[:, 3], line_arr[:, 0] - line_arr[:, 2]) * 180) / np.pi
                    line_arr = line_arr[np.abs(slope_degree) < 150]
                    slope_degree = slope_degree[np.abs(slope_degree) < 150]
                    line_arr = line_arr[np.abs(slope_degree) > 95]
                    slope_degree = slope_degree[np.abs(slope_degree) > 95]
                    L_lines, R_lines = line_arr[(slope_degree > 0), :], line_arr[(slope_degree < 0), :]
                    if not L_lines.size or not R_lines.size:  # 선 배열이 비어 있는지 확인
                        print("No lines detected")
                        return None
                    temp = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
                    L_lines, R_lines = L_lines[:, None], R_lines[:, None]
                    left_fit_line = get_fitline(frame, L_lines)
                    right_fit_line = get_fitline(frame, R_lines)
                    fit_line_xy = np.array([[left_fit_line[0], left_fit_line[1]], [right_fit_line[0],right_fit_line[1]], [left_fit_line[2]+15, left_fit_line[3]+15], [right_fit_line[2]-15,right_fit_line[3]-15]], np.int32)
                    draw_fit_line(temp, fit_line_xy)
                    result = weighted_img(temp, frame)
                    preds = model(frame)
                    preds = preds.pandas().xyxy[0]
                    for index, row in preds.iterrows():
                        if row['confidence'] > 0.4:
                            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                            cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(result, f'car {row["confidence"]:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    writer.append_data(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))  # 최종 결과를 RGB로 변환하여 writer에 저장
                    if i % 30 == 0:  # 30프레임마다 한 번씩만 이미지를 저장합니다.
                        frame_save_path = f'{user_dir}/{filename}_{image_index}.jpg'
                        cv2.imwrite(frame_save_path, cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
                        image_index += 1
                except Exception as e:
                    logger.error(f"Error processing video {filename}: {e}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"Error processing video {filename}: {e}", exc_info=True)
            raise e
        writer.close()
        reader.close()
        output_file_path = f'{user_dir}/{filename}_output.mp4'
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'video_process_{username}', 
            {
                'type': 'video_process_message',
                'message': 'completed'
            }
        )
        clean_up_directory(user_dir, output_file_path)
        return output_file_path

async def get_username(request):
    user = await sync_to_async(get_user)(request)
    return user.username if user.is_authenticated else 'anonymous'

class ManageAPIKey(View):
    def post(self, request):
        api_key = request.POST.get('apiKey')
        # API 키 저장 로직 구현
        return HttpResponse("API 키 저장 완료")

@login_required
def process_video(request):
    username = request.user.username  # 로그인된 사용자의 이름을 가져옵니다.
    return render(request, 'process_video.html', {'username': username})

def index(request):
    return render(request, 'index.html')

def profile_view(request):
    return render(request, 'profile.html')