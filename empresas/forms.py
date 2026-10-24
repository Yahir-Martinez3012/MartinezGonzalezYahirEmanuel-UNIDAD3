from django import forms

from cuentas.forms import BootstrapMixin

from .models import Empresa


class EmpresaForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'sector', 'descripcion', 'sitio_web', 'telefono', 'ciudad']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 4})}
        labels = {'nombre': 'Nombre de la empresa'}
