from django.contrib import admin

from .models import Carrera, Habilidad


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Habilidad)
class HabilidadAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)
