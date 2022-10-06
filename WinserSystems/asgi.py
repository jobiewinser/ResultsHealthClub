import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from messaging import consumers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WinserSystems.settings')

django.setup()

websocket_urlpatterns=[
                    re_path(
                        r"ws/chat/(?P<chat_box_whatsapp_number>\w+)/(?P<chat_box_site_pk>\w+)/$", consumers.ChatRoomConsumer.as_asgi()
                    ),
                ]

application = ProtocolTypeRouter( 
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
               websocket_urlpatterns
            )
        ),
    }
)