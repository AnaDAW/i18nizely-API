import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from projects.models import Project

class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_{self.project_id}'
        self.user = self.scope['user']
        project = await sync_to_async(lambda: Project.objects.filter(id=self.project_id).first())()
        if not self.user.is_authenticated or not project:
            await self.close()
            return
        is_collaborators = await sync_to_async(lambda: project.collaborators.filter(user=self.user).exists())()
        created_by = await sync_to_async(lambda: project.created_by)()
        if created_by != self.user and not is_collaborators:
            await self.close()
            return
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['data']))