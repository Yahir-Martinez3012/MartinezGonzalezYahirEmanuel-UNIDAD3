from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    """Usuario del sistema. El rol determina qué puede hacer."""

    class Rol(models.TextChoices):
        ESTUDIANTE = 'estudiante', 'Estudiante'
        EMPRESA = 'empresa', 'Empresa'
        ADMIN = 'admin', 'Administrador UTC'

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ESTUDIANTE)

    @property
    def es_admin_utc(self):
        return self.is_superuser or self.rol == self.Rol.ADMIN

    @property
    def rol_efectivo(self):
        return self.Rol.ADMIN if self.es_admin_utc else self.rol

    @property
    def rol_efectivo_display(self):
        return dict(self.Rol.choices)[self.rol_efectivo]

    def save(self, *args, **kwargs):
        if self.is_superuser:          # todo superusuario es administrador UTC
            self.rol = self.Rol.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.get_rol_display()})'


class IntentoLogin(models.Model):
    """Bitácora de inicios de sesión fallidos; se usa para bloquear cuentas atacadas por fuerza bruta."""
    usuario = models.CharField('usuario escrito', max_length=150, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    creado = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'intento de inicio de sesión fallido'
        verbose_name_plural = 'intentos de inicio de sesión fallidos'

    def __str__(self):
        return f'{self.usuario} desde {self.ip or "?"} ({self.creado:%d/%m/%Y %H:%M})'
