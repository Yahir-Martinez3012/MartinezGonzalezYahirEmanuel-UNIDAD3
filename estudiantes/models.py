import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from catalogo.models import Carrera, Habilidad


def ruta_cv(instance, filename):
    """Nombre aleatorio: el archivo no se puede adivinar y solo se descarga mediante una vista con permisos."""
    return f'cvs/{uuid.uuid4().hex}.pdf'


class PerfilEstudiante(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_estudiante')
    nombre_completo = models.CharField(max_length=120, blank=True)
    carrera = models.ForeignKey(Carrera, on_delete=models.SET_NULL, null=True, blank=True, related_name='estudiantes')
    cuatrimestre = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=[(i, f'{i}.º cuatrimestre') for i in range(1, 12)])
    es_egresado = models.BooleanField('Soy egresado', default=False)
    habilidades = models.ManyToManyField(Habilidad, blank=True, related_name='estudiantes')
    telefono = models.CharField(
        max_length=20, blank=True,
        validators=[RegexValidator(r'^[0-9+\-\s()]{7,20}$', 'Escribe un teléfono válido.')])
    experiencia = models.TextField(blank=True)
    cv = models.FileField(upload_to=ruta_cv, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    @classmethod
    def para(cls, usuario):
        perfil, _ = cls.objects.get_or_create(usuario=usuario)
        return perfil

    @property
    def nombre_visible(self):
        return self.nombre_completo or self.usuario.get_username()

    @property
    def esta_completo(self):
        return bool(self.nombre_completo and self.carrera)

    def __str__(self):
        return self.nombre_visible
