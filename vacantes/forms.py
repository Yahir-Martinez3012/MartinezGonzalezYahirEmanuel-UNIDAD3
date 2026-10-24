from datetime import timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from catalogo.models import Carrera
from cuentas.forms import BootstrapMixin
from empresas.models import Empresa

from .models import Vacante


class VacanteForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Vacante
        fields = ['titulo', 'descripcion', 'requisitos', 'tipo', 'modalidad', 'experiencia', 'ubicacion',
                  'horario', 'salario', 'fecha_limite', 'carreras', 'habilidades']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 5}),
            'requisitos': forms.Textarea(attrs={'rows': 4}),
            'fecha_limite': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'carreras': forms.CheckboxSelectMultiple,
            'habilidades': forms.CheckboxSelectMultiple,
        }

    def clean_fecha_limite(self):
        fecha = self.cleaned_data.get('fecha_limite')
        nueva = not self.instance.pk or 'fecha_limite' in self.changed_data
        if fecha and nueva and fecha < timezone.localdate():
            raise forms.ValidationError('La fecha límite no puede estar en el pasado.')
        return fecha


class VacanteFiltroForm(BootstrapMixin, forms.Form):
    FECHAS = [('', 'Cualquier fecha'), ('hoy', 'Hoy'), ('semana', 'Últimos 7 días'), ('mes', 'Últimos 30 días')]

    q = forms.CharField(label='Palabra clave', required=False)
    carrera = forms.ModelChoiceField(Carrera.objects.all(), label='Carrera', required=False, empty_label='Todas')
    empresa = forms.ModelChoiceField(Empresa.objects.none(), label='Empresa', required=False, empty_label='Todas')
    modalidad = forms.ChoiceField(label='Modalidad', required=False,
                                  choices=[('', 'Todas')] + Vacante.Modalidad.choices)
    ubicacion = forms.CharField(label='Ubicación', required=False)
    tipo = forms.ChoiceField(label='Tipo de empleo', required=False,
                             choices=[('', 'Todos')] + Vacante.Tipo.choices)
    experiencia = forms.ChoiceField(label='Experiencia', required=False,
                                    choices=[('', 'Cualquiera')] + Vacante.Experiencia.choices)
    fecha = forms.ChoiceField(label='Fecha de publicación', required=False, choices=FECHAS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = Empresa.objects.filter(estado=Empresa.Estado.APROBADA)

    def filtrar(self, qs):
        d = self.cleaned_data
        if d.get('q'):
            q = d['q']
            qs = qs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q)
                           | Q(empresa__nombre__icontains=q) | Q(habilidades__nombre__icontains=q))
        if d.get('carrera'):   # una vacante sin carreras indicadas es para cualquier carrera
            qs = qs.filter(Q(carreras=d['carrera']) | Q(carreras__isnull=True))
        if d.get('empresa'):
            qs = qs.filter(empresa=d['empresa'])
        if d.get('modalidad'):
            qs = qs.filter(modalidad=d['modalidad'])
        if d.get('ubicacion'):
            qs = qs.filter(ubicacion__icontains=d['ubicacion'])
        if d.get('tipo'):
            qs = qs.filter(tipo=d['tipo'])
        if d.get('experiencia'):
            qs = qs.filter(experiencia=d['experiencia'])
        dias = {'hoy': 0, 'semana': 7, 'mes': 30}.get(d.get('fecha'))
        if dias is not None:
            desde = timezone.localdate() - timedelta(days=dias)
            qs = qs.filter(fecha_publicacion__date__gte=desde)
        return qs.distinct()
