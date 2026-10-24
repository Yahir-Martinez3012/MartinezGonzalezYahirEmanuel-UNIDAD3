from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from cuentas.decorators import rol_requerido
from cuentas.models import Usuario
from postulaciones.models import Postulacion

from .forms import PerfilEstudianteForm
from .models import PerfilEstudiante

ESTUDIANTE = Usuario.Rol.ESTUDIANTE


@rol_requerido(ESTUDIANTE)
def perfil(request):
    perfil = PerfilEstudiante.para(request.user)
    context = {
        'perfil': perfil,
        'favoritos': perfil.favoritos.select_related('vacante__empresa'),
        'postulaciones': perfil.postulaciones.select_related('vacante__empresa'),
    }
    return render(request, 'estudiantes/perfil.html', context)


@rol_requerido(ESTUDIANTE)
def editar_perfil(request):
    perfil = PerfilEstudiante.para(request.user)
    cv_anterior = perfil.cv.name
    form = PerfilEstudianteForm(request.POST or None, request.FILES or None, instance=perfil)
    if request.method == 'POST' and form.is_valid():
        perfil = form.save()
        if cv_anterior and perfil.cv.name != cv_anterior:     # elimina el CV reemplazado
            perfil.cv.storage.delete(cv_anterior)
        messages.success(request, 'Tu perfil se actualizó correctamente.')
        return redirect('estudiantes:perfil')
    return render(request, 'estudiantes/perfil_form.html', {'form': form})


@login_required
def descargar_cv(request, pk):
    """El CV solo lo ve su dueño, el administrador UTC o una empresa a la que el estudiante se postuló."""
    perfil = get_object_or_404(PerfilEstudiante, pk=pk)
    u = request.user
    permitido = (
        u.es_admin_utc
        or perfil.usuario_id == u.pk
        or (u.rol == Usuario.Rol.EMPRESA
            and Postulacion.objects.filter(estudiante=perfil, vacante__empresa__usuario=u).exists())
    )
    if not permitido:
        raise PermissionDenied
    if not perfil.cv:
        raise Http404('Este estudiante no ha subido su CV.')
    try:
        archivo = perfil.cv.open('rb')
    except FileNotFoundError:
        raise Http404('El archivo ya no está disponible.')
    return FileResponse(archivo, content_type='application/pdf', filename=f'CV_{perfil.usuario.username}.pdf')
