from django.contrib import admin
from django.apps import apps
from django.db import models
from django.forms import SelectMultiple


appModels = apps.get_models()

class CustomModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'25'})},
    }

for model in appModels:
    try:
        admin.site.register(model, CustomModelAdmin)
    except admin.sites.AlreadyRegistered:
        pass
