"""Capa de servicios: reglas de negocio de las postulaciones.

La vista web y la API REST llaman a esta función, así las reglas viven en un solo lugar (principio DRY).
"""
from .models import Postulacion


class PostulacionNoPermitida(Exception):
    """El estudiante no cumple los requisitos para postularse."""


def postular(perfil, vacante):
    """Registra la postulación. Devuelve (postulacion, creada). Lanza PostulacionNoPermitida si no procede."""
    if not vacante.esta_abierta:
        raise PostulacionNoPermitida('Esta vacante ya no recibe postulaciones.')
    if not perfil.esta_completo or not perfil.tiene_cv:
        raise PostulacionNoPermitida('Completa tu perfil (nombre y carrera) y sube tu CV en PDF para postularte.')
    return Postulacion.objects.get_or_create(estudiante=perfil, vacante=vacante)
