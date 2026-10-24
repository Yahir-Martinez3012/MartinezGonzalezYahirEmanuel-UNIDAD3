from django.contrib import admin

from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'sector', 'ciudad', 'estado', 'creada')
    list_filter = ('estado', 'ciudad')
    search_fields = ('nombre', 'usuario__username', 'usuario__email')
    actions = ['aprobar', 'rechazar']

    @admin.action(description='Aprobar empresas seleccionadas')
    def aprobar(self, request, queryset):
        n = queryset.update(estado=Empresa.Estado.APROBADA)
        self.message_user(request, f'{n} empresa(s) aprobada(s).')

    @admin.action(description='Rechazar empresas seleccionadas')
    def rechazar(self, request, queryset):
        n = queryset.update(estado=Empresa.Estado.RECHAZADA)
        self.message_user(request, f'{n} empresa(s) rechazada(s).')
