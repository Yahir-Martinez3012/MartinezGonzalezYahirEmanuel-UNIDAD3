from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from catalogo.models import Carrera, Habilidad
from cuentas import seguridad
from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion
from postulaciones.servicios import PostulacionNoPermitida, postular
from vacantes.forms import VacanteFiltroForm
from vacantes.models import Vacante

from .permissions import EsAdminUTC, EsEstudiante
from .serializers import (CarreraSerializer, HabilidadSerializer, PostulacionSerializer,
                          VacanteDetalleSerializer, VacanteListaSerializer)


def vacantes_publicas():
    return Vacante.objects.abiertas().select_related('empresa').prefetch_related('habilidades', 'carreras')


PARAMETROS_FILTRO = [
    OpenApiParameter('q', str, description='Palabra clave: busca en puesto, descripción, empresa y habilidades.'),
    OpenApiParameter('carrera', int, description='Id de la carrera (ver /carreras/). Incluye vacantes para cualquier carrera.'),
    OpenApiParameter('empresa', int, description='Id de la empresa.'),
    OpenApiParameter('modalidad', str, enum=[c for c, _ in Vacante.Modalidad.choices]),
    OpenApiParameter('ubicacion', str, description='Texto contenido en la ubicación.'),
    OpenApiParameter('tipo', str, enum=[c for c, _ in Vacante.Tipo.choices]),
    OpenApiParameter('experiencia', str, enum=[c for c, _ in Vacante.Experiencia.choices]),
    OpenApiParameter('fecha', str, enum=['hoy', 'semana', 'mes'], description='Publicadas desde hoy, 7 o 30 días.'),
]


@extend_schema(tags=['Vacantes'], parameters=PARAMETROS_FILTRO, summary='Listar vacantes publicadas')
class ListaVacantes(generics.ListAPIView):
    """Vacantes disponibles, con los mismos filtros que la página web."""
    permission_classes = [AllowAny]
    serializer_class = VacanteListaSerializer

    def get_queryset(self):
        filtros = VacanteFiltroForm(self.request.query_params)        # reutiliza el formulario de la web
        if not filtros.is_valid():
            raise ValidationError(filtros.errors.get_json_data())
        return filtros.filtrar(vacantes_publicas()).order_by('-destacada', '-fecha_publicacion', '-pk')


@extend_schema(tags=['Vacantes'], summary='Detalle de una vacante publicada')
class DetalleVacante(generics.RetrieveAPIView):
    """Detalle de una vacante publicada."""
    permission_classes = [AllowAny]
    serializer_class = VacanteDetalleSerializer
    queryset = Vacante.objects.abiertas().select_related('empresa').prefetch_related('habilidades', 'carreras')


@extend_schema(tags=['Catálogos'], summary='Listar carreras')
class ListaCarreras(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CarreraSerializer
    queryset = Carrera.objects.all()
    pagination_class = None


@extend_schema(tags=['Catálogos'], summary='Listar habilidades')
class ListaHabilidades(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = HabilidadSerializer
    queryset = Habilidad.objects.all()
    pagination_class = None


@extend_schema(
    tags=['Autenticación'], summary='Obtener un token de acceso', auth=[],
    responses={200: inline_serializer('Token', {'token': serializers.CharField()}),
               429: inline_serializer('BloqueoPorIntentos', {'detail': serializers.CharField()})})
class ObtenerToken(ObtainAuthToken):
    """Intercambia usuario y contraseña por un token. Comparte con el login web el bloqueo por intentos fallidos."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token'                 # 10 peticiones por minuto

    def post(self, request, *args, **kwargs):
        usuario = str(request.data.get('username', ''))
        if usuario and seguridad.esta_bloqueado(usuario):
            return Response(
                {'detail': f'Demasiados intentos fallidos. Espera {seguridad.minutos_restantes(usuario)} minuto(s).'},
                status=status.HTTP_429_TOO_MANY_REQUESTS)
        respuesta = super().post(request, *args, **kwargs)     # un fallo dispara la señal user_login_failed
        if respuesta.status_code == 200:
            seguridad.limpiar(usuario)
        return respuesta


@extend_schema(tags=['Postulaciones'], summary='Mis postulaciones')
class MisPostulaciones(generics.ListAPIView):
    """Postulaciones del estudiante autenticado."""
    permission_classes = [EsEstudiante]
    serializer_class = PostulacionSerializer

    def get_queryset(self):
        return (Postulacion.objects.filter(estudiante__usuario=self.request.user)
                .select_related('vacante__empresa'))


@extend_schema(
    tags=['Postulaciones'], summary='Postularme a una vacante', request=None,
    responses={201: PostulacionSerializer, 200: PostulacionSerializer,
               400: inline_serializer('PostulacionNoPermitida', {'detail': serializers.CharField()})})
class PostularAVacante(APIView):
    """El estudiante autenticado se postula a una vacante publicada."""
    permission_classes = [EsEstudiante]

    def post(self, request, pk):
        vacante = get_object_or_404(Vacante.objects.abiertas().select_related('empresa'), pk=pk)
        try:
            postulacion, creada = postular(PerfilEstudiante.para(request.user), vacante)
        except PostulacionNoPermitida as error:
            return Response({'detail': str(error)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PostulacionSerializer(postulacion).data,
                        status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK)


@extend_schema(
    tags=['Administración'], summary='Estadísticas generales',
    responses=inline_serializer('Estadisticas', {
        'totales': serializers.DictField(child=serializers.IntegerField()),
        'vacantes_por_estado': serializers.DictField(child=serializers.IntegerField()),
        'empresas_por_estado': serializers.DictField(child=serializers.IntegerField()),
        'postulaciones_por_estado': serializers.DictField(child=serializers.IntegerField())}))
class Estadisticas(APIView):
    """Estadísticas generales del sistema (solo administradores UTC)."""
    permission_classes = [EsAdminUTC]

    @staticmethod
    def _por_estado(modelo):
        return {fila['estado']: fila['n'] for fila in modelo.objects.values('estado').annotate(n=Count('id'))}

    def get(self, request):
        return Response({
            'totales': {
                'estudiantes': PerfilEstudiante.objects.count(),
                'empresas': Empresa.objects.count(),
                'vacantes': Vacante.objects.count(),
                'vacantes_publicadas': Vacante.objects.abiertas().count(),
                'postulaciones': Postulacion.objects.count(),
            },
            'vacantes_por_estado': self._por_estado(Vacante),
            'empresas_por_estado': self._por_estado(Empresa),
            'postulaciones_por_estado': self._por_estado(Postulacion),
        })
