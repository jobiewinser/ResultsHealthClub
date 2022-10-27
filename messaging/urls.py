from django.contrib import admin
from django.urls import path
from messaging.views import *

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("chat/<str:messaging_whatsapp_number>/", chat_box, name="chat"),
    

    path("message-list/", message_list, name="message-list"),

    path("message-window/<str:customer_number>/<str:whatsappnumber_pk>/", message_window, name="message-window"),
    path("message-window/<str:customer_number>/", message_window, name="message-window"),
    path('get-messaging-window/', get_messaging_section, name='get-messaging-window' ),
    path('get-message-list-row/', get_messaging_list_row, name='get-message-list-row' ),
    path('send-first-template-whatsapp/<str:lead_pk>/', send_first_template_whatsapp_htmx, name='send-first-template-whatsapp' ),
    
    path('get-more-messages/', get_more_messages, name='get-more-messages' ),
    path('messaging-get-modal-content/', get_modal_content, name='messaging-get-modal-content' ),
    path('update-message-counts/', update_message_counts, name='update-message-counts' ),
    
    path('ajax-clear-chat-from-session/', clear_chat_from_session, name='clear-chat-from-session' ),
    path('ajax-add-chat-whatsapp-number-to-session/', add_chat_whatsapp_number_to_session, name='add-chat-whatsapp-number-to-session' ),
    path('ajax-add-chat-conversation-to-session/', add_chat_conversation_to_session, name='add-chat-conversation-to-session' ),
]