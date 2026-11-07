from servicios import recaptcha


def recaptcha_config(request):
    """Expone la clave pública de reCAPTCHA a las plantillas (vacía si el servicio no está configurado)."""
    from django.conf import settings
    return {'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY if recaptcha.habilitado() else ''}
