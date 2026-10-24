from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cuentas.decorators import rol_requerido
from cuentas.models import Usuario
from postulaciones.models import Postulacion
from vacantes.forms import VacanteForm
from vacantes.models import Vacante

from .forms import EmpresaForm
from .models import Empresa

EMPRESA = Usuario.Rol.EMPRESA


@rol_requerido(EMPRESA)
def panel(request):
    empresa = Empresa.para(request.user)
    vacantes = empresa.vacantes.annotate(total_postulados=Count('postulaciones'))
    return render(request, 'empresas/panel.html', {'empresa': empresa, 'vacantes': vacantes})


@rol_requerido(EMPRESA)
def editar_perfil(request):
    empresa = Empresa.para(request.user)
    form = EmpresaForm(request.POST or None, instance=empresa)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'El perfil de la empresa se actualizó.')
        return redirect('empresas:panel')
    return render(request, 'empresas/empresa_form.html', {'form': form})


@rol_requerido(EMPRESA)
def crear_vacante(request):
    empresa = Empresa.para(request.user)
    if not empresa.esta_aprobada:
        messages.warning(request, 'Tu empresa debe ser aprobada por un administrador de la UTC antes de publicar vacantes.')
        return redirect('empresas:panel')
    form = VacanteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vacante = form.save(commit=False)
        vacante.empresa = empresa
        vacante.estado = Vacante.Estado.PENDIENTE      # siempre inicia pendiente: la aprueba la UTC
        vacante.save()
        form.save_m2m()
        messages.success(request, 'Vacante creada. Se publicará cuando un administrador de la UTC la apruebe.')
        return redirect('empresas:panel')
    return render(request, 'empresas/vacante_form.html', {'form': form, 'titulo': 'Nueva vacante'})


@rol_requerido(EMPRESA)
def editar_vacante(request, pk):
    empresa = Empresa.para(request.user)
    vacante = get_object_or_404(Vacante, pk=pk, empresa=empresa)       # solo vacantes propias
    form = VacanteForm(request.POST or None, instance=vacante)
    if request.method == 'POST' and form.is_valid():
        vacante = form.save(commit=False)
        vacante.estado = Vacante.Estado.PENDIENTE      # todo cambio vuelve a revisión
        vacante.save()
        form.save_m2m()
        messages.success(request, 'Vacante actualizada. Volverá a publicarse cuando la UTC la apruebe.')
        return redirect('empresas:panel')
    return render(request, 'empresas/vacante_form.html', {'form': form, 'titulo': 'Editar vacante'})


@require_POST
@rol_requerido(EMPRESA)
def cerrar_vacante(request, pk):
    vacante = get_object_or_404(Vacante, pk=pk, empresa=Empresa.para(request.user))
    vacante.estado = Vacante.Estado.CERRADA
    vacante.save(update_fields=['estado'])
    messages.success(request, f'La vacante «{vacante.titulo}» fue cerrada.')
    return redirect('empresas:panel')


@rol_requerido(EMPRESA)
def candidatos(request, pk):
    vacante = get_object_or_404(Vacante, pk=pk, empresa=Empresa.para(request.user))
    postulaciones = (vacante.postulaciones
                     .select_related('estudiante__usuario', 'estudiante__carrera')
                     .prefetch_related('estudiante__habilidades'))
    return render(request, 'empresas/candidatos.html', {
        'vacante': vacante, 'postulaciones': postulaciones, 'estados': Postulacion.Estado.choices})


@require_POST
@rol_requerido(EMPRESA)
def cambiar_estado(request, pk):
    postulacion = get_object_or_404(Postulacion, pk=pk, vacante__empresa=Empresa.para(request.user))
    estado = request.POST.get('estado')
    if estado in Postulacion.Estado.values:
        postulacion.estado = estado
        postulacion.save(update_fields=['estado', 'actualizada'])
        messages.success(request, f'Estado actualizado a «{postulacion.get_estado_display()}».')
    else:
        messages.error(request, 'Estado no válido.')
    return redirect('empresas:candidatos', pk=postulacion.vacante_id)
