"""Nominatim (OpenStreetMap): convierte una dirección en coordenadas.

Política de uso: https://operations.osmfoundation.org/policies/nominatim/
Exige identificar la aplicación con un User-Agent, no pasar de 1 petición por segundo y guardar los
resultados en lugar de repetir consultas; por eso las coordenadas se almacenan en la vacante.
"""
import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
URL_BUSQUEDA = 'https://nominatim.openstreetmap.org/search'
SEIS_DECIMALES = Decimal('0.000001')


def geocodificar(direccion):
    """Devuelve (latitud, longitud) como Decimal, o None si no se encontró o el servicio falló."""
    if not settings.GEOCODIFICACION_HABILITADA or not direccion or not direccion.strip():
        return None
    try:
        respuesta = requests.get(
            URL_BUSQUEDA,
            params={'q': direccion.strip(), 'format': 'jsonv2', 'limit': 1, 'countrycodes': 'mx'},
            headers={'User-Agent': settings.NOMINATIM_USER_AGENT},
            timeout=5,
        )
        respuesta.raise_for_status()
        resultados = respuesta.json()
        if not resultados:
            return None
        return (Decimal(resultados[0]['lat']).quantize(SEIS_DECIMALES),
                Decimal(resultados[0]['lon']).quantize(SEIS_DECIMALES))
    except (requests.RequestException, ValueError, KeyError, ArithmeticError):
        logger.warning('No se pudo geocodificar «%s»', direccion)
        return None
