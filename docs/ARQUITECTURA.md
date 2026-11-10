# Arquitectura de Conecta UTC

## Estilo arquitectónico

Aplicación web monolítica **modular**, con el patrón **MVT** (Modelo-Vista-Plantilla) de Django, organizada en capas:

| Capa | Responsabilidad | Dónde está |
|---|---|---|
| Presentación | Plantillas HTML (Bootstrap 5), JavaScript y CSS | `templates/`, `static/` |
| Interfaz web y API | Vistas, formularios, serializadores, permisos | `*/views.py`, `*/forms.py`, `api/` |
| Lógica de negocio | Reglas de postulación, aprobación, bloqueo | `postulaciones/servicios.py`, `cuentas/seguridad.py`, modelos |
| Integración | Adaptadores de servicios externos | `servicios/` |
| Datos | Modelos y migraciones (SQLite en local, PostgreSQL en producción) | `*/models.py`, `*/migrations/` |

Cada aplicación de Django agrupa un módulo del negocio (`cuentas`, `catalogo`, `estudiantes`, `empresas`, `vacantes`, `postulaciones`) y la API vive en `api/`. Las dependencias van en una sola dirección: `catalogo` → `cuentas` → `estudiantes`/`empresas` → `vacantes` → `postulaciones` → `api`/`core`.

## Patrones de diseño aplicados

| Patrón | Para qué se usa | Dónde |
|---|---|---|
| MVT (variante de MVC) | Separar datos, lógica y presentación | Todo el proyecto |
| Decorator | Exigir sesión y rol antes de ejecutar una vista | `cuentas/decorators.py` (`rol_requerido`) |
| Repository / Manager | Centralizar la consulta «vacantes públicas» | `vacantes/models.py` (`VacanteQuerySet.abiertas`) |
| Adapter | Ocultar URLs, claves y formatos de cada servicio externo | `servicios/recaptcha.py`, `geocodificacion.py`, `correo.py` |
| Observer | Reaccionar a eventos sin acoplar el código (correos, bitácora) | `postulaciones/signals.py`, `cuentas/signals.py` |
| Service Layer | Una sola implementación de las reglas, usada por la web y la API | `postulaciones/servicios.py` |
| Mixin | Reutilizar comportamiento en formularios (estilos, captcha) | `cuentas/forms.py` (`BootstrapMixin`, `CaptchaMixin`) |
| Command | Tareas administrativas ejecutables | `poblar_demo`, `geocodificar_vacantes` |

## Frameworks y librerías

Django 6.1 (aplicación), Django REST Framework (API), drf-spectacular (OpenAPI/Swagger), Bootstrap 5 y Leaflet (interfaz), WhiteNoise y gunicorn (servidor), psycopg y dj-database-url (PostgreSQL), requests (servicios externos).

## Decisiones de diseño relevantes

- **CV en la base de datos (`ArchivoCV`)**: los servicios gratuitos de hosting tienen disco efímero, por lo que un archivo en disco se pierde al reiniciar. Se guarda en un modelo aparte para no cargar archivos pesados en cada consulta del perfil. Para un volumen grande convendría un almacenamiento de objetos (S3, Cloudinary).
- **Bloqueo por usuario y no por IP**: frena ataques distribuidos; la contrapartida es que alguien podría bloquear a propósito una cuenta ajena unos minutos.
- **reCAPTCHA «falla cerrado»**: si Google no responde, la solicitud se rechaza.
- **La API solo acepta token**: no usa sesiones, por lo que no está expuesta a CSRF.
- **Los servicios externos nunca rompen la aplicación**: timeouts de 5 s, errores capturados y funcionamiento sin claves configuradas.

## Esquema de pruebas

| Tipo | Qué verifica | Ejemplos |
|---|---|---|
| Unitarias | Validadores, modelos, adaptadores (con `unittest.mock`) | `estudiantes/tests.py`, `servicios/tests*.py` |
| Integración | Flujos completos con el cliente de pruebas de Django | `vacantes/tests.py`, `empresas/tests.py` |
| Seguridad | Bloqueo, CSP, permisos por rol, CSRF, sesiones | `cuentas/tests_seguridad.py`, `core/tests_seguridad.py` |
| API | Autenticación, permisos, filtros, límites, esquema OpenAPI | `api/tests.py` |

Los servicios externos se simulan: las pruebas nunca llaman a Google, OpenStreetMap ni Resend. Ejecución: `python manage.py test`. Cobertura: `coverage run manage.py test && coverage report`. GitHub Actions ejecuta ambas en cada pull request y exige al menos 90 % de cobertura.
