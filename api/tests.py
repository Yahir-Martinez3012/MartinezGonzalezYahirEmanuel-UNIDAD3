from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Carrera
from vacantes.models import Vacante


class ApiBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('poblar_demo', '--usuarios', verbosity=0)

    def setUp(self):
        cache.clear()                    # reinicia los contadores de límite de peticiones


class ApiPublicaTests(ApiBase):
    def test_lista_solo_vacantes_publicadas_y_paginada(self):
        r = self.client.get(reverse('api:vacantes'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()), {'count', 'next', 'previous', 'results'})
        self.assertEqual(r.json()['count'], 10)
        titulos = [v['titulo'] for v in r.json()['results']]
        self.assertNotIn('Diseñador UX/UI (medio tiempo)', titulos)                  # pendiente
        self.assertNotIn('Operador de Producción (vacante cerrada)', titulos)        # cerrada
        self.assertEqual(len(titulos), 10)

    def test_tamano_de_pagina_y_segunda_pagina(self):
        from api.views import ListaVacantes
        self.assertEqual(ListaVacantes.pagination_class.page_size, 10)
        r = self.client.get(reverse('api:vacantes'), {'page': 2})
        self.assertEqual(r.status_code, 404)                 # con 10 resultados solo existe la página 1

    def test_filtros_como_en_la_web(self):
        url = reverse('api:vacantes')
        self.assertTrue(all(v['modalidad'] == 'remota' for v in self.client.get(url, {'modalidad': 'remota'}).json()['results']))
        self.assertEqual(self.client.get(url, {'q': 'Django'}).json()['count'], 1)
        self.assertGreater(self.client.get(url, {'tipo': 'practicas'}).json()['count'], 0)
        carrera = Carrera.objects.get(nombre='TSU en Contaduría')
        self.assertGreater(self.client.get(url, {'carrera': carrera.pk}).json()['count'], 0)

    def test_filtro_invalido_responde_400_con_el_detalle(self):
        r = self.client.get(reverse('api:vacantes'), {'carrera': 'abc', 'modalidad': 'volando'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('carrera', r.json())
        self.assertIn('modalidad', r.json())

    def test_detalle_de_vacante_publicada(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        r = self.client.get(reverse('api:vacante', args=[v.pk]))
        datos = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(datos['titulo'], 'Desarrollador Web Junior')
        self.assertEqual(datos['empresa']['nombre'], 'Tecnologías del Norte')
        self.assertIn('Django', datos['habilidades'])
        self.assertAlmostEqual(datos['latitud'], 25.4232, places=4)

    def test_no_se_exponen_datos_privados_de_la_empresa(self):
        v = Vacante.objects.get(titulo='Desarrollador Web Junior')
        cuerpo = self.client.get(reverse('api:vacante', args=[v.pk])).content.decode()
        for privado in ('empresa_demo', '@ejemplo.com', 'password', 'estado'):
            self.assertNotIn(privado, cuerpo)

    def test_vacantes_no_publicadas_dan_404(self):
        for titulo in ('Diseñador UX/UI (medio tiempo)', 'Operador de Producción (vacante cerrada)'):
            v = Vacante.objects.get(titulo=titulo)
            self.assertEqual(self.client.get(reverse('api:vacante', args=[v.pk])).status_code, 404)

    def test_catalogos_publicos(self):
        self.assertEqual(len(self.client.get(reverse('api:carreras')).json()), 10)
        self.assertEqual(len(self.client.get(reverse('api:habilidades')).json()), 24)

    def test_la_api_solo_responde_json(self):
        navegador = 'text/html,application/xhtml+xml,*/*;q=0.8'          # lo que envía un navegador al abrir la URL
        r = self.client.get(reverse('api:vacantes'), HTTP_ACCEPT=navegador)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/json')
        self.assertEqual(self.client.get(reverse('api:vacantes'), HTTP_ACCEPT='text/html').status_code, 406)

    def test_solo_lectura_en_los_recursos_publicos(self):
        for nombre in ('api:vacantes', 'api:carreras', 'api:habilidades'):
            self.assertEqual(self.client.post(reverse(nombre), {}).status_code, 405)       # solo se permite GET


PWD = 'ConectaUTC2026!'


class TokenTests(ApiBase):
    def pedir(self, usuario='estudiante_demo', clave=PWD):
        return self.client.post(reverse('api:token'), {'username': usuario, 'password': clave})

    def test_credenciales_correctas_entregan_un_token(self):
        r = self.pedir()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['token']), 40)

    def test_credenciales_incorrectas(self):
        r = self.pedir(clave='mala')
        self.assertEqual(r.status_code, 400)
        self.assertNotIn('token', r.json())

    def test_el_token_se_bloquea_con_el_mismo_mecanismo_que_el_login_web(self):
        for _ in range(5):
            self.pedir(clave='mala')
        r = self.pedir()                                           # ya con la clave correcta
        self.assertEqual(r.status_code, 429)
        self.assertIn('Demasiados intentos', r.json()['detail'])
        r = self.client.post(reverse('cuentas:login'), {'username': 'estudiante_demo', 'password': PWD})
        self.assertContains(r, 'Demasiados intentos fallidos')     # el bloqueo también vale en la web

    def test_token_correcto_reinicia_el_contador(self):
        for _ in range(3):
            self.pedir(clave='mala')
        self.pedir()
        from cuentas.models import IntentoLogin
        self.assertEqual(IntentoLogin.objects.filter(usuario='estudiante_demo').count(), 0)

    def test_limite_de_peticiones_por_minuto(self):
        from unittest.mock import patch
        from rest_framework.throttling import ScopedRateThrottle
        with patch.object(ScopedRateThrottle, 'THROTTLE_RATES', {'token': '3/min'}):
            codigos = [self.pedir().status_code for _ in range(5)]
        self.assertEqual(codigos, [200, 200, 200, 429, 429])

    def test_el_token_solo_acepta_post(self):
        self.assertEqual(self.client.get(reverse('api:token')).status_code, 405)


class AutorizacionDeLaApiTests(ApiBase):
    def cabecera(self, usuario):
        token = self.client.post(reverse('api:token'), {'username': usuario, 'password': PWD}).json()['token']
        return {'HTTP_AUTHORIZATION': f'Token {token}'}

    def test_sin_token_los_recursos_protegidos_responden_401(self):
        self.assertEqual(self.client.get(reverse('api:mis_postulaciones')).status_code, 401)
        self.assertEqual(self.client.get(reverse('api:estadisticas')).status_code, 401)
        self.assertEqual(self.client.post(reverse('api:postular', args=[1])).status_code, 401)

    def test_token_falso_responde_401(self):
        r = self.client.get(reverse('api:mis_postulaciones'), HTTP_AUTHORIZATION='Token ' + '0' * 40)
        self.assertEqual(r.status_code, 401)

    def test_las_sesiones_del_navegador_no_sirven_para_la_api(self):
        self.client.login(username='estudiante_demo', password=PWD)
        self.assertEqual(self.client.get(reverse('api:mis_postulaciones')).status_code, 401)

    def test_mis_postulaciones_solo_muestra_las_propias(self):
        r = self.client.get(reverse('api:mis_postulaciones'), **self.cabecera('estudiante_demo'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 2)
        self.assertEqual(r.json()['results'][0]['estado'], 'enviada')
        self.assertIn('empresa', r.json()['results'][0]['vacante'])

    def test_la_empresa_no_puede_usar_recursos_de_estudiante(self):
        h = self.cabecera('empresa_demo')
        self.assertEqual(self.client.get(reverse('api:mis_postulaciones'), **h).status_code, 403)
        self.assertEqual(self.client.post(reverse('api:postular', args=[1]), **h).status_code, 403)

    def test_estadisticas_solo_para_administradores(self):
        self.assertEqual(self.client.get(reverse('api:estadisticas'), **self.cabecera('estudiante_demo')).status_code, 403)
        self.assertEqual(self.client.get(reverse('api:estadisticas'), **self.cabecera('empresa_demo')).status_code, 403)
        r = self.client.get(reverse('api:estadisticas'), **self.cabecera('admin_utc'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['totales']['vacantes'], 12)
        self.assertEqual(r.json()['totales']['vacantes_publicadas'], 10)
        self.assertEqual(r.json()['vacantes_por_estado']['pendiente'], 1)


class PostularPorApiTests(ApiBase):
    def setUp(self):
        super().setUp()
        self.vacante = Vacante.objects.get(titulo='Auxiliar Contable')
        self.url = reverse('api:postular', args=[self.vacante.pk])
        token = self.client.post(reverse('api:token'), {'username': 'estudiante_demo', 'password': PWD}).json()['token']
        self.h = {'HTTP_AUTHORIZATION': f'Token {token}'}

    def con_cv(self):
        from estudiantes.models import PerfilEstudiante
        PerfilEstudiante.objects.get(usuario__username='estudiante_demo').guardar_cv('cv.pdf', b'%PDF-1.4')

    def test_sin_cv_responde_400(self):
        r = self.client.post(self.url, **self.h)
        self.assertEqual(r.status_code, 400)
        self.assertIn('CV', r.json()['detail'])

    def test_postulacion_creada_y_repetida(self):
        self.con_cv()
        r = self.client.post(self.url, **self.h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['vacante']['titulo'], 'Auxiliar Contable')
        self.assertEqual(r.json()['estado'], 'enviada')
        self.assertEqual(self.client.post(self.url, **self.h).status_code, 200)      # ya existía: no se duplica

    def test_vacante_cerrada_o_inexistente_da_404(self):
        self.con_cv()
        cerrada = Vacante.objects.get(titulo='Operador de Producción (vacante cerrada)')
        self.assertEqual(self.client.post(reverse('api:postular', args=[cerrada.pk]), **self.h).status_code, 404)
        self.assertEqual(self.client.post(reverse('api:postular', args=[99999]), **self.h).status_code, 404)

    def test_la_postulacion_por_api_aparece_en_mis_postulaciones(self):
        self.con_cv()
        self.client.post(self.url, **self.h)
        r = self.client.get(reverse('api:mis_postulaciones'), **self.h)
        self.assertEqual(r.json()['count'], 3)

    def test_solo_se_acepta_post(self):
        self.assertEqual(self.client.get(self.url, **self.h).status_code, 405)


class DocumentacionTests(ApiBase):
    def test_el_esquema_openapi_describe_todos_los_servicios(self):
        r = self.client.get(reverse('api:schema'), {'format': 'json'})
        self.assertEqual(r.status_code, 200)
        rutas = r.json()['paths']
        for ruta in ('/api/v1/vacantes/', '/api/v1/vacantes/{id}/', '/api/v1/vacantes/{id}/postular/', '/api/v1/token/',
                     '/api/v1/mis-postulaciones/', '/api/v1/estadisticas/', '/api/v1/carreras/', '/api/v1/habilidades/'):
            self.assertIn(ruta, rutas)
        self.assertIn('tokenAuth', r.json()['components']['securitySchemes'])

    def test_swagger_ui_carga_y_su_javascript_no_esta_en_linea(self):
        r = self.client.get(reverse('api:docs'))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        import re
        for apertura in re.findall(r'<script\b[^>]*>', html):
            self.assertIn('src=', apertura)                         # ningún <script> en línea
        directivas = [d.strip() for d in r['Content-Security-Policy'].split(';')]
        scripts = [d for d in directivas if d.startswith('script-src ')][0]
        self.assertNotIn('unsafe-inline', scripts)                  # los scripts siguen estrictos

    def test_el_resto_del_sitio_conserva_la_politica_estricta(self):
        csp = self.client.get(reverse('inicio'))['Content-Security-Policy']
        estilos = [d for d in csp.split(';') if d.strip().startswith('style-src ')][0]
        self.assertNotIn('unsafe-inline', estilos)
