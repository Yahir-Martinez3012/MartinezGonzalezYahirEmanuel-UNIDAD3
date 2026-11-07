from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class ContrasenasYSesionesTests(TestCase):
    DATOS = {'username': 'ana', 'email': 'ana@utc.edu.mx', 'rol': 'estudiante'}

    def registrar(self, clave):
        return self.client.post(reverse('cuentas:registro'), {**self.DATOS, 'password1': clave, 'password2': clave})

    def test_contrasena_de_9_caracteres_rechazada(self):
        r = self.registrar('Abcd#1234')                          # 9 caracteres
        self.assertContains(r, 'al menos 10 caracteres')
        self.assertFalse(Usuario.objects.exists())

    def test_contrasena_de_10_caracteres_aceptada(self):
        self.assertRedirects(self.registrar('Abcd#12345'), reverse('estudiantes:editar_perfil'))

    def test_contrasena_comun_rechazada(self):
        r = self.registrar('password123')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Usuario.objects.exists())

    def test_parametros_de_sesion_y_cookies(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 7200)
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')

    def test_cookie_de_sesion_es_httponly(self):
        self.registrar('Abcd#12345')
        self.assertTrue(self.client.cookies[settings.SESSION_COOKIE_NAME]['httponly'])

    def test_la_pagina_no_se_puede_incrustar_en_un_iframe(self):
        self.assertEqual(self.client.get(reverse('inicio'))['X-Frame-Options'], 'DENY')
