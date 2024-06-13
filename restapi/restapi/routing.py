from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, re_path
from .consumers import VideoProcessConsumer

websocket_urlpatterns = [
    re_path(r'^ws/process_video/process_video_(?P<username>\w+)/$', VideoProcessConsumer.as_asgi()),
]

