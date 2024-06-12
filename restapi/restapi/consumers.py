from channels.generic.websocket import AsyncWebsocketConsumer
import json

class VideoProcessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # URL 경로에서 username을 추출합니다.
        username = self.scope['url_route']['kwargs']['username']
        self.room_group_name = f'video_process_{username}'  # room_group_name을 동적으로 설정합니다.

        # 사용자를 해당 그룹에 추가합니다.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # WebSocket 연결을 수락합니다.
        await self.accept()

    async def disconnect(self, close_code):
        # 연결이 끊어지면 사용자를 그룹에서 제거합니다.
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # 클라이언트로부터 메시지를 받습니다.
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # 그룹에 메시지를 전송합니다.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_process_message',
                'message': message
            }
        )

    async def video_process_message(self, event):
        # 그룹에서 메시지를 받아 클라이언트에 전송합니다.
        message = event['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
