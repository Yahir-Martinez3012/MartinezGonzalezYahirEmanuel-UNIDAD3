from django import forms

from cuentas.forms import BootstrapMixin

from .models import PerfilEstudiante
from .validators import MAX_CV_MB, validar_cv_pdf


class PerfilEstudianteForm(BootstrapMixin, forms.ModelForm):
    # El validador se aplica solo a archivos nuevos (no al CV ya guardado).
    cv = forms.FileField(
        label=f'CV en PDF (máx. {MAX_CV_MB} MB)', required=False, validators=[validar_cv_pdf],
        widget=forms.FileInput(attrs={'accept': 'application/pdf'}))

    class Meta:
        model = PerfilEstudiante
        fields = ['nombre_completo', 'carrera', 'cuatrimestre', 'es_egresado', 'telefono',
                  'habilidades', 'experiencia', 'cv']
        widgets = {
            'habilidades': forms.CheckboxSelectMultiple,
            'experiencia': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {'nombre_completo': 'Nombre completo', 'telefono': 'Teléfono de contacto'}

    def clean(self):
        datos = super().clean()
        if datos.get('es_egresado'):
            datos['cuatrimestre'] = None
        return datos
