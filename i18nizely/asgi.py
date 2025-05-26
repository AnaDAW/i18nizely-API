"""
ASGI config for i18nizely project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

import django
from django.core.asgi import get_asgi_application

from utils.language_util import LanguageUtil


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'i18nizely.settings')
django.setup()
LanguageUtil.init_languages()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from projects.routing import websocket_urlpatterns
from projects.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})