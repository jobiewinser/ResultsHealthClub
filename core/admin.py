from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.apps import apps

from core.models import *
models = apps.get_models()

class SiteAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'created']
    search_fields = ['pk', 'name', 'created']
admin.site.register(Site, SiteAdmin)
class AttachedErrorAdmin(admin.ModelAdmin):
    readonly_fields = ('created',) 
    list_display = ['pk', 'created', 'attached_field']
    search_fields = ['pk', 'created', 'attached_field']
admin.site.register(AttachedError, AttachedErrorAdmin)
class ErrorModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created',) 
    list_display = ['pk', 'created']
    search_fields = ['pk', 'created']
admin.site.register(ErrorModel, ErrorModelAdmin)

for model in models:
    try:
        admin.site.register(model) #Register all models that aren't already registered
    except:
        pass #If the model is already registed, don't bother


