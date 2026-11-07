from datetime import timedelta

from django.contrib.auth import authenticate
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import IntentoLogin, Usuario

OK = 'ClaveSegura#2026'


class BloqueoPorIntentosTests(TestCase):
    def setUp(self):
        Usuario.objects.create_user('ana', 'ana@utc.edu.mx', OK)
        Usuario.objects.create_user('luis', 'luis@utc.edu.mx', OK)
        self.url = reverse('cuentas:login')

    def fallar(self, usuario='ana', veces=1):
        for _ in range(veces):
            r = self.client.post(self.url, {'username': usuario, 'password': 'incorrecta'})
        return r

    def test_cada_fallo_queda_registrado(self):
        self.fallar(veces=2)
        self.assertEqual(IntentoLogin.objects.filter(usuario='ana').count(), 2)

    def test_cuenta_se_bloquea_al_quinto_fallo_aunque_la_clave_sea_correcta(self):
        self.fallar(veces=5)
        r = self.client.post(self.url, {'username': 'ana', 'password': OK})
        self.assertContains(r, 'Demasiados intentos fallidos')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cuatro_fallos_todavia_no_bloquean(self):
        self.fallar(veces=4)
        r = self.client.post(self.url, {'username': 'ana', 'password': OK})
        self.assertRedirects(r, reverse('inicio'))

    def test_el_bloqueo_expira(self):
        self.fallar(veces=5)
        IntentoLogin.objects.update(creado=timezone.now() - timedelta(minutes=16))
        r = self.client.post(self.url, {'username': 'ana', 'password': OK})
        self.assertRedirects(r, reverse('inicio'))

    def test_acceso_correcto_reinicia_el_contador(self):
        self.fallar(veces=3)
        self.client.post(self.url, {'username': 'ana', 'password': OK})
        self.client.post(reverse('cuentas:logout'))
        self.assertEqual(IntentoLogin.objects.filter(usuario='ana').count(), 0)

    def test_el_bloqueo_es_por_usuario(self):
        self.fallar('ana', 5)
        r = self.client.post(self.url, {'username': 'luis', 'password': OK})
        self.assertRedirects(r, reverse('inicio'))

    def test_usuario_inexistente_recibe_el_mismo_mensaje(self):
        self.fallar('fantasma', 5)
        r = self.client.post(self.url, {'username': 'fantasma', 'password': 'x'})
        self.assertContains(r, 'Demasiados intentos fallidos')      # no revela si la cuenta existe

    @override_settings(LOGIN_MAX_INTENTOS=2)
    def test_el_limite_es_configurable(self):
        self.fallar(veces=2)
        self.assertContains(self.client.post(self.url, {'username': 'ana', 'password': OK}), 'Demasiados intentos')

    def test_se_guarda_la_ip_detras_de_un_proxy(self):
        self.client.post(self.url, {'username': 'ana', 'password': 'x'}, HTTP_X_FORWARDED_FOR='203.0.113.7, 10.0.0.1')
        self.assertEqual(IntentoLogin.objects.get().ip, '203.0.113.7')

    def test_la_bitacora_es_de_solo_lectura_en_el_admin(self):
        Usuario.objects.create_superuser('root', 'r@utc.edu.mx', OK)
        IntentoLogin.objects.create(usuario='ana', ip='203.0.113.7')
        self.client.login(username='root', password=OK)
        r = self.client.get(reverse('admin:cuentas_intentologin_changelist'))
        self.assertContains(r, 'ana')
        self.assertEqual(self.client.get(reverse('admin:cuentas_intentologin_add')).status_code, 403)
