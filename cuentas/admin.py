from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Rol en Conecta UTC', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Rol en Conecta UTC', {'fields': ('rol',)}),)
    list_display = ('username', 'email', 'rol', 'is_staff')
    list_filter = UserAdmin.list_filter + ('rol',)
