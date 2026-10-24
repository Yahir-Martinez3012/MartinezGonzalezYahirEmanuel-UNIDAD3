from django.db import models
from django.utils import timezone

from estudiantes.models import PerfilEstudiante
from vacantes.models import Vacante


class Postulacion(models.Model):
    class Estado(models.TextChoices):
        ENVIADA = 'enviada', 'Enviada'
        EN_REVISION = 'en_revision', 'En revisión'
        ENTREVISTA = 'entrevista', 'Entrevista'
        ACEPTADA = 'aceptada', 'Aceptada'
        RECHAZADA = 'rechazada', 'Rechazada'

    CLASES_ESTADO = {'enviada': 'secondary', 'en_revision': 'info', 'entrevista': 'primary',
                     'aceptada': 'success', 'rechazada': 'danger'}

    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name='postulaciones')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='postulaciones')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ENVIADA)
    fecha = models.DateTimeField(default=timezone.now)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'postulaciones'
        constraints = [models.UniqueConstraint(fields=['estudiante', 'vacante'], name='postulacion_unica')]

    @property
    def clase_estado(self):
        return self.CLASES_ESTADO[self.estado]

    def __str__(self):
        return f'{self.estudiante} → {self.vacante} ({self.get_estado_display()})'
