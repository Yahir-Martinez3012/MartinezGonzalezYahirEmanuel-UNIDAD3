from unittest.mock import MagicMock, patch

import requests
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.models import Usuario
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion
from servicios import correo
from vacantes.models import Vacante

PWD = 'ConectaUTC2026!'
CLAVE = {'RESEND_API_KEY': 're_clave_de_prueba'}


def respuesta(status=200):
    r = MagicMock(status_code=status)
    r.raise_for_status.side_effect = None if status < 400 else requests.HTTPError('error')
    return r


class AdaptadorResendTests(TestCase):
    def test_sin_clave_no_envia_nada(self):
        with patch('servicios.correo.requests.post') as post:
            self.assertFalse(correo.habilitado())
            self.assertFalse(correo.enviar('a@b.com', 'Asunto', '<p>x</p>'))
            post.assert_not_called()

    @override_settings(**CLAVE)
    def test_envio_correcto(self):
        with patch('servicios.correo.requests.post', return_value=respuesta(200)) as post:
            self.assertTrue(correo.enviar('ana@utc.edu.mx', 'Hola', '<p>x</p>'))
            kw = post.call_args.kwargs
            self.assertEqual(post.call_args.args[0], 'https://api.resend.com/emails')
            self.assertEqual(kw['headers']['Authorization'], 'Bearer re_clave_de_prueba')
            self.assertEqual(kw['json']['to'], ['ana@utc.edu.mx'])
            self.assertEqual(kw['json']['subject'], 'Hola')
            self.assertEqual(kw['timeout'], 5)

    @override_settings(**CLAVE)
    def test_errores_no_rompen_la_aplicacion(self):
        with patch('servicios.correo.requests.post', side_effect=requests.Timeout()):
            self.assertFalse(correo.enviar('a@b.com', 'x', 'y'))
        with patch('servicios.correo.requests.post', return_value=respuesta(422)):
            self.assertFalse(correo.enviar('a@b.com', 'x', 'y'))


@override_settings(**CLAVE)
class NotificacionesDePostulacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)

    def setUp(self):
        self.perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        self.vacante = Vacante.objects.get(titulo='Auxiliar Contable')

    def test_al_postularse_el_estudiante_recibe_un_correo(self):
        with patch('servicios.correo.requests.post', return_value=respuesta()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            Postulacion.objects.create(estudiante=self.perfil, vacante=self.vacante)
        self.assertEqual(post.call_count, 1)
        cuerpo = post.call_args.kwargs['json']
        self.assertEqual(cuerpo['to'], ['estudiante_demo@ejemplo.com'])
        self.assertIn('Recibimos tu postulación', cuerpo['subject'])

    def test_al_cambiar_de_estado_se_avisa_y_sin_cambio_no(self):
        p = Postulacion.objects.create(estudiante=self.perfil, vacante=self.vacante)
        with patch('servicios.correo.requests.post', return_value=respuesta()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            p.estado = Postulacion.Estado.ENTREVISTA
            p.save()
        self.assertEqual(post.call_count, 1)
        self.assertIn('Entrevista', post.call_args.kwargs['json']['html'])
        with patch('servicios.correo.requests.post', return_value=respuesta()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            p.save()                                   # sin cambiar el estado
        post.assert_not_called()

    def test_la_empresa_cambia_el_estado_y_el_estudiante_es_notificado(self):
        p = Postulacion.objects.create(estudiante=self.perfil, vacante=Vacante.objects.get(titulo='Desarrollador Web Junior')) \
            if not Postulacion.objects.filter(estudiante=self.perfil, vacante__titulo='Desarrollador Web Junior').exists() \
            else Postulacion.objects.get(estudiante=self.perfil, vacante__titulo='Desarrollador Web Junior')
        self.client.login(username='empresa_demo', password=PWD)
        with patch('servicios.correo.requests.post', return_value=respuesta()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('empresas:cambiar_estado', args=[p.pk]), {'estado': 'aceptada'})
        self.assertIn('Aceptada', post.call_args.kwargs['json']['html'])

    def test_los_datos_se_escapan_en_el_cuerpo_del_correo(self):
        Vacante.objects.filter(pk=self.vacante.pk).update(titulo='<script>alert(1)</script>')
        self.vacante.refresh_from_db()
        with patch('servicios.correo.requests.post', return_value=respuesta()) as post, \
                self.captureOnCommitCallbacks(execute=True):
            Postulacion.objects.create(estudiante=self.perfil, vacante=self.vacante)
        html = post.call_args.kwargs['json']['html']
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_si_resend_falla_la_postulacion_se_guarda_igual(self):
        with patch('servicios.correo.requests.post', side_effect=requests.ConnectionError()), \
                self.captureOnCommitCallbacks(execute=True):
            Postulacion.objects.create(estudiante=self.perfil, vacante=self.vacante)
        self.assertTrue(Postulacion.objects.filter(estudiante=self.perfil, vacante=self.vacante).exists())

    def test_estudiante_sin_correo_no_genera_envio(self):
        Usuario.objects.filter(pk=self.perfil.usuario_id).update(email='')
        self.perfil.refresh_from_db()
        with patch('servicios.correo.requests.post') as post, self.captureOnCommitCallbacks(execute=True):
            Postulacion.objects.create(estudiante=self.perfil, vacante=self.vacante)
        post.assert_not_called()
