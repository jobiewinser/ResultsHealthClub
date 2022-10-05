from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from messaging import consumers
import os
# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns=[
                    re_path(
                        r"ws/chat/(?P<chat_box_whatsapp_number>\w+)/(?P<chat_box_site_pk>\w+)/$", consumers.ChatRoomConsumer.as_asgi()
                    ),
                ]

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WinserSystems.settings')
DJANGO_SETTINGS_MODULE = 'WinserSystems.settings'
application = ProtocolTypeRouter( 
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
               websocket_urlpatterns
            )
        ),
    }
)