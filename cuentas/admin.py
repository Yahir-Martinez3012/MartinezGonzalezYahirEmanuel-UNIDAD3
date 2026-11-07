from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import IntentoLogin, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Rol en Conecta UTC', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Rol en Conecta UTC', {'fields': ('rol',)}),)
    list_display = ('username', 'email', 'rol', 'is_staff')
    list_filter = UserAdmin.list_filter + ('rol',)


@admin.register(IntentoLogin)
class IntentoLoginAdmin(admin.ModelAdmin):
    """Bitácora de solo lectura: sirve para auditar posibles ataques de fuerza bruta."""
    list_display = ('usuario', 'ip', 'creado')
    list_filter = ('creado',)
    search_fields = ('usuario', 'ip')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
