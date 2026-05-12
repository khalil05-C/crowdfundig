from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ('email', 'first_name', 'last_name', 'role', 'is_verified')
    list_filter   = ('role', 'is_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering      = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'bio', 'avatar', 'is_verified')
        }),
    )