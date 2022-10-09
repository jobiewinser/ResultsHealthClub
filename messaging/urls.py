from django.contrib import admin
from django.urls import path
from messaging.views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("chat/<str:chat_box_whatsapp_number>/", chat_box, name="chat"),
    path("message-window/<str:customer_number>/<str:chat_box_site_pk>/", message_window, name="message-window"),
    path('get-messaging-window/', get_messaging_section, name='get-messaging-window' ),
    path('get-message-list-row/', get_messaging_list_row, name='get-message-list-row' ),
    
]