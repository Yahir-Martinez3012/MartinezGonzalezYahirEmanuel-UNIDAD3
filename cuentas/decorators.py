from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    """Exige sesión iniciada y que el rol del usuario esté entre los permitidos (403 en caso contrario)."""
    def decorador(vista):
        @login_required
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if request.user.rol_efectivo not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
