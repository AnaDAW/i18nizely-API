from django.urls import re_path
from .consumers import ProjectConsumer

websocket_urlpatterns = [
    re_path(r'ws/projects/(?P<project_id>\d+)/$', ProjectConsumer.as_asgi()),
]