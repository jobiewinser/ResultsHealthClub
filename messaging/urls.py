from django.contrib import admin
from django.urls import path
from messaging.views import message_window

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("chat/<str:chat_box_whatsapp_number>/", chat_box, name="chat"),
    path("message-window/<str:customer_number>/<str:chat_box_site_pk>/", message_window, name="message-window"),
]