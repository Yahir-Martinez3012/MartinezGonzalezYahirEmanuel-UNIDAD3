from django.contrib import admin

from .models import PerfilEstudiante


@admin.register(PerfilEstudiante)
class PerfilEstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre_visible', 'usuario', 'carrera', 'cuatrimestre', 'es_egresado')
    list_filter = ('carrera', 'es_egresado', 'cuatrimestre')
    search_fields = ('nombre_completo', 'usuario__username', 'usuario__email')
    filter_horizontal = ('habilidades',)
