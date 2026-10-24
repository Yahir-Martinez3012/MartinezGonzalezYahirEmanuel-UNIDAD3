from django.conf import settings
from django.db import models


class Empresa(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de revisión'
        APROBADA = 'aprobada', 'Aprobada'
        RECHAZADA = 'rechazada', 'Rechazada'

    CLASES_ESTADO = {'pendiente': 'warning', 'aprobada': 'success', 'rechazada': 'danger'}

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='empresa')
    nombre = models.CharField(max_length=150)
    sector = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField(blank=True)
    sitio_web = models.URLField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    @classmethod
    def para(cls, usuario):
        empresa, _ = cls.objects.get_or_create(usuario=usuario, defaults={'nombre': usuario.get_username()})
        return empresa

    @property
    def esta_aprobada(self):
        return self.estado == self.Estado.APROBADA

    @property
    def clase_estado(self):
        return self.CLASES_ESTADO[self.estado]

    def __str__(self):
        return self.nombre
