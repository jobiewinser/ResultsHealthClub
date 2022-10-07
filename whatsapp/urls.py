"""jobiewebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
import whatsapp.views as whatsappviews
urlpatterns = [
    path('whatsapp-webhooks/', whatsappviews.Webhooks.as_view(), name='whatsapp-webhooks' ),
    path('ajax-clear-chat-from-session/', whatsappviews.clear_chat_from_session, name='clear-chat-from-session' ),
    path('ajax-add-chat-to-session/', whatsappviews.add_chat_to_session, name='add-chat-to-session' ),
    path('configuration/whatsapp-templates/', whatsappviews.WhatsappTemplatesView.as_view(), name='whatsapp-templates'),
    path('configuration/whatsapp-templates/<str:template_id>/<str:site_pk>/', whatsappviews.WhatsappTemplatesEditView.as_view(), name='whatsapp-templates'),
    path('configuration/whatsapp-templates/delete/', whatsappviews.delete_whatsapp_template_htmx, name='whatsapp-templates-delete'),
]