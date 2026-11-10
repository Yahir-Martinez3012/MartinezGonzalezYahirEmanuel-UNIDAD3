from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from empresas.models import Empresa
from servicios import geocodificacion
from vacantes.models import Vacante

PWD = 'ConectaUTC2026!'
SALTILLO = [{'lat': '25.4232000', 'lon': '-100.9737000', 'display_name': 'Saltillo'}]


def respuesta(json, status=200):
    r = MagicMock(status_code=status)
    r.json.return_value = json
    r.raise_for_status.side_effect = None if status < 400 else requests.HTTPError('error')
    return r


@override_settings(GEOCODIFICACION_HABILITADA=True)
class AdaptadorNominatimTests(TestCase):
    def test_devuelve_coordenadas_como_decimal(self):
        with patch('servicios.geocodificacion.requests.get', return_value=respuesta(SALTILLO)) as get:
            self.assertEqual(geocodificacion.geocodificar('Saltillo, Coahuila'),
                             (Decimal('25.423200'), Decimal('-100.973700')))
            params, cabeceras = get.call_args.kwargs['params'], get.call_args.kwargs['headers']
            self.assertEqual(params['limit'], 1)
            self.assertEqual(params['countrycodes'], 'mx')
            self.assertIn('ConectaUTC', cabeceras['User-Agent'])          # obligatorio en la política de Nominatim
            self.assertEqual(get.call_args.kwargs['timeout'], 5)

    def test_sin_resultados(self):
        with patch('servicios.geocodificacion.requests.get', return_value=respuesta([])):
            self.assertIsNone(geocodificacion.geocodificar('Lugar inexistente'))

    def test_errores_de_red_o_de_formato_no_rompen_la_aplicacion(self):
        with patch('servicios.geocodificacion.requests.get', side_effect=requests.Timeout()):
            self.assertIsNone(geocodificacion.geocodificar('Saltillo'))
        with patch('servicios.geocodificacion.requests.get', return_value=respuesta(status=429, json={})):
            self.assertIsNone(geocodificacion.geocodificar('Saltillo'))
        with patch('servicios.geocodificacion.requests.get', return_value=respuesta([{'raro': 1}])):
            self.assertIsNone(geocodificacion.geocodificar('Saltillo'))

    def test_direccion_vacia_no_consulta(self):
        with patch('servicios.geocodificacion.requests.get') as get:
            self.assertIsNone(geocodificacion.geocodificar('   '))
            get.assert_not_called()

    @override_settings(GEOCODIFICACION_HABILITADA=False)
    def test_deshabilitado_no_consulta(self):
        with patch('servicios.geocodificacion.requests.get') as get:
            self.assertIsNone(geocodificacion.geocodificar('Saltillo'))
            get.assert_not_called()


@override_settings(GEOCODIFICACION_HABILITADA=True)
class CoordenadasEnVacantesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)
        cls.datos = {'titulo': 'Becario de TI', 'descripcion': 'Apoyo.', 'requisitos': 'Ganas.', 'tipo': 'practicas',
                     'modalidad': 'presencial', 'experiencia': 'ninguna', 'ubicacion': 'Saltillo, Coahuila',
                     'horario': '', 'salario': ''}

    def setUp(self):
        self.client.login(username='empresa_demo', password=PWD)

    def test_al_crear_la_vacante_se_guardan_las_coordenadas(self):
        with patch('servicios.geocodificacion.geocodificar', return_value=(Decimal('25.4'), Decimal('-100.9'))) as g:
            self.client.post(reverse('empresas:crear_vacante'), self.datos)
            g.assert_called_once_with('Saltillo, Coahuila')
        v = Vacante.objects.get(titulo='Becario de TI')
        self.assertTrue(v.tiene_coordenadas)
        self.assertEqual(v.latitud, Decimal('25.400000'))

    def test_vacante_remota_no_se_geocodifica(self):
        with patch('servicios.geocodificacion.requests.get') as get:
            self.client.post(reverse('empresas:crear_vacante'), {**self.datos, 'modalidad': 'remota'})
            get.assert_not_called()
        self.assertFalse(Vacante.objects.get(titulo='Becario de TI').tiene_coordenadas)

    def test_si_el_servicio_falla_la_vacante_se_crea_igual(self):
        with patch('servicios.geocodificacion.requests.get', side_effect=requests.ConnectionError()):
            r = self.client.post(reverse('empresas:crear_vacante'), self.datos)
        self.assertRedirects(r, reverse('empresas:panel'))
        self.assertFalse(Vacante.objects.get(titulo='Becario de TI').tiene_coordenadas)

    def test_editar_sin_cambiar_el_lugar_no_vuelve_a_consultar(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        datos = {**self.datos, 'titulo': v.titulo, 'modalidad': v.modalidad, 'ubicacion': v.ubicacion}
        with patch('servicios.geocodificacion.geocodificar') as g:
            self.client.post(reverse('empresas:editar_vacante', args=[v.pk]), datos)
            g.assert_not_called()

    def test_editar_cambiando_el_lugar_vuelve_a_consultar(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        datos = {**self.datos, 'titulo': v.titulo, 'modalidad': v.modalidad, 'ubicacion': 'Arteaga, Coahuila'}
        with patch('servicios.geocodificacion.geocodificar', return_value=(Decimal('25.44'), Decimal('-100.85'))):
            self.client.post(reverse('empresas:editar_vacante', args=[v.pk]), datos)
        v.refresh_from_db()
        self.assertEqual(v.latitud, Decimal('25.440000'))

    def test_los_datos_demo_traen_coordenadas_y_las_remotas_no(self):
        self.assertTrue(Vacante.objects.get(titulo='Desarrollador Web Junior').tiene_coordenadas)
        self.assertFalse(Vacante.objects.get(titulo='Prácticas en Análisis de Datos').tiene_coordenadas)   # remota

    def test_comando_completa_solo_las_que_faltan(self):
        Vacante.objects.filter(titulo='Auxiliar Contable').update(latitud=None, longitud=None)
        with patch('servicios.geocodificacion.geocodificar', return_value=(Decimal('25.42'), Decimal('-100.99'))) as g, \
                patch('vacantes.management.commands.geocodificar_vacantes.time.sleep') as espera:
            call_command('geocodificar_vacantes', verbosity=0)
            self.assertEqual(g.call_count, 1)
            espera.assert_called_once_with(1.1)                      # respeta el límite de 1 petición por segundo
        self.assertTrue(Vacante.objects.get(titulo='Auxiliar Contable').tiene_coordenadas)
