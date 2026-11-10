"""Resend: envío de correos mediante su API REST (HTTPS).

Se usa una API web y no SMTP porque los servicios gratuitos de algunos hosting (como Render) bloquean
los puertos SMTP. Documentación: https://resend.com/docs/api-reference/emails/send-email
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
URL_ENVIO = 'https://api.resend.com/emails'


def habilitado():
    return bool(settings.RESEND_API_KEY)


def enviar(destinatario, asunto, html):
    """Envía un correo. Devuelve True si Resend lo aceptó; nunca lanza excepciones de red."""
    if not habilitado():
        logger.info('Correo omitido (RESEND_API_KEY no configurada): %s → %s', asunto, destinatario)
        return False
    try:
        respuesta = requests.post(
            URL_ENVIO,
            json={'from': settings.CORREO_REMITENTE, 'to': [destinatario], 'subject': asunto, 'html': html},
            headers={'Authorization': f'Bearer {settings.RESEND_API_KEY}'},
            timeout=5,
        )
        respuesta.raise_for_status()
        return True
    except requests.RequestException:
        logger.warning('No se pudo enviar el correo «%s» a %s', asunto, destinatario)
        return False
