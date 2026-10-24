# Conecta UTC

Bolsa de trabajo universitaria para estudiantes y egresados de la **Universidad Tecnológica de Coahuila (UTC)**, desarrollada con Django.

## Problemática

Las vacantes dirigidas a los estudiantes se comparten principalmente por correo institucional, donde se pierden entre otros mensajes, no se pueden buscar ni filtrar, no se sabe cuáles siguen disponibles y no hay seguimiento de las postulaciones.

## Solución

Una plataforma web donde los **estudiantes** consultan, buscan, filtran, guardan y se postulan a vacantes; las **empresas** publican y administran ofertas y candidatos; y el **administrador UTC** revisa empresas y vacantes y consulta estadísticas.

## Funcionalidades

| Rol | Puede |
|---|---|
| Estudiante | Registrarse, iniciar/cerrar sesión, editar perfil (carrera, cuatrimestre, habilidades, experiencia), subir CV en PDF, buscar y filtrar vacantes, ver detalle, guardar favoritas, postularse y consultar el estado (Enviada, En revisión, Entrevista, Aceptada, Rechazada) |
| Empresa | Tener perfil empresarial, publicar, editar y cerrar vacantes, ver candidatos y cambiar el estado de cada postulación |
| Administrador UTC | Aprobar o rechazar empresas y vacantes, administrar estudiantes, empresas, vacantes y postulaciones (panel de Django) y consultar estadísticas generales |

Filtros de vacantes: palabra clave, carrera, empresa, modalidad, ubicación, tipo de empleo, experiencia y fecha de publicación.

## Estructura de aplicaciones

| App | Responsabilidad | Modelos |
|---|---|---|
| `config` | Configuración del proyecto | — |
| `core` | Inicio, estadísticas y datos de demostración | — |
| `cuentas` | Autenticación y roles | `Usuario` |
| `catalogo` | Datos de referencia | `Carrera`, `Habilidad` |
| `estudiantes` | Perfil, CV y descarga protegida | `PerfilEstudiante` |
| `empresas` | Perfil y panel de empresa | `Empresa` |
| `vacantes` | Listado, filtros, detalle y favoritos | `Vacante`, `Favorito` |
| `postulaciones` | Postulaciones y estados | `Postulacion` |

Relaciones: `Usuario` 1:1 `PerfilEstudiante` y 1:1 `Empresa`; `Empresa` 1:N `Vacante`; `Vacante` N:M `Habilidad` y N:M `Carrera`; `PerfilEstudiante` N:M `Habilidad`; `Favorito` y `Postulacion` unen estudiante y vacante con restricción de unicidad.

## Seguridad

- Contraseñas con hash de Django y validación de contraseñas débiles.
- Protección CSRF en todos los formularios; acciones que modifican datos solo por POST.
- Autorización por rol (`rol_requerido`) y comprobación de propiedad (una empresa solo gestiona sus vacantes y candidatos).
- El registro público no permite crear administradores.
- Toda vacante nueva o editada pasa por aprobación de la UTC; las empresas también.
- CV: validación de extensión, tamaño (5 MB) y firma real del PDF; nombre aleatorio; se descarga solo mediante una vista con permisos (dueño, administrador o empresa a la que se postuló).
- Secretos por variables de entorno; `.env` y la base de datos están en `.gitignore`.
- En producción: HTTPS forzado, cookies seguras y `SECRET_KEY` obligatoria.

## Ejecutar en local (Windows)

    python -m venv venv
    venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py poblar_demo --usuarios
    python manage.py runserver

Abre http://127.0.0.1:8000/. Cuentas demo (contraseña por defecto `ConectaUTC2026!`, o la de `--password` / `DEMO_PASSWORD`):

| Usuario | Rol |
|---|---|
| `estudiante_demo` | Estudiante |
| `empresa_demo` | Empresa (aprobada) |
| `admin_utc` | Administrador UTC (también entra a `/admin/`) |

`poblar_demo` es idempotente. Sin `--usuarios` solo carga carreras, habilidades, empresas y vacantes. Cambia o elimina las cuentas demo antes de usar datos reales.

Para crear tu propio administrador: `python manage.py createsuperuser`.

## Pruebas

    python manage.py test

## Despliegue en Render

| Parámetro | Valor |
|---|---|
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py poblar_demo --usuarios` |
| Start Command | `gunicorn config.wsgi:application` |
| `SECRET_KEY` | cadena aleatoria larga |
| `DEBUG` | `False` |
| `DEMO_PASSWORD` | contraseña de las cuentas demo |

Render define `RENDER_EXTERNAL_HOSTNAME`, que `settings.py` agrega a `ALLOWED_HOSTS` y a `CSRF_TRUSTED_ORIGINS`. El disco del plan gratuito es efímero: la base SQLite y los CV subidos se pierden al reiniciar, por eso el build vuelve a migrar y poblar los datos.

## Flujo de trabajo (GitHub Flow)

Rama `main` estable y ramas `feature/*` integradas mediante pull requests. Mensajes de commit con Conventional Commits (`feat:`, `fix:`, `docs:`, `style:`, `test:`, `chore:`).
