from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework import status
import cv2
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from allauth.socialaccount.models import SocialApp
from django.conf import settings

from .process_video import process_video
from .get_weather_data import get_weather_data

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
    
class ProcessVideoURL(View):
    def post(self, request):
        video_url = request.POST.get('videoUrl')
        # URL로 비디오 처리 로직 구현
        return HttpResponse("비디오 URL 처리 완료")

class ProcessVideoUpload(View):
    def post(self, request):
        video_file = request.FILES.get('videoFile')
        if not video_file:
            return HttpResponse("파일이 제공되지 않았습니다.", status=400)

        # 파일 저장
        file_path = f'tmp/{video_file.name}'
        with open(file_path, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)

        # OpenCV를 사용하여 비디오 처리
        cap = cv2.VideoCapture(file_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                processed_image_url = f'tmp/processed_{video_file.name}.png'
                cv2.imwrite(processed_image_url, frame)
                cap.release()
                return JsonResponse({'imageUrl': processed_image_url})
            else:
                cap.release()
                return HttpResponse("비디오 프레임을 읽을 수 없습니다.", status=400)
        else:
            return HttpResponse("비디오 파일을 열 수 없습니다.", status=400)
        
class ManageAPIKey(View):
    def post(self, request):
        api_key = request.POST.get('apiKey')
        # API 키 저장 로직 구현
        return HttpResponse("API 키 저장 완료")

def process_video(request):
    return render(request, 'process_video.html')

def index(request):
    return render(request, 'index.html')