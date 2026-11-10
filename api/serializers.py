from rest_framework import serializers

from catalogo.models import Carrera, Habilidad
from postulaciones.models import Postulacion
from vacantes.models import Vacante


class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = ['id', 'nombre']


class HabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habilidad
        fields = ['id', 'nombre']


class EmpresaPublicaSerializer(serializers.Serializer):
    """Solo datos públicos de la empresa: nunca se expone el correo ni el usuario."""
    nombre = serializers.CharField()
    sector = serializers.CharField()
    ciudad = serializers.CharField()
    sitio_web = serializers.URLField()


class VacanteListaSerializer(serializers.ModelSerializer):
    empresa = serializers.CharField(source='empresa.nombre')
    tipo_display = serializers.CharField(source='get_tipo_display')
    modalidad_display = serializers.CharField(source='get_modalidad_display')
    habilidades = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')

    class Meta:
        model = Vacante
        fields = ['id', 'titulo', 'empresa', 'tipo', 'tipo_display', 'modalidad', 'modalidad_display',
                  'ubicacion', 'salario', 'experiencia', 'habilidades', 'destacada',
                  'fecha_publicacion', 'fecha_limite']


class VacanteDetalleSerializer(VacanteListaSerializer):
    empresa = EmpresaPublicaSerializer(read_only=True)
    carreras = serializers.SlugRelatedField(many=True, read_only=True, slug_field='nombre')

    class Meta(VacanteListaSerializer.Meta):
        fields = VacanteListaSerializer.Meta.fields + ['descripcion', 'requisitos', 'horario', 'carreras',
                                                       'latitud', 'longitud']


class VacanteResumenSerializer(serializers.ModelSerializer):
    empresa = serializers.CharField(source='empresa.nombre')

    class Meta:
        model = Vacante
        fields = ['id', 'titulo', 'empresa']


class PostulacionSerializer(serializers.ModelSerializer):
    vacante = VacanteResumenSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Postulacion
        fields = ['id', 'vacante', 'estado', 'estado_display', 'fecha']
