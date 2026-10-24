import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalogo.models import Carrera, Habilidad
from cuentas.models import Usuario
from empresas.models import Empresa
from estudiantes.models import PerfilEstudiante
from postulaciones.models import Postulacion
from vacantes.models import Favorito, Vacante

CARRERAS = [
    'TSU en Desarrollo de Software Multiplataforma', 'Ingeniería en Desarrollo y Gestión de Software',
    'TSU en Mecatrónica', 'Ingeniería en Mecatrónica', 'TSU en Procesos Industriales',
    'TSU en Mantenimiento Industrial', 'TSU en Administración', 'TSU en Contaduría',
    'TSU en Energías Renovables', 'TSU en Mecánica Automotriz',
]
HABILIDADES = [
    'Python', 'Django', 'JavaScript', 'HTML y CSS', 'SQL', 'Git', 'Java', 'Redes', 'Soporte técnico',
    'AutoCAD', 'PLC', 'Electrónica', 'Mantenimiento preventivo', 'Excel avanzado', 'Contabilidad',
    'Atención al cliente', 'Comunicación', 'Trabajo en equipo', 'Inglés intermedio', 'Seguridad e higiene',
    'Control de calidad', 'Lean manufacturing', 'Facturación electrónica', 'Diseño UX',
]
EMPRESAS = [
    ('empresa_demo', 'Tecnologías del Norte', 'Tecnología', 'Saltillo', 'Desarrollo de software y soporte para la industria regional.', 'aprobada'),
    ('empresa_autopartes', 'AutoPartes Saltillo', 'Automotriz', 'Ramos Arizpe', 'Manufactura de componentes automotrices para exportación.', 'aprobada'),
    ('empresa_logistica', 'Logística Coahuila', 'Logística', 'Saltillo', 'Transporte y almacenamiento para cadenas de suministro.', 'aprobada'),
    ('empresa_contable', 'Despacho Contable Vega', 'Servicios profesionales', 'Saltillo', 'Asesoría contable, fiscal y administrativa para pymes.', 'aprobada'),
    ('empresa_nueva', 'Soluciones Industriales del Desierto', 'Manufactura', 'Arteaga', 'Empresa nueva pendiente de revisión.', 'pendiente'),
]
# (empresa, puesto, tipo, modalidad, ubicación, horario, salario, experiencia, carreras, habilidades,
#  días desde publicación, días hasta el límite, destacada, estado, descripción)
VACANTES = [
    (0, 'Desarrollador Web Junior', 'tiempo_completo', 'hibrida', 'Saltillo, Coahuila', 'Lun-Vie 9:00-18:00', '$14,000 mensuales', 'menos_1', [0, 1], ['Python', 'Django', 'Git', 'HTML y CSS'], 2, 25, True, 'aprobada', 'Desarrollarás y mantendrás aplicaciones web internas con Django junto a un equipo ágil.'),
    (0, 'Prácticas en Soporte Técnico', 'practicas', 'presencial', 'Saltillo, Coahuila', 'Lun-Vie 9:00-14:00', 'Beca de $4,000', 'ninguna', [0, 1], ['Soporte técnico', 'Redes', 'Comunicación'], 5, 30, False, 'aprobada', 'Apoyo en mesa de ayuda, instalación de equipos y atención a usuarios.'),
    (0, 'Estadía en Desarrollo de Aplicaciones', 'estadia', 'hibrida', 'Saltillo, Coahuila', 'Lun-Vie 9:00-17:00', 'Beca de $5,000', 'ninguna', [0, 1], ['Python', 'SQL', 'JavaScript'], 8, 40, True, 'aprobada', 'Proyecto de estadía profesional con asesoría de un desarrollador sénior.'),
    (1, 'Técnico en Mantenimiento Industrial', 'tiempo_completo', 'presencial', 'Ramos Arizpe, Coahuila', 'Turnos rotativos', '$13,500 mensuales', 'uno_dos', [5, 2], ['Mantenimiento preventivo', 'PLC', 'Seguridad e higiene'], 3, 20, False, 'aprobada', 'Mantenimiento preventivo y correctivo de líneas de producción automatizadas.'),
    (1, 'Auxiliar de Control de Calidad', 'medio_tiempo', 'presencial', 'Ramos Arizpe, Coahuila', 'Lun-Vie 14:00-20:00', '$8,000 mensuales', 'ninguna', [4, 5], ['Control de calidad', 'Excel avanzado', 'Trabajo en equipo'], 10, 18, False, 'aprobada', 'Inspección de piezas, registro de mediciones y apoyo en auditorías internas.'),
    (1, 'Ingeniero de Automatización', 'egresados', 'presencial', 'Ramos Arizpe, Coahuila', 'Lun-Vie 8:00-17:00', '$22,000 mensuales', 'uno_dos', [3, 2], ['PLC', 'Electrónica', 'AutoCAD'], 1, 35, True, 'aprobada', 'Programación de PLC y mejora continua de celdas robotizadas.'),
    (2, 'Auxiliar Administrativo de Logística', 'tiempo_completo', 'presencial', 'Saltillo, Coahuila', 'Lun-Vie 8:00-17:00', '$11,000 mensuales', 'ninguna', [6, 4], ['Excel avanzado', 'Atención al cliente', 'Comunicación'], 6, 22, False, 'aprobada', 'Seguimiento de embarques, captura de documentos y atención a clientes.'),
    (2, 'Prácticas en Análisis de Datos', 'practicas', 'remota', 'Remoto (México)', 'Flexible, 20 h semanales', 'Beca de $3,500', 'ninguna', [0, 1, 6], ['SQL', 'Excel avanzado', 'Python'], 12, 28, False, 'aprobada', 'Construcción de reportes de indicadores logísticos con apoyo de un analista.'),
    (3, 'Auxiliar Contable', 'tiempo_completo', 'presencial', 'Saltillo, Coahuila', 'Lun-Vie 9:00-18:00', '$10,500 mensuales', 'menos_1', [7, 6], ['Contabilidad', 'Facturación electrónica', 'Excel avanzado'], 4, 15, False, 'aprobada', 'Registro contable, conciliaciones bancarias y facturación electrónica.'),
    (3, 'Estadía en Administración Fiscal', 'estadia', 'hibrida', 'Saltillo, Coahuila', 'Lun-Vie 9:00-15:00', 'Beca de $4,500', 'ninguna', [7, 6], ['Contabilidad', 'Comunicación', 'Inglés intermedio'], 15, 45, False, 'aprobada', 'Apoyo en declaraciones y asesoría fiscal para clientes pyme.'),
    (0, 'Diseñador UX/UI (medio tiempo)', 'medio_tiempo', 'remota', 'Remoto (México)', 'Flexible', '$9,000 mensuales', 'menos_1', [0, 1], ['Diseño UX', 'HTML y CSS', 'Trabajo en equipo'], 0, 30, False, 'pendiente', 'Diseño de interfaces para productos internos. Pendiente de aprobación.'),
    (1, 'Operador de Producción (vacante cerrada)', 'tiempo_completo', 'presencial', 'Ramos Arizpe, Coahuila', 'Turnos rotativos', '$10,000 mensuales', 'ninguna', [4], ['Seguridad e higiene'], 40, 5, False, 'cerrada', 'Vacante ocupada; se conserva para consulta del historial.'),
]


