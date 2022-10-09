from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.apps import apps

from core.models import Site
models = apps.get_models()

class SiteAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', 'created']
    search_fields = ['pk', 'name', 'created']
admin.site.register(Site, SiteAdmin)
for model in models:
    try:
        admin.site.register(model) #Register all models that aren't already registered
    except:
        pass #If the model is already registed, don't bother


