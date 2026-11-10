from django.core.management import call_command
from django.test import TestCase

from estudiantes.models import PerfilEstudiante
from vacantes.models import Vacante

from .servicios import PostulacionNoPermitida, postular


class ServicioDePostulacionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)

    def setUp(self):
        self.perfil = PerfilEstudiante.objects.get(usuario__username='estudiante_demo')
        self.vacante = Vacante.objects.get(titulo='Auxiliar Contable')

    def test_sin_cv_no_se_puede_postular(self):
        with self.assertRaisesMessage(PostulacionNoPermitida, 'sube tu CV'):
            postular(self.perfil, self.vacante)

    def test_perfil_incompleto_no_puede_postular(self):
        self.perfil.guardar_cv('cv.pdf', b'%PDF-1.4')
        self.perfil.carrera = None
        with self.assertRaises(PostulacionNoPermitida):
            postular(self.perfil, self.vacante)

    def test_vacante_cerrada_no_recibe_postulaciones(self):
        self.perfil.guardar_cv('cv.pdf', b'%PDF-1.4')
        cerrada = Vacante.objects.get(titulo='Operador de Producción (vacante cerrada)')
        with self.assertRaisesMessage(PostulacionNoPermitida, 'ya no recibe'):
            postular(self.perfil, cerrada)

    def test_postulacion_correcta_y_sin_duplicados(self):
        self.perfil.guardar_cv('cv.pdf', b'%PDF-1.4')
        _, creada = postular(self.perfil, self.vacante)
        _, otra_vez = postular(self.perfil, self.vacante)
        self.assertTrue(creada)
        self.assertFalse(otra_vez)
