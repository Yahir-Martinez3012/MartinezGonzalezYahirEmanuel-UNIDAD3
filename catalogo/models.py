from django.db import models


class Carrera(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Habilidad(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'habilidades'

    def __str__(self):
        return self.nombre
