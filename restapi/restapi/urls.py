from django.urls import path, include
from django.contrib import admin

from .views import index, process_video, WeatherAPIView, ProcessVideoURL, ProcessVideoUpload

urlpatterns = [
    path('', index, name='index'),

    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),

    path('process_video/', process_video, name='process_video'),
    path('process_video_url/', ProcessVideoURL.as_view(), name='process_video_url'),
    path('process_video_upload/', ProcessVideoUpload.as_view(), name='process_video_upload'),
    path('weather/', WeatherAPIView.as_view(), name='weather'),
]