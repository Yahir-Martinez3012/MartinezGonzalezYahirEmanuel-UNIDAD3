from rest_framework.permissions import BasePermission

from cuentas.models import Usuario


class EsEstudiante(BasePermission):
    message = 'Esta operación es solo para cuentas de estudiante.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.rol_efectivo == Usuario.Rol.ESTUDIANTE)


class EsAdminUTC(BasePermission):
    message = 'Esta operación es solo para administradores de la UTC.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.es_admin_utc)
