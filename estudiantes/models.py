import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone

from catalogo.models import Carrera, Habilidad


def ruta_cv(instance, filename):
    """Obsoleta: se conserva solo porque la migración 0001 la referencia (el CV ahora vive en ArchivoCV)."""
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
    cv_nombre = models.CharField(max_length=150, blank=True)      # indicador barato de que existe un CV
    cv_subido = models.DateTimeField(null=True, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    @classmethod
    def para(cls, usuario):
        perfil, _ = cls.objects.get_or_create(usuario=usuario)
        return perfil

    @property
    def tiene_cv(self):
        return bool(self.cv_nombre)

    @transaction.atomic
    def guardar_cv(self, nombre, contenido):
        """Guarda (o reemplaza) el CV en la base de datos para que sobreviva a los reinicios del servidor."""
        ArchivoCV.objects.update_or_create(perfil=self, defaults={'contenido': contenido, 'nombre': nombre[:150]})
        self.cv_nombre = nombre[:150]
        self.cv_subido = timezone.now()
        self.save(update_fields=['cv_nombre', 'cv_subido'])

    @property
    def nombre_visible(self):
        return self.nombre_completo or self.usuario.get_username()

    @property
    def esta_completo(self):
        return bool(self.nombre_completo and self.carrera)

    def __str__(self):
        return self.nombre_visible


class ArchivoCV(models.Model):
    """Contenido del CV en PDF. Va en un modelo aparte para no cargar archivos pesados en cada consulta del perfil."""
    perfil = models.OneToOneField(PerfilEstudiante, on_delete=models.CASCADE, related_name='archivo_cv')
    contenido = models.BinaryField()
    nombre = models.CharField(max_length=150)
    subido = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'archivo de CV'
        verbose_name_plural = 'archivos de CV'

    def __str__(self):
        return f'CV de {self.perfil}'
