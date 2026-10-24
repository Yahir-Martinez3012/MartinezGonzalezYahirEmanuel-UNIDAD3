import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.models import Carrera, Habilidad
from cuentas.models import Usuario
from postulaciones.models import Postulacion
from vacantes.models import Vacante

from .models import PerfilEstudiante

PWD = 'ConectaUTC2026!'
PDF = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF'


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PerfilTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client.login(username='estudiante_demo', password=PWD)
        self.url = reverse('estudiantes:editar_perfil')
        self.base = {'nombre_completo': 'Ana M.', 'carrera': Carrera.objects.first().pk, 'cuatrimestre': 8,
                     'telefono': '844 123 4567', 'experiencia': 'Proyectos', 'habilidades': [Habilidad.objects.first().pk]}

    def test_empresa_no_edita_perfil_de_estudiante(self):
        self.client.login(username='empresa_demo', password=PWD)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_guardar_perfil_con_cv_valido(self):
        r = self.client.post(self.url, {**self.base, 'cv': SimpleUploadedFile('cv.pdf', PDF, 'application/pdf')})
        self.assertRedirects(r, reverse('estudiantes:perfil'))
        perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        self.assertTrue(perfil.cv.name.startswith('cvs/') and perfil.cv.name.endswith('.pdf'))
        self.assertNotIn('cv.pdf', perfil.cv.name)             # nombre aleatorio

    def test_cv_rechaza_extension_falsa_y_contenido_falso(self):
        r = self.client.post(self.url, {**self.base, 'cv': SimpleUploadedFile('virus.exe', PDF)})
        self.assertContains(r, 'extensión .pdf')
        r = self.client.post(self.url, {**self.base, 'cv': SimpleUploadedFile('falso.pdf', b'MZ no soy un pdf')})
        self.assertContains(r, 'no es un PDF válido')

    def test_cv_rechaza_archivo_grande(self):
        grande = SimpleUploadedFile('grande.pdf', b'%PDF-' + b'0' * (5 * 1024 * 1024 + 10))
        self.assertContains(self.client.post(self.url, {**self.base, 'cv': grande}), 'no puede pesar más de 5 MB')

    def test_reemplazar_cv_borra_el_anterior(self):
        self.client.post(self.url, {**self.base, 'cv': SimpleUploadedFile('a.pdf', PDF)})
        perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        viejo = perfil.cv.name
        self.client.post(self.url, {**self.base, 'cv': SimpleUploadedFile('b.pdf', PDF)})
        perfil.refresh_from_db()
        self.assertNotEqual(perfil.cv.name, viejo)
        self.assertFalse(perfil.cv.storage.exists(viejo))

    def test_egresado_limpia_cuatrimestre(self):
        self.client.post(self.url, {**self.base, 'es_egresado': 'on'})
        self.assertIsNone(PerfilEstudiante.objects.get(usuario__username='estudiante_demo').cuatrimestre)

    def test_telefono_invalido(self):
        self.assertContains(self.client.post(self.url, {**self.base, 'telefono': 'abc'}), 'teléfono válido')

    def test_perfil_muestra_postulaciones_y_favoritos(self):
        r = self.client.get(reverse('estudiantes:perfil'))
        self.assertContains(r, 'Historial de postulaciones')
        self.assertContains(r, 'Desarrollador Web Junior')
        self.assertContains(r, 'Enviada')

    def test_permisos_para_descargar_cv(self):
        self.client.post(self.url, {**self.base, 'cv': SimpleUploadedFile('cv.pdf', PDF)})
        perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        url = reverse('estudiantes:descargar_cv', args=[perfil.pk])
        r = self.client.get(url)                                # dueño
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.client.login(username='admin_utc', password=PWD)   # admin
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.login(username='empresa_demo', password=PWD)   # empresa donde se postuló
        self.assertEqual(self.client.get(url).status_code, 200)
        otra = Usuario.objects.get(username='empresa_autopartes')
        otra.set_password(PWD); otra.save()
        Postulacion.objects.filter(estudiante=perfil, vacante__empresa__usuario=otra).delete()
        self.client.login(username='empresa_autopartes', password=PWD)   # empresa sin postulación
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)          # sin sesión
