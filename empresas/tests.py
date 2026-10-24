from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Carrera, Habilidad
from cuentas.models import Usuario
from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion
from vacantes.models import Vacante

PWD = 'ConectaUTC2026!'


class PanelEmpresaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)
        cls.datos = {'titulo': 'Becario de TI', 'descripcion': 'Apoyo al equipo.', 'requisitos': 'Ganas de aprender.',
                     'tipo': 'practicas', 'modalidad': 'presencial', 'experiencia': 'ninguna',
                     'ubicacion': 'Saltillo', 'horario': '', 'salario': ''}

    def setUp(self):
        self.client.login(username='empresa_demo', password=PWD)

    def test_estudiante_no_entra_al_panel(self):
        self.client.login(username='estudiante_demo', password=PWD)
        self.assertEqual(self.client.get(reverse('empresas:panel')).status_code, 403)

    def test_crear_vacante_inicia_pendiente(self):
        r = self.client.post(reverse('empresas:crear_vacante'), self.datos)
        self.assertRedirects(r, reverse('empresas:panel'))
        v = Vacante.objects.get(titulo='Becario de TI')
        self.assertEqual(v.estado, 'pendiente')
        self.assertEqual(v.empresa.nombre, 'Tecnologías del Norte')

    def test_empresa_pendiente_no_puede_publicar(self):
        u = Usuario.objects.get(username='empresa_nueva')
        u.set_password(PWD); u.save()
        self.client.login(username='empresa_nueva', password=PWD)
        r = self.client.post(reverse('empresas:crear_vacante'), self.datos)
        self.assertRedirects(r, reverse('empresas:panel'))
        self.assertFalse(Vacante.objects.filter(titulo='Becario de TI').exists())

    def test_fecha_limite_pasada_rechazada(self):
        r = self.client.post(reverse('empresas:crear_vacante'), {**self.datos, 'fecha_limite': '2020-01-01'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'no puede estar en el pasado')

    def test_editar_vuelve_a_revision(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        self.assertEqual(v.estado, 'aprobada')
        self.client.post(reverse('empresas:editar_vacante', args=[v.pk]), {**self.datos, 'titulo': 'Desarrollador Web Junior'})
        v.refresh_from_db()
        self.assertEqual(v.estado, 'pendiente')

    def test_no_se_pueden_tocar_vacantes_de_otra_empresa(self):
        ajena = Vacante.objects.get(titulo='Técnico en Mantenimiento Industrial')
        self.assertEqual(self.client.get(reverse('empresas:editar_vacante', args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('empresas:cerrar_vacante', args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('empresas:candidatos', args=[ajena.pk])).status_code, 404)

    def test_cerrar_vacante(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        self.client.post(reverse('empresas:cerrar_vacante', args=[v.pk]))
        v.refresh_from_db()
        self.assertEqual(v.estado, 'cerrada')
        self.assertFalse(Vacante.objects.abiertas().filter(pk=v.pk).exists())

    def test_candidatos_y_cambio_de_estado(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        p = Postulacion.objects.get(vacante=v)
        self.assertContains(self.client.get(reverse('empresas:candidatos', args=[v.pk])), 'Ana Martínez')
        url = reverse('empresas:cambiar_estado', args=[p.pk])
        for estado in ('en_revision', 'entrevista', 'aceptada', 'rechazada'):
            self.client.post(url, {'estado': estado})
            p.refresh_from_db()
            self.assertEqual(p.estado, estado)
        self.client.post(url, {'estado': 'inventado'})
        p.refresh_from_db()
        self.assertEqual(p.estado, 'rechazada')              # estado inválido ignorado

    def test_no_se_cambia_estado_de_postulacion_ajena(self):
        otra = Vacante.objects.get(titulo='Técnico en Mantenimiento Industrial')
        perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        p = Postulacion.objects.create(estudiante=perfil, vacante=otra)
        r = self.client.post(reverse('empresas:cambiar_estado', args=[p.pk]), {'estado': 'aceptada'})
        self.assertEqual(r.status_code, 404)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'enviada')

    def test_cambiar_estado_requiere_post(self):
        p = Postulacion.objects.first()
        self.assertEqual(self.client.get(reverse('empresas:cambiar_estado', args=[p.pk])).status_code, 405)
