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
import whatsapp.htmx as whatsapphtmx
urlpatterns = [
    path('whatsapp-webhooks/', whatsappviews.Webhooks.as_view(), name='whatsapp-webhooks' ),
    
    path('configuration/whatsapp-templates/', whatsappviews.WhatsappTemplatesView.as_view(), name='whatsapp-templates'),
    path('configuration/whatsapp-template/<str:template_pk>/', whatsappviews.WhatsappTemplatesEditView.as_view(), name='whatsapp-template'),
    path('configuration/whatsapp-template-readonly/<str:template_pk>/', whatsappviews.WhatsappTemplatesReadOnlyView.as_view(), name='whatsapp-template-readonly'),
    path('configuration/whatsapp-template-import/<str:template_pk>/', whatsappviews.WhatsappTemplatesImportView.as_view(), name='whatsapp-template-import'),


    path('configuration/whatsapp-template-create/<str:whatsapp_business_account_pk>/', whatsappviews.WhatsappTemplatesCreateView.as_view(), name='whatsapp-template-create'),
    # path('configuration/whatsapp-template/', whatsappviews.WhatsappTemplatesCreateView.as_view(), name='whatsapp-template'),
    path('configuration/whatsapp-template-delete/', whatsappviews.delete_whatsapp_template_htmx, name='whatsapp-template-delete'),
    path('configuration/whatsapp-templates-save/', whatsappviews.save_whatsapp_template_ajax, name='whatsapp-template-save'),
    path('configuration/whatsapp-templates-approval/', whatsappviews.whatsapp_approval_htmx, name='whatsapp-approval'),   
    path('configuration/whatsapp-templates/clear-changes/', whatsappviews.whatsapp_clear_changes_htmx, name='whatsapp-clear-changes'),    
    path('configuration/whatsapp-change-number-alias/', whatsappviews.whatsapp_number_change_alias, name='whatsapp-change-number-alias'),
    
    # path('configuration/whatsapp-number-make-default  /', whatsappviews.whatsapp_number_make_default, name='whatsapp-number-make-default'),
      
    # path('configuration/whatsapp-change-template-site/', whatsappviews.whatsapp_template_change_site, name='whatsapp-change-template-site'),    
    # path('configuration/whatsapp-change-number-site/', whatsappviews.whatsapp_number_change_site, name='whatsapp-change-number-site'),      
    path('configuration/add-phone-number/', whatsappviews.add_phone_number, name='add-phone-number'),      
    path('configuration/add-whatsapp-business-account/', whatsappviews.add_whatsapp_business_account, name='add-whatsapp-business-account'),    

    path('whatsapp-get-modal-content/', whatsapphtmx.get_modal_content, name='whatsapp-get-modal-content' ),
    path('whatsapp-get-modal-content/<str:param1>/', whatsapphtmx.get_modal_content, name='whatsapp-get-modal-content' ),
    path('whatsapp-get-modal-content/<str:param1>/<str:param2>/', whatsapphtmx.get_modal_content, name='whatsapp-get-modal-content' ),

    path('send-new-template-message/', whatsappviews.send_new_template_message, name='send-new-template-message' ),

    path('set-whatsapp-company-config/', whatsappviews.set_whatsapp_company_config, name='set-whatsapp-company-config'),
    
]    