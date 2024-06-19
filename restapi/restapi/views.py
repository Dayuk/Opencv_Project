import cv2
import os
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.contrib.auth import get_user
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
import aiofiles
import asyncio
from asgiref.sync import sync_to_async
import imageio
import cv2
import uuid
import shutil
import logging
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor
import base64
from PIL import Image
import io
from .settings import STATICFILES_DIRS, MODEL
import threading

from .models import APIKey
from .get_weather_data import get_weather_data
from .process_image import process_image
from .youtube_process_video import download_and_process_video

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
            if os.path.isfile(file_path) and file_path != keep_file and '_output' not in file_path:
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(f'Failed to delete {file_path}. Reason: {e}')

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
                total_chunks += sum(1 for _ in video_file.chunks())

        for video_url in video_urls:
            if video_url.strip():
                task = loop.create_task(self.handle_video_url(video_url.strip(), username))
                tasks.append(task)

        # 모든 비동기 작업이 완료될 때까지 기다립니다.
        completed_tasks = await asyncio.gather(*tasks)

        # ThreadPoolExecutor를 사용하여 비디오 프레임 처리를 별도의 스레드에서 실행합니다.
        executor = ThreadPoolExecutor(max_workers=2)
        executor.submit(self.run_process_video_frames, f'{STATICFILES_DIRS}/tmp/{username}/{self.random_filename}', self.random_filename, username)

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
        user_dir = f'{STATICFILES_DIRS}/tmp/{username}/{self.random_filename}'
        os.makedirs(user_dir, exist_ok=True)  # 디렉토리가 이미 존재해도 오류를 발생시키지 않음
        file_path = f'{user_dir}/{self.random_filename}'
        async with aiofiles.open(file_path, 'wb+') as f:
            for chunk in video_file.chunks():  # 동기적으로 청크 읽기
                await f.write(chunk)  # 비동기적으로 파일 쓰기
        return file_path  # 파일 경로 반환

    async def handle_video_url(self, video_url, username):
        user_dir = f'{STATICFILES_DIRS}/tmp/{username}'
        os.makedirs(user_dir, exist_ok=True)  # 디렉토리가 이미 존재해도 오류를 발생시키지 않음
        random_filename = f"{uuid.uuid4()}.mp4"  # 랜덤한 파일 이름 생성
        output_path = f'{user_dir}/{random_filename}'
        
        # 유튜브 URL에서 비디오 다운로드
        await self.download_video_from_youtube(video_url, output_path)  # 가정: 유튜브 다운로드 함수
        
        return output_path

    async def download_video_from_youtube(self, video_url, output_path):
        ydl_opts = {
            'format': 'bestvideo[height<=720]',  # 720p 이하의 최고 화질 비디오만 다운로드
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # 비디오 포맷을 mp4로 설정
            }],
            'external_downloader_args': {
                'ffmpeg': ['-t', '180']  # 비디오를 180초(3분)로 제한
            }
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

    def run_process_video_frames(self, path, filename, username):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            new_loop.run_until_complete(self.process_video_frames(path, filename, username))
        finally:
            new_loop.close()

    async def process_video_frames(self, user_dir, filename, username):
        try:
            logger.debug(f"Processing video frames for {filename} in directory {user_dir}")

            reader = imageio.get_reader(f'{user_dir}/{filename}')
            fps = reader.get_meta_data()['fps']
            writer = imageio.get_writer(f'{user_dir}/{filename}_output.mp4', fps=fps)
            image_index = 0

            #차선 인식 코드는 불안정하여 제거

            # 클라이언트에 'start' 메시지 전송
            channel_layer = get_channel_layer()
            room_group_name = f'process_video_{username}'  # WebSocket 경로 설정
            await channel_layer.group_send(
                room_group_name,
                {
                    'type': 'video_process_message',
                    'message': 'start'
                }
            )

            for i, frame in enumerate(reader):
                try:
                    preds = MODEL(frame)
                    preds = preds.pandas().xyxy[0]
                    for index, row in preds.iterrows():
                        if row['confidence'] > 0.4:
                            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, f'car {row["confidence"]:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # 최종 결과를 RGB로 변환하여 writer에 저장
                    if i % 100 == 0:
                        frame_save_path = f'{user_dir}/{filename}_{image_index}.webp'
                        cv2.imwrite(frame_save_path, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        image_index += 1
                except Exception as e:
                    logger.error(f"Error processing video {filename}: {e}", exc_info=True)
                    continue
        finally:    
            writer.close()
            reader.close()
            output_file_path = f'{user_dir}/{filename}_output.mp4'
            
            # 비디오 처리가 완료된 후:
            channel_layer = get_channel_layer()
            room_group_name = f'process_video_{username}'  # WebSocket 경로 설정
            await channel_layer.group_send(
                room_group_name,
                {
                    'type': 'video_process_message',
                    'message': 'completed'
                }
            )
            clean_up_directory(user_dir, f'{user_dir}/{filename}_output.mp4')
            return output_file_path

async def get_username(request):
    user = await sync_to_async(get_user)(request)
    return user.username if user.is_authenticated else 'anonymous'

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def process_video(request):
    username = request.user.username  # 로그인된 사용자의 이름을 가져옵니다.
    return render(request, 'process_video.html', {'username': username})

@login_required
def weather(request):
    ip_address = get_client_ip(request)

    weather_data = get_weather_data(ip_address)
    
    if weather_data:
        context = {
            'weather_date': weather_data['date'],
            'weather_location': weather_data['location'],
            'weather_icon': weather_data['icon'],  # 이미지 파일 이름
            'weather_status': weather_data['status'],
            'temperature': weather_data['temperature'],
            'humidity': weather_data['humidity'],
        }
    else:
        context = {
            'weather_date': '데이터를 가져올 수 없습니다.',
            'weather_location': '',
            'weather_icon': '맑음',  # 기본 이미지
            'weather_status': '',
            'temperature': '',
            'humidity': '',
        }
    
    return render(request, 'weather.html', context)

def index(request):
    return render(request, 'index.html')

def profile_view(request):
    return render(request, 'profile.html')

def myapi(request):
    return render(request, 'myapi.html')

@login_required
def create_api_key(request):
    new_key_value = APIKey.generate_key()  # 유니크한 키 생성
    new_key, created = APIKey.objects.get_or_create(user=request.user, defaults={'key': new_key_value})
    if not created:
        # 이미 키가 존재하는 경우, 새로운 키를 생성하고 저장
        new_key.key = new_key_value
        new_key.save()
    return JsonResponse({'key': str(new_key.key)})

@login_required
def refresh_api_key(request):
    try:
        old_key = APIKey.objects.get(user=request.user)
        old_key.key = APIKey.generate_key()
        old_key.save()
        return JsonResponse({'new_key': str(old_key.key)})
    except APIKey.DoesNotExist:
        return JsonResponse({'error': 'API key does not exist'}, status=404)

@login_required
def get_api_key(request):
    try:
        api_key = APIKey.objects.get(user=request.user)
    except APIKey.DoesNotExist:
        # APIKey가 존재하지 않는 경우, 새로운 키를 생성하고 저장
        new_key_value = APIKey.generate_key()
        api_key = APIKey.objects.create(user=request.user, key=new_key_value)
    return JsonResponse({'key': str(api_key.key)})

def v1_weather_api(request):
    api_key = request.headers.get('X-API-KEY')
    ip_address = request.headers.get('X-IP-ADDRESS')

    try:
        # APIKey 모델에서 제공된 API 키가 유효한지 확인
        APIKey.objects.get(key=api_key)
    except APIKey.DoesNotExist:
        return JsonResponse({'error': 'Invalid API key'}, status=401)

    # IP 주소를 사용하여 날씨 데이터 가져오기
    weather_data = get_weather_data(ip_address)

    if weather_data:
        response_data = {
            'date': weather_data['date'],
            'location': weather_data['location'],
            'icon': weather_data['icon'],
            'status': weather_data['status'],
            'temperature': weather_data['temperature'],
            'humidity': weather_data['humidity'],
        }
    else:
        response_data = {
            'error': 'Weather data not available'
        }

    return JsonResponse(response_data)

def v1_car_recognition_api_image(request):
    if request.method == 'PUT':
        api_key = request.headers.get('X-API-KEY')
        image_data = request.headers.get('X-BASE64-INCODE-IMAGE')

        try:
            # APIKey 모델에서 제공된 API 키가 유효한지 확인
            APIKey.objects.get(key=api_key)
        except APIKey.DoesNotExist:
            return JsonResponse({'Unauthorized Error': 'Invalid API key'}, status=401)

        try:
            if image_data:
                # base64로 인코딩된 이미지 데이터를 디코딩
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))

                # 이미지 처리를 비동기로 수행하고 결과를 반환
                def process_and_respond():
                    processed_image = process_image(image, api_key)  # 이미지 처리 함수 가정
                    response_data = {
                        'processed_image': processed_image
                    }
                    return JsonResponse(response_data, status=200)

                # 응답을 202 Accepted로 먼저 보내고 처리를 계속합니다.
                response = JsonResponse({'message': 'Processing image, please wait...'}, status=202)
                threading.Thread(target=process_and_respond).start()
                return response
            else:
                return JsonResponse({'Not Found Error': 'No valid image'}, status=404)
        except Exception as e:
            return JsonResponse({'Internal Server Error': 'An error occurred while processing the image'}, status=500)
    else:
        return JsonResponse({'Bad Request': 'Invalid HTTP method'}, status=405)

