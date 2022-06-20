from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group


from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import ADUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = ADUser
    list_display = ('email', 'is_superuser', 'always_notify', 'is_faculty',)
    list_filter= ('email', 'is_superuser', 'always_notify', 'is_faculty',)
    fieldsets = (
        (None, {'fields': ('email', 'date_joined', 'is_active')}),
        ('Permissions', {'fields': ('is_superuser', 'always_notify', 'is_faculty')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'date_joined', 'is_active')}),
        ('Permissions', {'fields': ('is_superuser', 'always_notify', 'is_faculty')}),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.unregister(ADUser)
admin.site.register(ADUser, CustomUserAdmin)
admin.site.unregister(Group)
