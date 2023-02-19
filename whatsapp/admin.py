from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.apps import apps

from whatsapp.models import *

class WhatsAppWebhookRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_type',  
        'created',  
        'json_data',   
        ]
    search_fields = ['pk']
admin.site.register(WhatsAppWebhookRequest, WhatsAppWebhookRequestAdmin)

class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 
        'customer_number', 
        'inbound',     
        'datetime',  
        'message',   
        'site',  
        'created',  
        'template',
        'conversationid',  
        'wamid',    
        'raw_webhook',
        ]
    search_fields = ['pk']
admin.site.register(WhatsAppMessage, WhatsAppMessageAdmin)

class WhatsAppMessageStatusAdmin(admin.ModelAdmin):
    list_display = [
        'whatsapp_message',  
        'datetime', 
        'status',     
        'created',  
        'raw_webhook',   
    ]
    search_fields = ['pk']
admin.site.register(WhatsAppMessageStatus, WhatsAppMessageStatusAdmin)

class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'pk', 
        'name',  
        'message_template_id',  
        # 'site_name',  
        'category', 
        'language',     
        'created',  
        # 'send_order',  
        'edited',   
        'edited_by',   
    ]
    search_fields = ['pk']
admin.site.register(WhatsappTemplate, WhatsAppTemplateAdmin)