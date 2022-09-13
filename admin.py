from django.contrib import admin, auth
from core.models import Technology, TechnologyType, Language, ProjectImage, Project
from import_export.admin import ImportExportModelAdmin
    
class ProjectAdmin(ImportExportModelAdmin):
    search_fields = ['pk', 'name', 'role', 'teamsize', 'start', 'end', 'shorthtmldescription']
    list_display = ['pk', 'name', 'role', 'teamsize', 'start', 'end', 'shorthtmldescription']
admin.site.register(Project, ProjectAdmin)

class TechnologyAdmin(ImportExportModelAdmin):
    search_fields = ['pk', 'name', 'type']
    list_display = ['pk', 'name']
admin.site.register(Technology, TechnologyAdmin)

class TechnologyTypeAdmin(ImportExportModelAdmin):
    search_fields = ['pk', 'name']
    list_display = ['pk', 'name']
admin.site.register(TechnologyType, TechnologyTypeAdmin)

class LanguageAdmin(ImportExportModelAdmin):
    search_fields = ['pk', 'name']
    list_display = ['pk', 'name']
admin.site.register(Language, LanguageAdmin)

class ProjectImageAdmin(ImportExportModelAdmin):
    search_fields = ['pk', 'image', 'htmldescription', 'priority']
    list_display = ['pk', 'image', 'htmldescription', 'priority']
admin.site.register(ProjectImage, ProjectImageAdmin)

from django.apps import apps
models = apps.get_models()

for model in models:
    try:
        admin.site.register(model) #Register all models that aren't already registered
    except:
        pass #If the model is already registed, don't bother