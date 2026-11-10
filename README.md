# Conecta UTC

Bolsa de trabajo universitaria para estudiantes y egresados de la **Universidad Tecnológica de Coahuila (UTC)**, desarrollada con Django.

## Problemática y solución

Las vacantes se compartían por correo institucional, donde se perdían, no se podían buscar ni se les daba seguimiento. Conecta UTC centraliza las vacantes: los **estudiantes** consultan, filtran, guardan y se postulan; las **empresas** publican y gestionan candidatos; y el **administrador UTC** revisa empresas y vacantes y consulta estadísticas.

## Funcionalidades

| Rol | Puede |
|---|---|
| Estudiante | Registrarse, editar su perfil, subir su CV en PDF, buscar y filtrar vacantes, ver el mapa de cada una, guardar favoritas, postularse, recibir correos y consultar el estado de sus postulaciones |
| Empresa | Tener perfil, publicar, editar y cerrar vacantes, ver candidatos y cambiar el estado de cada postulación |
| Administrador UTC | Aprobar o rechazar empresas y vacantes, administrar datos, ver estadísticas y la bitácora de intentos fallidos |

## Mecanismos de seguridad

| Mecanismo | Implementación |
|---|---|
| Autenticación y autorización | Usuario personalizado con roles; decorador `rol_requerido`; comprobación de propiedad de los datos |
| Contraseñas | Hash de Django; mínimo 10 caracteres; validación de contraseñas comunes |
| Fuerza bruta | Bloqueo de 15 min tras 5 intentos fallidos (web y API) y bitácora en el admin |
| reCAPTCHA | Registro e inicio de sesión (Google reCAPTCHA v2) |
| CSRF | Token en todos los formularios; la API usa solo token |
| CSP y encabezados | Política de seguridad de contenido estricta, `X-Frame-Options`, `nosniff`, `Referrer-Policy` |
| Sesiones y cookies | `HttpOnly`, `SameSite`, expiración a las 2 horas de inactividad; `Secure` y HTTPS forzado en producción |
| Archivos | Validación de extensión, tamaño y contenido del PDF; descarga solo con permisos |
| Secretos | Variables de entorno; `.env` fuera del repositorio |
| Límite de peticiones | 60/min anónimos, 120/min autenticados y 10/min para el token |

## Servicios web de terceros

| Servicio | Uso | Adaptador |
|---|---|---|
| Google reCAPTCHA | Distinguir personas de robots | `servicios/recaptcha.py` |
| OpenStreetMap (Nominatim y Leaflet) | Coordenadas y mapa de cada vacante | `servicios/geocodificacion.py`, `static/js/mapa.js` |
| Resend | Correos de cambio de estado | `servicios/correo.py` |
| PostgreSQL (Neon, Supabase o Render) | Base de datos persistente | `DATABASE_URL` |

## Servicios web propios (API REST)

Documentación interactiva en **`/api/v1/docs/`** y esquema OpenAPI en `/api/v1/schema/`.

| Método y ruta | Acceso | Descripción |
|---|---|---|
| `GET /api/v1/vacantes/` | Público | Listado paginado con filtros (`q`, `carrera`, `empresa`, `modalidad`, `ubicacion`, `tipo`, `experiencia`, `fecha`) |
| `GET /api/v1/vacantes/{id}/` | Público | Detalle de una vacante |
| `GET /api/v1/carreras/`, `/habilidades/` | Público | Catálogos |
| `POST /api/v1/token/` | Público | Obtiene un token con usuario y contraseña |
| `POST /api/v1/vacantes/{id}/postular/` | Estudiante | Postularse |
| `GET /api/v1/mis-postulaciones/` | Estudiante | Postulaciones propias |
| `GET /api/v1/estadisticas/` | Administrador | Totales por estado |

Ejemplo: `curl -H "Authorization: Token TU_TOKEN" http://127.0.0.1:8000/api/v1/mis-postulaciones/`

## Arquitectura, metodología y pruebas

Ver `docs/ARQUITECTURA.md` (capas y patrones), `docs/METODOLOGIA_AGIL.md` (backlog y sprints) y `docs/GUIA_DE_CAPTURAS.md`.

## Ejecutar en local (Windows)

    python -m venv venv
    venv\Scripts\Activate.ps1
    pip install -r requirements-dev.txt
    python manage.py migrate
    python manage.py poblar_demo --usuarios
    python manage.py runserver

Abre http://127.0.0.1:8000/. Cuentas demo (contraseña `ConectaUTC2026!` o la de `DEMO_PASSWORD`): `estudiante_demo`, `empresa_demo` y `admin_utc`.
`poblar_demo` no pisa los cambios ya hechos; usa `--restablecer` para volver a los valores de ejemplo.

## Pruebas

    python manage.py test
    coverage run manage.py test
    coverage report

140 pruebas, cobertura superior al 90 %. Los servicios externos se simulan.

## Variables de entorno

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Obligatoria con `DEBUG=False` |
| `DEBUG` | `False` en producción |
| `DATABASE_URL` | PostgreSQL (ej. `postgres://usuario:clave@host/db?sslmode=require`); sin ella se usa SQLite |
| `DEMO_PASSWORD` | Contraseña de las cuentas demo |
| `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY` | reCAPTCHA v2 (sin claves, el captcha se desactiva) |
| `RESEND_API_KEY`, `CORREO_REMITENTE` | Correos (sin clave, no se envían) |

## Despliegue en Render

| Parámetro | Valor |
|---|---|
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py poblar_demo --usuarios` |
| Start Command | `gunicorn config.wsgi:application` |

El disco de Render es efímero: por eso los datos viven en PostgreSQL y los CV en la base de datos.

## Flujo de trabajo

GitHub Flow: `main` estable y ramas `feature/*`, `fix/*` y `test/*` integradas con pull requests. Mensajes con Conventional Commits.
