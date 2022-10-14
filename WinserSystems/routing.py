from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from messaging import consumers

from django.urls import path
# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns=[
                    # re_path(
                    #     r"ws/messaging/(?P<messaging_whatsapp_number>\w+)/(?P<messaging_site_pk>\w+)/$", consumers.ChatConsumer.as_asgi()
                    # ),
                    path('ws/messaging/<str:messaging_site_pk>/', consumers.ChatConsumer.as_asgi()),
                    path('ws/lead/<str:company_pk>/', consumers.LeadsConsumer.as_asgi()),
                    
                    # re_path(
                    #     r"ws/chatlist/(?P<messaging_site_pk>\w+)/$", consumers.ChatListConsumer.as_asgi(),
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