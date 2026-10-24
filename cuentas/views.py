from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante

from .forms import RegistroForm
from .models import Usuario


def registro(request):
    """Registro público de estudiantes y empresas."""
    if request.user.is_authenticated:
        return redirect('inicio')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()      # Django guarda la contraseña cifrada (hash), nunca en texto plano
        login(request, usuario)
        if usuario.rol == Usuario.Rol.EMPRESA:
            Empresa.para(usuario)
            messages.success(request, '¡Cuenta creada! Completa el perfil de tu empresa; un administrador de la UTC lo revisará.')
            return redirect('empresas:editar_perfil')
        PerfilEstudiante.para(usuario)
        messages.success(request, '¡Cuenta creada! Completa tu perfil y sube tu CV para postularte.')
        return redirect('estudiantes:editar_perfil')
    return render(request, 'cuentas/registro.html', {'form': form})
