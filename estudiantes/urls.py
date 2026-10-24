from django.urls import path

from . import views

app_name = 'estudiantes'

urlpatterns = [
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('cv/<int:pk>/', views.descargar_cv, name='descargar_cv'),
]
