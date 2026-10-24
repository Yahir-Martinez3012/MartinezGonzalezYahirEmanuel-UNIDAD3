from django.urls import path

from . import views

app_name = 'vacantes'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/postular/', views.postular, name='postular'),
    path('<int:pk>/favorito/', views.favorito, name='favorito'),
]
