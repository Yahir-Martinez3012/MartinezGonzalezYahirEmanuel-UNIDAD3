from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm

app_name = 'cuentas'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', LoginView.as_view(
        template_name='cuentas/login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),   # solo acepta POST
]
