from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from messaging import consumers

# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns=[
                    re_path(
                        r"ws/chat/(?P<chat_box_whatsapp_number>\w+)/(?P<chat_box_site_pk>\w+)/$", consumers.ChatConsumer.as_asgi()
                    ),
                    re_path(
                        r"ws/chatlist/(?P<chat_box_site_pk>\w+)/$", consumers.ChatListConsumer.as_asgi(),
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