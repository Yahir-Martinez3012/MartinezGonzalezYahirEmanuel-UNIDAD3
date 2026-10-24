from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cuentas.decorators import rol_requerido
from cuentas.models import Usuario
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion

from .forms import VacanteFiltroForm
from .models import Favorito, Vacante

ESTUDIANTE = Usuario.Rol.ESTUDIANTE


def lista(request):
    vacantes = Vacante.objects.abiertas().select_related('empresa').prefetch_related('habilidades')
    form = VacanteFiltroForm(request.GET or None)
    if form.is_valid():
        vacantes = form.filtrar(vacantes)
    paginador = Paginator(vacantes.order_by('-destacada', '-fecha_publicacion', '-pk'), 9)
    pagina = paginador.get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    favoritos_ids = set()
    if request.user.is_authenticated and request.user.rol == ESTUDIANTE:
        favoritos_ids = set(Favorito.objects.filter(estudiante__usuario=request.user)
                            .values_list('vacante_id', flat=True))
    return render(request, 'vacantes/lista.html', {
        'form': form, 'page_obj': pagina, 'total': paginador.count,
        'querystring': params.urlencode(), 'favoritos_ids': favoritos_ids,
    })


def detalle(request, pk):
    vacante = get_object_or_404(
        Vacante.objects.select_related('empresa').prefetch_related('habilidades', 'carreras'), pk=pk)
    u = request.user
    es_dueno = u.is_authenticated and vacante.empresa.usuario_id == u.pk
    es_admin = u.is_authenticated and u.es_admin_utc
    # Las vacantes pendientes o rechazadas solo las ven su empresa y el administrador.
    publica = vacante.estado in (Vacante.Estado.APROBADA, Vacante.Estado.CERRADA) and vacante.empresa.esta_aprobada
    if not (publica or es_dueno or es_admin):
        raise Http404

    es_estudiante = u.is_authenticated and u.rol_efectivo == ESTUDIANTE
    ya_postulado = es_favorito = False
    if es_estudiante:
        perfil = PerfilEstudiante.para(u)
        ya_postulado = Postulacion.objects.filter(estudiante=perfil, vacante=vacante).exists()
        es_favorito = Favorito.objects.filter(estudiante=perfil, vacante=vacante).exists()
    return render(request, 'vacantes/detalle.html', {
        'vacante': vacante, 'es_estudiante': es_estudiante, 'ya_postulado': ya_postulado,
        'es_favorito': es_favorito, 'vista_previa': not publica,
    })


@require_POST
@rol_requerido(ESTUDIANTE)
def postular(request, pk):
    vacante = get_object_or_404(Vacante.objects.abiertas(), pk=pk)
    perfil = PerfilEstudiante.para(request.user)
    if not perfil.esta_completo or not perfil.cv:
        messages.warning(request, 'Completa tu perfil (nombre y carrera) y sube tu CV en PDF para postularte.')
        return redirect('estudiantes:editar_perfil')
    _, creada = Postulacion.objects.get_or_create(estudiante=perfil, vacante=vacante)
    if creada:
        messages.success(request, f'¡Te postulaste a «{vacante.titulo}»! Puedes seguir el estado en tu perfil.')
    else:
        messages.info(request, 'Ya te habías postulado a esta vacante.')
    return redirect(vacante)


@require_POST
@rol_requerido(ESTUDIANTE)
def favorito(request, pk):
    vacante = get_object_or_404(Vacante.objects.abiertas(), pk=pk)
    perfil = PerfilEstudiante.para(request.user)
    obj, creado = Favorito.objects.get_or_create(estudiante=perfil, vacante=vacante)
    if creado:
        messages.success(request, 'Vacante guardada en tus favoritas.')
    else:
        obj.delete()
        messages.info(request, 'Vacante quitada de tus favoritas.')
    destino = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        return redirect(destino)
    return redirect(vacante)
