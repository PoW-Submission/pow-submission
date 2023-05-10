from django.contrib import admin
from django.apps import apps
from django.db import models
from django.forms import SelectMultiple


appModels = apps.get_models()

class CustomModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'25'})},
    }

class CustomOfferingAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ManyToManyField: {'widget': SelectMultiple(attrs={'size':'25'})},
    }
    list_display = ('__str__', 'term')

for model in appModels:
    try:
        if 'offering' == model._meta.model.__name__.lower():
            admin.site.register(model, CustomOfferingAdmin)
        else:
            admin.site.register(model, CustomModelAdmin)
    except admin.sites.AlreadyRegistered:
        pass
