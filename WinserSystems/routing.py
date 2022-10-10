from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from messaging import consumers

from django.urls import path
# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns=[
                    # re_path(
                    #     r"ws/chatlistrow/(?P<chat_box_whatsapp_number>\w+)/(?P<chat_box_site_pk>\w+)/$", consumers.ChatConsumer.as_asgi()
                    # ),
                    path('ws/chatlistrow/<str:chat_box_site_pk>/', consumers.ChatConsumer.as_asgi()),
                    # re_path(
                    #     r"ws/chatlist/(?P<chat_box_site_pk>\w+)/$", consumers.ChatListConsumer.as_asgi(),
                    # ),
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