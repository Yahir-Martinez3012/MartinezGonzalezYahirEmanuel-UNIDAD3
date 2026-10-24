from django.contrib import admin

from .models import Postulacion


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'vacante', 'estado', 'fecha')
    list_filter = ('estado', 'vacante__empresa')
    search_fields = ('estudiante__nombre_completo', 'estudiante__usuario__username', 'vacante__titulo')
