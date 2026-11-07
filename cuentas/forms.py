from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from servicios import recaptcha

from . import seguridad
from .models import Usuario


class BootstrapMixin:
    """Agrega las clases de Bootstrap 5 a todos los campos del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            w = campo.widget
            if isinstance(w, forms.CheckboxSelectMultiple):
                continue
            if isinstance(w, forms.CheckboxInput):
                clase = 'form-check-input'
            elif isinstance(w, forms.Select):
                clase = 'form-select'
            else:
                clase = 'form-control'
            w.attrs['class'] = f"{w.attrs.get('class', '')} {clase}".strip()


class CaptchaMixin:
    """Exige resolver reCAPTCHA antes de procesar el formulario (si el servicio está configurado).

    Se valida primero, para que un robot no pueda ni siquiera provocar intentos de inicio de sesión.
    """

    def clean(self):
        if recaptcha.habilitado():
            token = self.data.get('g-recaptcha-response')
            ip = seguridad.ip_cliente(getattr(self, 'request', None))
            if not recaptcha.verificar(token, ip):
                raise forms.ValidationError('Confirma que no eres un robot e inténtalo de nuevo.', code='captcha')
        return super().clean()


class RegistroForm(CaptchaMixin, BootstrapMixin, UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    # Solo se permiten estos dos roles: el administrador UTC nunca se crea desde el registro público.
    rol = forms.ChoiceField(
        label='¿Cómo usarás Conecta UTC?',
        choices=[
            (Usuario.Rol.ESTUDIANTE, 'Soy estudiante o egresado de la UTC'),
            (Usuario.Rol.EMPRESA, 'Represento a una empresa'),
        ],
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'rol')
        labels = {'username': 'Nombre de usuario'}

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo.')
        return email


class LoginForm(CaptchaMixin, BootstrapMixin, AuthenticationForm):
    username = forms.CharField(label='Nombre de usuario')
    password = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput)

    def clean(self):
        usuario = self.cleaned_data.get('username')
        if usuario and seguridad.esta_bloqueado(usuario):
            # El mensaje es igual exista o no la cuenta, para no revelar qué usuarios están registrados.
            raise forms.ValidationError(
                'Demasiados intentos fallidos. Por seguridad, espera %(min)s minuto(s) antes de volver a intentar.',
                code='bloqueado', params={'min': seguridad.minutos_restantes(usuario)})
        return super().clean()
