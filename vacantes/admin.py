from django.contrib import admin

from .models import Favorito, Vacante


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'tipo', 'modalidad', 'estado', 'destacada', 'fecha_publicacion')
    list_filter = ('estado', 'tipo', 'modalidad', 'destacada', 'empresa')
    list_editable = ('destacada',)
    search_fields = ('titulo', 'empresa__nombre', 'ubicacion')
    filter_horizontal = ('habilidades', 'carreras')
    date_hierarchy = 'fecha_publicacion'
    actions = ['aprobar', 'rechazar']

    @admin.action(description='Aprobar (publicar) vacantes seleccionadas')
    def aprobar(self, request, queryset):
        n = queryset.update(estado=Vacante.Estado.APROBADA)
        self.message_user(request, f'{n} vacante(s) publicada(s).')

    @admin.action(description='Rechazar vacantes seleccionadas')
    def rechazar(self, request, queryset):
        n = queryset.update(estado=Vacante.Estado.RECHAZADA)
        self.message_user(request, f'{n} vacante(s) rechazada(s).')


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'vacante', 'creado')
