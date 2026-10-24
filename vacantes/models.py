from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Carrera, Habilidad
from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante


class VacanteQuerySet(models.QuerySet):
    def abiertas(self):
        """Vacantes visibles al público: aprobadas, de empresa aprobada y con plazo vigente."""
        hoy = timezone.localdate()
        return self.filter(
            estado=Vacante.Estado.APROBADA,
            empresa__estado=Empresa.Estado.APROBADA,
        ).filter(Q(fecha_limite__isnull=True) | Q(fecha_limite__gte=hoy))


class Vacante(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente de aprobación'
        APROBADA = 'aprobada', 'Publicada'
        RECHAZADA = 'rechazada', 'Rechazada'
        CERRADA = 'cerrada', 'Cerrada'

    class Modalidad(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        HIBRIDA = 'hibrida', 'Híbrida'
        REMOTA = 'remota', 'Remota'

    class Tipo(models.TextChoices):
        PRACTICAS = 'practicas', 'Prácticas'
        ESTADIA = 'estadia', 'Estadía profesional'
        MEDIO_TIEMPO = 'medio_tiempo', 'Medio tiempo'
        TIEMPO_COMPLETO = 'tiempo_completo', 'Tiempo completo'
        EGRESADOS = 'egresados', 'Vacante para egresados'

    class Experiencia(models.TextChoices):
        NINGUNA = 'ninguna', 'Sin experiencia'
        MENOS_1 = 'menos_1', 'Menos de 1 año'
        UNO_DOS = 'uno_dos', '1 a 2 años'
        MAS_2 = 'mas_2', 'Más de 2 años'

    CLASES_ESTADO = {'pendiente': 'warning', 'aprobada': 'success', 'rechazada': 'danger', 'cerrada': 'secondary'}

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='vacantes')
    titulo = models.CharField('Nombre del puesto', max_length=150)
    descripcion = models.TextField('Descripción')
    requisitos = models.TextField()
    habilidades = models.ManyToManyField(Habilidad, blank=True, related_name='vacantes')
    carreras = models.ManyToManyField(Carrera, blank=True, related_name='vacantes',
                                      help_text='Déjalo vacío si la vacante es para cualquier carrera.')
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices)
    tipo = models.CharField('Tipo de oportunidad', max_length=20, choices=Tipo.choices)
    experiencia = models.CharField('Experiencia requerida', max_length=20, choices=Experiencia.choices,
                                   default=Experiencia.NINGUNA)
    ubicacion = models.CharField('Ubicación', max_length=120)
    horario = models.CharField(max_length=100, blank=True)
    salario = models.CharField(max_length=100, blank=True, help_text='Opcional. Ej.: $9,000 mensuales')
    fecha_publicacion = models.DateTimeField(default=timezone.now, editable=False)
    fecha_limite = models.DateField('Fecha límite', null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    destacada = models.BooleanField(default=False)

    objects = VacanteQuerySet.as_manager()

    class Meta:
        ordering = ['-fecha_publicacion']

    @property
    def esta_abierta(self):
        if self.estado != self.Estado.APROBADA or not self.empresa.esta_aprobada:
            return False
        return self.fecha_limite is None or self.fecha_limite >= timezone.localdate()

    @property
    def clase_estado(self):
        return self.CLASES_ESTADO[self.estado]

    def get_absolute_url(self):
        return reverse('vacantes:detalle', args=[self.pk])

    def __str__(self):
        return f'{self.titulo} · {self.empresa.nombre}'


class Favorito(models.Model):
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name='favoritos')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='favoritos')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']
        constraints = [models.UniqueConstraint(fields=['estudiante', 'vacante'], name='favorito_unico')]

    def __str__(self):
        return f'{self.estudiante} ♥ {self.vacante}'
