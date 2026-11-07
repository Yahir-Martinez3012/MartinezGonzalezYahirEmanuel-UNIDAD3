from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from . import seguridad


@receiver(user_login_failed)
def al_fallar_inicio_de_sesion(sender, credentials, request=None, **kwargs):
    usuario = (credentials or {}).get('username')
    if usuario:
        seguridad.registrar_fallo(usuario, seguridad.ip_cliente(request))


@receiver(user_logged_in)
def al_iniciar_sesion(sender, user, request=None, **kwargs):
    seguridad.limpiar(user.get_username())      # un acceso correcto reinicia el contador
