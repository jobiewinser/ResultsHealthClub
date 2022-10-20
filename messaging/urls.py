from django.contrib import admin
from django.urls import path
from messaging.views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("chat/<str:messaging_whatsapp_number>/", chat_box, name="chat"),
    

    path("message-list/", message_list, name="message-list"),

    path("message-window/<str:customer_number>/<str:whatsappnumber_pk>/", message_window, name="message-window"),
    path('get-messaging-window/', get_messaging_section, name='get-messaging-window' ),
    path('get-message-list-row/', get_messaging_list_row, name='get-message-list-row' ),
    path('send-first-template-whatsapp/<str:lead_pk>/', send_first_template_whatsapp_htmx, name='send-first-template-whatsapp' ),
    
    path('messaging-get-modal-content/', get_modal_content, name='messaging-get-modal-content' ),
]