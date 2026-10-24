from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Carrera
from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion

from .models import Favorito, Vacante

PWD = 'ConectaUTC2026!'


class VacantesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)

    def test_lista_solo_muestra_vacantes_abiertas(self):
        r = self.client.get(reverse('vacantes:lista'))
        titulos = [v.titulo for v in r.context['page_obj']]
        self.assertIn('Desarrollador Web Junior', titulos)
        self.assertNotIn('Diseñador UX/UI (medio tiempo)', titulos)
        self.assertNotIn('Operador de Producción (vacante cerrada)', titulos)

    def test_vencida_no_aparece(self):
        Vacante.objects.filter(titulo='Auxiliar Contable').update(fecha_limite=timezone.localdate() - timedelta(days=1))
        r = self.client.get(reverse('vacantes:lista'), {'q': 'Auxiliar Contable'})
        self.assertEqual(r.context['total'], 0)

    def test_filtros(self):
        url = reverse('vacantes:lista')
        self.assertTrue(all(v.modalidad == 'remota' for v in self.client.get(url, {'modalidad': 'remota'}).context['page_obj']))
        self.assertTrue(all(v.tipo == 'practicas' for v in self.client.get(url, {'tipo': 'practicas'}).context['page_obj']))
        self.assertEqual(self.client.get(url, {'q': 'Django'}).context['total'], 1)
        self.assertGreater(self.client.get(url, {'ubicacion': 'Ramos'}).context['total'], 0)
        carrera = Carrera.objects.get(nombre='TSU en Contaduría')
        for v in self.client.get(url, {'carrera': carrera.pk}).context['page_obj']:
            self.assertTrue(not v.carreras.exists() or carrera in v.carreras.all())
        empresa = Empresa.objects.get(nombre='AutoPartes Saltillo')
        self.assertTrue(all(v.empresa == empresa for v in self.client.get(url, {'empresa': empresa.pk}).context['page_obj']))
        self.assertGreater(self.client.get(url, {'experiencia': 'ninguna'}).context['total'], 0)
        self.assertGreater(self.client.get(url, {'fecha': 'mes'}).context['total'], 0)
        self.assertEqual(self.client.get(url, {'fecha': 'hoy', 'q': 'Ingeniero de Automatización'}).context['total'], 0)

    def test_detalle_publico_y_vista_previa(self):
        pub = Vacante.objects.get(titulo='Desarrollador Web Junior')
        self.assertContains(self.client.get(pub.get_absolute_url()), 'Inicia sesión para postularte')   # invitado
        pend = Vacante.objects.get(titulo='Diseñador UX/UI (medio tiempo)')
        self.assertEqual(self.client.get(pend.get_absolute_url()).status_code, 404)
        self.client.login(username='empresa_demo', password=PWD)       # su dueña sí la ve
        self.assertEqual(self.client.get(pend.get_absolute_url()).status_code, 200)

    def test_postular_exige_sesion_rol_y_cv(self):
        v = Vacante.objects.get(titulo='Prácticas en Soporte Técnico')
        url = reverse('vacantes:postular', args=[v.pk])
        self.assertEqual(self.client.post(url).status_code, 302)       # sin sesión
        self.assertFalse(Postulacion.objects.filter(vacante=v).exists())
        self.client.login(username='empresa_demo', password=PWD)
        self.assertEqual(self.client.post(url).status_code, 403)       # empresa no puede postularse
        self.client.login(username='estudiante_demo', password=PWD)
        self.assertEqual(self.client.get(url).status_code, 405)        # solo POST
        r = self.client.post(url)                                      # sin CV
        self.assertRedirects(r, reverse('estudiantes:editar_perfil'))
        self.assertFalse(Postulacion.objects.filter(vacante=v).exists())

    @override_settings(MEDIA_ROOT='/tmp/conecta_test_media')
    def test_postular_con_cv_y_sin_duplicados(self):
        self.client.login(username='estudiante_demo', password=PWD)
        perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        perfil.cv.save('x.pdf', SimpleUploadedFile('x.pdf', b'%PDF-1.4 prueba'))
        v = Vacante.objects.get(titulo='Prácticas en Soporte Técnico')
        url = reverse('vacantes:postular', args=[v.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(Postulacion.objects.filter(estudiante=perfil, vacante=v).count(), 1)
        self.assertEqual(Postulacion.objects.get(estudiante=perfil, vacante=v).estado, 'enviada')

    def test_no_se_postula_a_vacante_cerrada_o_pendiente(self):
        self.client.login(username='estudiante_demo', password=PWD)
        for t in ('Operador de Producción (vacante cerrada)', 'Diseñador UX/UI (medio tiempo)'):
            v = Vacante.objects.get(titulo=t)
            self.assertEqual(self.client.post(reverse('vacantes:postular', args=[v.pk])).status_code, 404)

    def test_favorito_alterna(self):
        self.client.login(username='estudiante_demo', password=PWD)
        perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        v = Vacante.objects.get(titulo='Auxiliar Contable')
        url = reverse('vacantes:favorito', args=[v.pk])
        self.client.post(url)
        self.assertTrue(Favorito.objects.filter(estudiante=perfil, vacante=v).exists())
        self.client.post(url)
        self.assertFalse(Favorito.objects.filter(estudiante=perfil, vacante=v).exists())

    def test_favorito_no_redirige_a_sitios_externos(self):
        self.client.login(username='estudiante_demo', password=PWD)
        v = Vacante.objects.get(titulo='Auxiliar Contable')
        r = self.client.post(reverse('vacantes:favorito', args=[v.pk]), {'next': 'https://malicioso.com'})
        self.assertRedirects(r, v.get_absolute_url())
