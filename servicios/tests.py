from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.models import IntentoLogin, Usuario
from servicios import recaptcha

CLAVES = {'RECAPTCHA_SITE_KEY': 'sitio-prueba', 'RECAPTCHA_SECRET_KEY': 'secreta-prueba'}
OK = 'ClaveSegura#2026'


def respuesta(json=None, status=200):
    r = MagicMock(status_code=status)
    r.json.return_value = json or {}
    r.raise_for_status.side_effect = None if status < 400 else requests.HTTPError('error')
    return r


class RecaptchaAdaptadorTests(TestCase):
    def test_sin_claves_esta_deshabilitado_y_no_llama_a_google(self):
        with patch('servicios.recaptcha.requests.post') as post:
            self.assertFalse(recaptcha.habilitado())
            self.assertTrue(recaptcha.verificar(None))
            post.assert_not_called()

    @override_settings(**CLAVES)
    def test_token_valido(self):
        with patch('servicios.recaptcha.requests.post', return_value=respuesta({'success': True})) as post:
            self.assertTrue(recaptcha.verificar('token', '203.0.113.7'))
            datos = post.call_args.kwargs['data']
            self.assertEqual(datos['secret'], 'secreta-prueba')
            self.assertEqual(datos['response'], 'token')
            self.assertEqual(post.call_args.kwargs['timeout'], 5)

    @override_settings(**CLAVES)
    def test_token_invalido(self):
        with patch('servicios.recaptcha.requests.post', return_value=respuesta({'success': False})):
            self.assertFalse(recaptcha.verificar('token'))

    @override_settings(**CLAVES)
    def test_sin_token_se_rechaza_sin_llamar_a_google(self):
        with patch('servicios.recaptcha.requests.post') as post:
            self.assertFalse(recaptcha.verificar(''))
            post.assert_not_called()

    @override_settings(**CLAVES)
    def test_si_google_no_responde_se_rechaza(self):
        for error in (requests.Timeout(), requests.ConnectionError()):
            with patch('servicios.recaptcha.requests.post', side_effect=error):
                self.assertFalse(recaptcha.verificar('token'))
        with patch('servicios.recaptcha.requests.post', return_value=respuesta(status=500)):
            self.assertFalse(recaptcha.verificar('token'))


@override_settings(**CLAVES)
class RecaptchaEnFormulariosTests(TestCase):
    DATOS = {'username': 'ana', 'email': 'ana@utc.edu.mx', 'rol': 'estudiante',
             'password1': OK, 'password2': OK}

    def test_el_widget_aparece_con_la_clave_publica(self):
        for nombre in ('cuentas:registro', 'cuentas:login'):
            r = self.client.get(reverse(nombre))
            self.assertContains(r, 'g-recaptcha')
            self.assertContains(r, 'data-sitekey="sitio-prueba"')
            self.assertNotContains(r, 'secreta-prueba')            # la clave privada nunca llega al navegador

    @override_settings(RECAPTCHA_SITE_KEY='', RECAPTCHA_SECRET_KEY='')
    def test_sin_configurar_no_se_muestra(self):
        self.assertNotContains(self.client.get(reverse('cuentas:login')), 'g-recaptcha')

    def test_registro_sin_captcha_es_rechazado(self):
        r = self.client.post(reverse('cuentas:registro'), self.DATOS)
        self.assertContains(r, 'no eres un robot')
        self.assertFalse(Usuario.objects.exists())

    def test_registro_con_captcha_valido(self):
        with patch('servicios.recaptcha.requests.post', return_value=respuesta({'success': True})):
            r = self.client.post(reverse('cuentas:registro'), {**self.DATOS, 'g-recaptcha-response': 'tok'})
        self.assertRedirects(r, reverse('estudiantes:editar_perfil'))

    def test_registro_con_captcha_falso(self):
        with patch('servicios.recaptcha.requests.post', return_value=respuesta({'success': False})):
            r = self.client.post(reverse('cuentas:registro'), {**self.DATOS, 'g-recaptcha-response': 'falso'})
        self.assertContains(r, 'no eres un robot')
        self.assertFalse(Usuario.objects.exists())

    def test_login_sin_captcha_no_cuenta_como_intento_fallido(self):
        Usuario.objects.create_user('ana', 'a@utc.edu.mx', OK)
        for _ in range(10):
            self.client.post(reverse('cuentas:login'), {'username': 'ana', 'password': 'mala'})
        self.assertEqual(IntentoLogin.objects.count(), 0)       # un robot no puede ni provocar bloqueos

    def test_login_con_captcha_valido(self):
        Usuario.objects.create_user('ana', 'a@utc.edu.mx', OK)
        with patch('servicios.recaptcha.requests.post', return_value=respuesta({'success': True})):
            r = self.client.post(reverse('cuentas:login'),
                                 {'username': 'ana', 'password': OK, 'g-recaptcha-response': 'tok'})
        self.assertRedirects(r, reverse('inicio'))

    def test_la_politica_csp_permite_recaptcha(self):
        csp = self.client.get(reverse('cuentas:login'))['Content-Security-Policy']
        self.assertIn('https://www.google.com/recaptcha/', csp)
        self.assertIn('frame-src', csp)
