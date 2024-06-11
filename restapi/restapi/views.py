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
from channels.layers import get_channel_layer
import aiohttp
import aiofiles
import asyncio
from asgiref.sync import sync_to_async
import datetime
import time
import imageio
import cv2
import numpy as np
import torch
import shutil

from .get_weather_data import get_weather_data
from .video_utils import download_video_from_url
from .image_processing_utils import grayscale, canny, gaussian_blur, region_of_interest, draw_fit_line, hough_lines, weighted_img, get_fitline

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
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if settings.DEBUG and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS:
            print("Internal debug request detected.")

        video_files = request.FILES.getlist('videoFiles')
        video_urls = request.POST.getlist('videoUrls')

        username = await get_username(request)  # 직접 비동기 함수 호출

        tasks = []
        video_filenames = []  # 비디오 파일 이름을 저장할 리스트
        for video_file in video_files:
            if video_file:
                video_filenames.append(video_file.name)  # 파일 이름 추가
                task = asyncio.create_task(self.handle_video_file(video_file, username))
                tasks.append(task)

        for video_url in video_urls:
            if video_url.strip():
                task = asyncio.create_task(self.handle_video_url(video_url.strip(), username))
                tasks.append(task)

        # 작업 시작 응답 보내기
        response_data = {
            'message': '비디오 처리가 시작되었습니다.',
            'tasksCount': len(tasks),
            'username': username,
            'videoFilenames': video_filenames  # 비디오 파일 이름 목록 추가
        }
        return JsonResponse(response_data)

    async def handle_video_file(self, video_file, username):
        user_dir = f'static/tmp/{username}/{video_file.name}'
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        file_path = f'{user_dir}/{video_file.name}'
        async with aiofiles.open(file_path, 'wb+') as f:
            for chunk in video_file.chunks():
                await f.write(chunk)
        video_file = await self.process_video_frames(user_dir, video_file.name)
        return video_file  # 이미지 URL 목록 반환

    async def handle_video_url(self, video_url, username):
        user_dir = f'tmp/{username}/{video_url.split("/")[-1]}/{video_url.split("/")[-1]}'
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        output_path = f'{user_dir}/{video_url.split("/")[-1]}'
        await download_video_from_url(video_url, output_path)  # 가정: 비디오 다운로드 ��수
        video_url = await self.process_video_frames(output_path)
        return video_url  # 이미지 URL 목록 반환

    async def process_video_frames(self, user_dir, filename):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
        model.eval()

        reader = imageio.get_reader(f'{user_dir}/{filename}')
        fps = reader.get_meta_data()['fps']
        writer = imageio.get_writer(f'{user_dir}/{filename}_output.mp4', fps=fps)
        for i, frame in enumerate(reader):
            try:
                frame_save_path = f'{user_dir}/{filename}_{i}.jpg'
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
                writer.append_data(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))  # 최종 결과를 RGB로 변하여 writer에 저장
                cv2.imwrite(frame_save_path, cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
            except Exception as e:
                continue
        writer.close()
        reader.close()
        output_file_path = f'{user_dir}/{filename}_output.mp4'
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

def process_video(request):
    return render(request, 'process_video.html')

def index(request):
    return render(request, 'index.html')

def profile_view(request):
    return render(request, 'profile.html')