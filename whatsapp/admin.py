from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.apps import apps

from whatsapp.models import *

class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'wamid',    
        'raw_webhook',
        'inbound',  
        'conversationid',     
        'datetime',  
        'message',  
        'system_user_number',  
        'customer_number',  
        'communication',   
        'communication',  
        'created',  
        'template'
        ]
    search_fields = ['pk']
admin.site.register(WhatsAppMessage, WhatsAppMessageAdmin)