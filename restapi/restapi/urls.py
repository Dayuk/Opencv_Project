from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

from .views import index, process_video, ProcessVideoUpload, weather, myapi

urlpatterns = [
    path('', index, name='index'),

    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # 비디오 처리 관련 URL
    path('process_video/', process_video, name='process_video'),
    path('process_video_upload/', ProcessVideoUpload.as_view(), name='process_video_upload'),
    
    path('weather/', weather, name='weather'),

    path('api/', myapi, name='myapi'),
]

urlpatterns += [
    path('api/create_key/', views.create_api_key, name='create_api_key'),
    path('api/refresh_key/', views.refresh_api_key, name='refresh_api_key'),
    path('api/get_api_key/', views.get_api_key, name='get_api_key'),
    path('api/v1/weather/', views.v1_weather_api, name='v1_weather_api'),
    path('api/v1/car_recognition/image/', views.v1_car_recognition_api_image, name='v1_car_recognition_api_image'),
    path('api/v1/car_recognition/youtube/', views.v1_car_recognition_api_youtube, name='v1_car_recognition_api_youtube'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)