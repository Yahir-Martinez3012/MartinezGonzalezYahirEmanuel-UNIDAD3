"""Google reCAPTCHA v2: confirma que quien envía un formulario es una persona.

Documentación: https://developers.google.com/recaptcha/docs/verify
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger('seguridad')
URL_VERIFICACION = 'https://www.google.com/recaptcha/api/siteverify'


def habilitado():
    """Solo se exige cuando hay claves configuradas (así el desarrollo local no depende de Google)."""
    return bool(settings.RECAPTCHA_SITE_KEY and settings.RECAPTCHA_SECRET_KEY)


def verificar(token, ip=None):
    """Devuelve True si Google confirma el token. Falla de forma segura: si Google no responde, devuelve False."""
    if not habilitado():
        return True
    if not token:
        return False
    try:
        respuesta = requests.post(
            URL_VERIFICACION,
            data={'secret': settings.RECAPTCHA_SECRET_KEY, 'response': token, 'remoteip': ip},
            timeout=5,
        )
        respuesta.raise_for_status()
        return bool(respuesta.json().get('success'))
    except (requests.RequestException, ValueError):
        logger.error('No se pudo verificar reCAPTCHA con Google; se rechaza la solicitud.')
        return False
