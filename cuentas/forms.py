from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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


class RegistroForm(BootstrapMixin, UserCreationForm):
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


class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.CharField(label='Nombre de usuario')
    password = forms.CharField(label='Contraseña', strip=False, widget=forms.PasswordInput)
