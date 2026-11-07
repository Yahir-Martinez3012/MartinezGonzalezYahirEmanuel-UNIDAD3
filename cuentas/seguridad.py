"""Protección contra fuerza bruta: bloquea un usuario tras varios inicios de sesión fallidos.

Se bloquea por nombre de usuario (no por IP) para frenar también ataques distribuidos. La contrapartida,
documentada, es que alguien podría bloquear a propósito una cuenta ajena durante unos minutos.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import IntentoLogin

logger = logging.getLogger('seguridad')


def _ventana():
    return timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS)


def _recientes(usuario):
    return IntentoLogin.objects.filter(usuario__iexact=usuario, creado__gte=timezone.now() - _ventana())


def ip_cliente(request):
    if request is None:
        return None
    reenviada = request.META.get('HTTP_X_FORWARDED_FOR')       # detrás del proxy de Render
    ip = reenviada.split(',')[0].strip() if reenviada else request.META.get('REMOTE_ADDR')
    return ip or None


def esta_bloqueado(usuario):
    return _recientes(usuario).count() >= settings.LOGIN_MAX_INTENTOS


def minutos_restantes(usuario):
    """Minutos que faltan para que el intento fallido más antiguo de la ventana deje de contar."""
    antiguo = _recientes(usuario).order_by('creado').first()
    if not antiguo:
        return 0
    falta = antiguo.creado + _ventana() - timezone.now()
    return max(1, int(falta.total_seconds() // 60) + 1)


def registrar_fallo(usuario, ip):
    IntentoLogin.objects.create(usuario=usuario[:150], ip=ip)
    restantes = settings.LOGIN_MAX_INTENTOS - _recientes(usuario).count()
    logger.warning('Inicio de sesión fallido: usuario=%s ip=%s (intentos restantes: %s)', usuario, ip, max(restantes, 0))
    if restantes == 0:
        logger.error('Cuenta bloqueada temporalmente por intentos fallidos: usuario=%s', usuario)


def limpiar(usuario):
    IntentoLogin.objects.filter(usuario__iexact=usuario).delete()