class Command(BaseCommand):
    help = 'Carga carreras, habilidades, empresas y vacantes de demostración (idempotente).'

    def add_arguments(self, parser):
        parser.add_argument('--usuarios', action='store_true',
                            help='Crea cuentas de acceso demo: estudiante_demo, empresa_demo y admin_utc.')
        parser.add_argument('--password', default=os.environ.get('DEMO_PASSWORD', 'ConectaUTC2026!'),
                            help='Contraseña de las cuentas demo (o variable DEMO_PASSWORD).')

    def handle(self, *args, **opts):
        carreras = [Carrera.objects.get_or_create(nombre=n)[0] for n in CARRERAS]
        habilidades = {n: Habilidad.objects.get_or_create(nombre=n)[0] for n in HABILIDADES}

        empresas = []
        for username, nombre, sector, ciudad, descripcion, estado in EMPRESAS:
            usuario, creado = Usuario.objects.get_or_create(
                username=username, defaults={'rol': Usuario.Rol.EMPRESA, 'email': f'{username}@ejemplo.com'})
            if creado:
                usuario.set_unusable_password()    # sin acceso, salvo que se pida --usuarios
                usuario.save()
            empresa, _ = Empresa.objects.update_or_create(usuario=usuario, defaults={
                'nombre': nombre, 'sector': sector, 'ciudad': ciudad, 'descripcion': descripcion, 'estado': estado})
            empresas.append(empresa)

        ahora = timezone.now()
        hoy = timezone.localdate()
        for (e, puesto, tipo, modalidad, ubicacion, horario, salario, exp, cars, habs,
             dias_pub, dias_lim, destacada, estado, desc) in VACANTES:
            vacante, _ = Vacante.objects.update_or_create(
                empresa=empresas[e], titulo=puesto, defaults={
                    'descripcion': desc, 'tipo': tipo, 'modalidad': modalidad, 'ubicacion': ubicacion,
                    'horario': horario, 'salario': salario, 'experiencia': exp, 'destacada': destacada,
                    'estado': estado, 'fecha_publicacion': ahora - timedelta(days=dias_pub),
                    'fecha_limite': hoy + timedelta(days=dias_lim),
                    'requisitos': '• Estudiante o egresado de la carrera indicada.\n'
                                  f'• Conocimientos en: {", ".join(habs)}.\n• Disponibilidad para el horario señalado.'})
            vacante.carreras.set([carreras[i] for i in cars])
            vacante.habilidades.set([habilidades[h] for h in habs])
        self.stdout.write(f'Catálogo: {len(carreras)} carreras, {len(habilidades)} habilidades; '
                          f'{len(empresas)} empresas, {len(VACANTES)} vacantes.')

        if opts['usuarios']:
            self._crear_usuarios(opts['password'], carreras, habilidades, empresas)

    def _crear_usuarios(self, password, carreras, habilidades, empresas):
        demo = empresas[0].usuario
        demo.set_password(password)
        demo.save()

        est, _ = Usuario.objects.get_or_create(
            username='estudiante_demo', defaults={'rol': Usuario.Rol.ESTUDIANTE, 'email': 'estudiante_demo@ejemplo.com'})
        est.set_password(password)
        est.save()
        perfil = PerfilEstudiante.para(est)
        perfil.nombre_completo = 'Ana Martínez (demo)'
        perfil.carrera = carreras[1]
        perfil.cuatrimestre = 9
        perfil.telefono = '844 000 0000'
        perfil.experiencia = 'Proyecto escolar de bolsa de trabajo en Django. Prácticas en soporte técnico.'
        perfil.save()
        perfil.habilidades.set([habilidades[h] for h in ('Python', 'Django', 'Git', 'SQL', 'HTML y CSS')])

        adm, _ = Usuario.objects.get_or_create(
            username='admin_utc', defaults={'email': 'admin_utc@ejemplo.com', 'is_staff': True, 'is_superuser': True})
        adm.is_staff = adm.is_superuser = True
        adm.set_password(password)
        adm.save()

        abiertas = list(Vacante.objects.abiertas()[:3])
        for v in abiertas[:2]:
            Postulacion.objects.get_or_create(estudiante=perfil, vacante=v)
        if abiertas:
            Favorito.objects.get_or_create(estudiante=perfil, vacante=abiertas[-1])
        self.stdout.write(self.style.WARNING(
            'Cuentas demo creadas (estudiante_demo, empresa_demo, admin_utc). Cambia o elimina estas '
            'contraseñas antes de usar el sistema con datos reales.'))
