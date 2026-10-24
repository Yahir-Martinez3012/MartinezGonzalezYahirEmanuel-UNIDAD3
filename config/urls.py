from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('cuentas.urls')),
    path('estudiante/', include('estudiantes.urls')),
    path('empresa/', include('empresas.urls')),
    path('vacantes/', include('vacantes.urls')),
    path('', include('core.urls')),
]
