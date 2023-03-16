from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from messaging import consumers

from django.urls import path
# URLs that handle the WebSocket connection are placed here.
websocket_urlpatterns=[
                    # re_path(
                    #     r"ws/messaging/(?P<messaging_whatsapp_number>\w+)/(?P<messaging_phone_number>\w+)/$", consumers.MessagingConsumer.as_asgi()
                    # ),
                    path('ws/messaging/<str:whatsappnumber_pk>/', consumers.MessagingConsumer.as_asgi()),
                    path('ws/lead/<str:company_pk>/', consumers.LeadsConsumer.as_asgi()),
                    path('ws/chat/<str:whatsappnumber_pk>/<str:site_contact_pk>/', consumers.ChatConsumer.as_asgi()),
                    path('ws/message_count/<str:company_pk>/', consumers.CompanyMessageCountConsumer.as_asgi()),
                    
                    # re_path(
                    #     r"ws/chatlist/(?P<messaging_phone_number>\w+)/$", consumers.ChatListConsumer.as_asgi(),
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