def v1_car_recognition_api_youtube(request):
    if request.method == 'POST':
        api_key = request.headers.get('X-API-KEY')
        youtube_link = request.headers.get('X-YOUTUBE-LINK')
        youtube_starttime = int(request.headers.get('X-YOUTUBE-STARTTIME-SECONDS', 0))
        youtube_endtime = int(request.headers.get('X-YOUTUBE-ENDTIME-SECONDS', 0))

        try:
            # APIKey 모델에서 제공된 API 키가 유효한지 확인
            APIKey.objects.get(key=api_key)
        except APIKey.DoesNotExist:
            return JsonResponse({'Unauthorized Error': 'Invalid API key'}, status=401)

        # 시작 시간과 끝나는 시간을 초 단위로 계산
        duration = youtube_endtime - youtube_starttime
        # 최대 3분(180초)으로 제한
        if duration > 180:
            return JsonResponse({'Not Acceptable Error': 'Video duration exceeds 3 minutes'}, status=406)

        def process_and_respond():
            youtube_video = download_and_process_video(youtube_link, youtube_starttime, youtube_endtime, api_key)
            response_data = {
                'youtube_video': youtube_video
            }
            return JsonResponse(response_data, status=200)

        # 응답을 202 Accepted로 먼저 보내고 처리를 계속합니다.
        response = JsonResponse({'message': 'Processing video, please wait...'}, status=202)
        threading.Thread(target=process_and_respond).start()
        return response
    else:
        return JsonResponse({'Bad Request': 'Invalid HTTP method'}, status=405)
