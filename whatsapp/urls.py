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
    path('configuration/whatsapp-template/<str:template_pk>/', whatsappviews.WhatsappTemplatesEditView.as_view(), name='whatsapp-template'),
    path('configuration/whatsapp-template/', whatsappviews.WhatsappTemplatesCreateView.as_view(), name='whatsapp-template'),
    path('configuration/whatsapp-template-delete/', whatsappviews.delete_whatsapp_template_htmx, name='whatsapp-template-delete'),
    path('configuration/whatsapp-templates-save/', whatsappviews.save_whatsapp_template_ajax, name='whatsapp-template-save'),
    path('configuration/whatsapp-templates-approval/', whatsappviews.whatsapp_approval_htmx, name='whatsapp-approval'),   
    path('configuration/whatsapp-templates/clear-changes/', whatsappviews.whatsapp_clear_changes_htmx, name='whatsapp-clear-changes'),    
    path('configuration/whatsapp-change-number-alias/', whatsappviews.whatsapp_number_change_alias, name='whatsapp-change-number-alias'),
    
    path('configuration/whatsapp-number-make-default  /', whatsappviews.whatsapp_number_make_default, name='whatsapp-number-make-default'),
      
    path('configuration/whatsapp-change-template-site/', whatsappviews.whatsapp_template_change_site, name='whatsapp-change-template-site'),    
    path('configuration/whatsapp-change-number-site/', whatsappviews.whatsapp_number_change_site, name='whatsapp-change-number-site'),    
]    