from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django.apps import apps
models = apps.get_models()

for model in models:
    try:
        admin.site.register(model) #Register all models that aren't already registered
    except:
        pass #If the model is already registed, don't bother