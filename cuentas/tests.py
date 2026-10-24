from django.test import TestCase
from django.urls import reverse

from .models import Usuario

DATOS = {'username': 'ana', 'email': 'ana@utc.edu.mx', 'rol': 'estudiante',
         'password1': 'ClaveSegura#2026', 'password2': 'ClaveSegura#2026'}


class RegistroTests(TestCase):
    def test_registro_estudiante_inicia_sesion(self):
        r = self.client.post(reverse('cuentas:registro'), DATOS)
        self.assertRedirects(r, reverse('estudiantes:editar_perfil'))
        u = Usuario.objects.get(username='ana')
        self.assertTrue(hasattr(u, 'perfil_estudiante'))
        self.assertEqual(u.rol, Usuario.Rol.ESTUDIANTE)
        self.assertEqual(int(self.client.session['_auth_user_id']), u.pk)

    def test_registro_empresa(self):
        r = self.client.post(reverse('cuentas:registro'), {**DATOS, 'username': 'acme', 'email': 'a@acme.com', 'rol': 'empresa'})
        self.assertRedirects(r, reverse('empresas:editar_perfil'))
        u = Usuario.objects.get(username='acme')
        self.assertEqual(u.rol, Usuario.Rol.EMPRESA)
        self.assertEqual(u.empresa.estado, 'pendiente')

    def test_no_se_puede_registrar_como_admin(self):
        r = self.client.post(reverse('cuentas:registro'), {**DATOS, 'rol': 'admin'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Usuario.objects.exists())

    def test_correo_duplicado_rechazado(self):
        self.client.post(reverse('cuentas:registro'), DATOS)
        self.client.post(reverse('cuentas:logout'))
        r = self.client.post(reverse('cuentas:registro'), {**DATOS, 'username': 'otra', 'email': 'ANA@utc.edu.mx'})
        self.assertContains(r, 'Ya existe una cuenta')
        self.assertEqual(Usuario.objects.count(), 1)

    def test_contrasena_guardada_con_hash(self):
        self.client.post(reverse('cuentas:registro'), DATOS)
        self.assertNotEqual(Usuario.objects.get(username='ana').password, DATOS['password1'])

    def test_contrasena_debil_rechazada(self):
        r = self.client.post(reverse('cuentas:registro'), {**DATOS, 'password1': '12345678', 'password2': '12345678'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Usuario.objects.exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        Usuario.objects.create_user('ana', 'ana@utc.edu.mx', 'ClaveSegura#2026')

    def test_login_correcto(self):
        r = self.client.post(reverse('cuentas:login'), {'username': 'ana', 'password': 'ClaveSegura#2026'})
        self.assertRedirects(r, reverse('inicio'))

    def test_superusuario_es_admin_utc(self):
        u = Usuario.objects.create_superuser('root', 'r@utc.edu.mx', 'ClaveSegura#2026')
        self.assertEqual(u.rol, Usuario.Rol.ADMIN)
        self.assertTrue(u.es_admin_utc)

    def test_login_incorrecto(self):
        r = self.client.post(reverse('cuentas:login'), {'username': 'ana', 'password': 'mala'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requiere_post(self):
        self.client.login(username='ana', password='ClaveSegura#2026')
        self.assertEqual(self.client.get(reverse('cuentas:logout')).status_code, 405)
        self.client.post(reverse('cuentas:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_navbar_cambia_segun_sesion(self):
        self.assertContains(self.client.get(reverse('inicio')), 'Registrarse')
        self.client.login(username='ana', password='ClaveSegura#2026')
        r = self.client.get(reverse('inicio'))
        self.assertContains(r, 'Cerrar sesión')
        self.assertContains(r, 'Estudiante')
