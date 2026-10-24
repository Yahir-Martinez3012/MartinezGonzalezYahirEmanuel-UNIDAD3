from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import render

from cuentas.models import Usuario
from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion
from vacantes.models import Favorito, Vacante


def inicio(request):
    abiertas = Vacante.objects.abiertas().select_related('empresa').prefetch_related('habilidades')
    conteo_tipos = dict(abiertas.values_list('tipo').annotate(n=Count('id')))
    categorias = [(valor, etiqueta, conteo_tipos.get(valor, 0)) for valor, etiqueta in Vacante.Tipo.choices]
    destacadas = list(abiertas.filter(destacada=True).order_by('-fecha_publicacion')[:3])
    return render(request, 'core/inicio.html', {
        'recientes': abiertas.exclude(pk__in=[v.pk for v in destacadas]).order_by('-fecha_publicacion')[:6],
        'destacadas': destacadas,
        'categorias': categorias,
        'total_vacantes': abiertas.count(),
        'total_empresas': Empresa.objects.filter(estado=Empresa.Estado.APROBADA).count(),
    })


def _conteo(queryset, campo, opciones):
    """Devuelve [(etiqueta, cantidad, porcentaje)] para una tabla de estadísticas."""
    datos = dict(queryset.values_list(campo).annotate(n=Count('id')))
    total = sum(datos.values()) or 1
    return [(etiqueta, datos.get(valor, 0), round(datos.get(valor, 0) * 100 / total)) for valor, etiqueta in opciones]


@login_required
def estadisticas(request):
    if not request.user.es_admin_utc:
        raise PermissionDenied
    return render(request, 'core/estadisticas.html', {
        'totales': [
            ('Estudiantes', PerfilEstudiante.objects.count()),
            ('Empresas', Empresa.objects.count()),
            ('Vacantes', Vacante.objects.count()),
            ('Postulaciones', Postulacion.objects.count()),
            ('Favoritos', Favorito.objects.count()),
            ('Usuarios', Usuario.objects.count()),
        ],
        'vacantes_estado': _conteo(Vacante.objects.all(), 'estado', Vacante.Estado.choices),
        'vacantes_tipo': _conteo(Vacante.objects.all(), 'tipo', Vacante.Tipo.choices),
        'empresas_estado': _conteo(Empresa.objects.all(), 'estado', Empresa.Estado.choices),
        'postulaciones_estado': _conteo(Postulacion.objects.all(), 'estado', Postulacion.Estado.choices),
        'top_vacantes': Vacante.objects.annotate(n=Count('postulaciones')).filter(n__gt=0).order_by('-n')[:5],
        'pendientes_vacantes': Vacante.objects.filter(estado=Vacante.Estado.PENDIENTE).count(),
        'pendientes_empresas': Empresa.objects.filter(estado=Empresa.Estado.PENDIENTE).count(),
    })
