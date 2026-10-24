from django.urls import path

from . import views

app_name = 'empresas'

urlpatterns = [
    path('panel/', views.panel, name='panel'),
    path('perfil/', views.editar_perfil, name='editar_perfil'),
    path('vacantes/nueva/', views.crear_vacante, name='crear_vacante'),
    path('vacantes/<int:pk>/editar/', views.editar_vacante, name='editar_vacante'),
    path('vacantes/<int:pk>/cerrar/', views.cerrar_vacante, name='cerrar_vacante'),
    path('vacantes/<int:pk>/candidatos/', views.candidatos, name='candidatos'),
    path('postulaciones/<int:pk>/estado/', views.cambiar_estado, name='cambiar_estado'),
]
