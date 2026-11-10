from django.conf import settings
from django.urls import path
from django.utils.csp import CSP
from django.views.decorators.csp import csp_override
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerSplitView

from . import views

app_name = 'api'

# La página de Swagger trae un bloque <style> en línea: solo para ella se permite 'unsafe-inline' en estilos
# (los scripts siguen estrictos). El resto del sitio conserva la política completa.
CSP_DOCUMENTACION = {**settings.SECURE_CSP, 'style-src': [CSP.SELF, CSP.UNSAFE_INLINE]}

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', csp_override(CSP_DOCUMENTACION)(SpectacularSwaggerSplitView.as_view(url_name='api:schema')), name='docs'),
    path('vacantes/', views.ListaVacantes.as_view(), name='vacantes'),
    path('vacantes/<int:pk>/', views.DetalleVacante.as_view(), name='vacante'),
    path('token/', views.ObtenerToken.as_view(), name='token'),
    path('vacantes/<int:pk>/postular/', views.PostularAVacante.as_view(), name='postular'),
    path('mis-postulaciones/', views.MisPostulaciones.as_view(), name='mis_postulaciones'),
    path('estadisticas/', views.Estadisticas.as_view(), name='estadisticas'),
    path('carreras/', views.ListaCarreras.as_view(), name='carreras'),
    path('habilidades/', views.ListaHabilidades.as_view(), name='habilidades'),
]
