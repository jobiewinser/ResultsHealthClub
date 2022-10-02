from django.contrib import admin
from django.urls import path
from messaging.views import leads_message_window

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("chat/<str:chat_box_name>/", chat_box, name="chat"),
    path("leads-message-window/<int:lead_pk>/", leads_message_window, name="leads-message-window"),
]