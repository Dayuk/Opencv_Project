from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

from .views import index, process_video, WeatherAPIView, ProcessVideoURL, ProcessVideoUpload

urlpatterns = [
    path('', index, name='index'),

    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('process_video/', process_video, name='process_video'),
    path('process_video_url/', ProcessVideoURL.as_view(), name='process_video_url'),
    path('process_video_upload/', ProcessVideoUpload.as_view(), name='process_video_upload'),
    path('weather/', WeatherAPIView.as_view(), name='weather'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)