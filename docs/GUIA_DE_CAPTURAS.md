# Guía de capturas para el documento PDF

En PowerShell usa `curl.exe` (no `curl`, que es un alias de otro comando). Sustituye `SITIO` por la URL del sitio.

## Mecanismos de seguridad

| # | Mecanismo | Cómo demostrarlo |
|---|---|---|
| 1 | Contraseñas con hash | `/admin/` → Usuarios → abrir un usuario: el campo contraseña muestra `pbkdf2_sha256$…` |
| 2 | Contraseñas fuertes | En `/cuentas/registro/` escribe una contraseña de 9 caracteres: aparece el error |
| 3 | Bloqueo por intentos fallidos | Falla 5 veces el login: mensaje de bloqueo. Después `/admin/` → *Intentos de inicio de sesión fallidos* |
| 4 | reCAPTCHA | Login y registro mostrando el widget «No soy un robot» |
| 5 | Autorización por rol | Con sesión de estudiante abre `/empresa/panel/`: página 403 |
| 6 | Protección CSRF | `curl.exe -i -X POST SITIO/cuentas/login/ -d "username=a&password=b"` → 403 *CSRF verification failed* |
| 7 | CSP | F12 → Network → documento principal → cabecera `Content-Security-Policy`. En Console pega `document.body.appendChild(Object.assign(document.createElement('script'),{textContent:'alert(1)'}))`: el navegador responde *Refused to execute inline script* |
| 8 | Validación de archivos | En editar perfil sube un `.exe` o un texto renombrado a `.pdf`: error de validación |
| 9 | Acceso protegido al CV | Con la sesión de otra empresa abre la URL `/estudiante/cv/N/`: 403 |
| 10 | HTTPS y cookies seguras | Candado del navegador; F12 → Application → Cookies: `HttpOnly` y `Secure` |
| 11 | Secretos fuera del repositorio | Captura de `.env.example` en GitHub y de las variables de entorno del hosting (ocultando los valores) |

## Servicios web de terceros

| Servicio | Evidencia |
|---|---|
| Google reCAPTCHA | Widget en login/registro y registro exitoso tras resolverlo |
| OpenStreetMap / Nominatim / Leaflet | Detalle de una vacante con el mapa; crear una vacante con ubicación nueva y mostrar que obtiene coordenadas |
| Resend | Correo recibido al cambiar el estado de una postulación y el panel *Emails* de Resend |
| PostgreSQL (Neon/Supabase) | Panel del proveedor con las tablas; datos que sobreviven a un reinicio |

## Servicios web propios (API)

| Evidencia | Cómo |
|---|---|
| Documentación | `SITIO/api/v1/docs/` completa |
| Consulta pública | En Swagger: `GET /vacantes/` → *Try it out* → *Execute* (con y sin filtros) |
| Token | `POST /token/` con usuario y contraseña; copia el token |
| Autorización | Botón *Authorize*: escribe `Token tu-token` |
| Ruta protegida | `GET /mis-postulaciones/` con token (200) y sin token (401) |
| Roles | Con token de estudiante `GET /estadisticas/` → 403; con token de admin → 200 |
| Postularse | `POST /vacantes/{id}/postular/` → 201 y luego 200 |
| Desde la terminal | `curl.exe SITIO/api/v1/vacantes/?modalidad=hibrida` |

## Metodología ágil y repositorio

Tablero de GitHub Projects, lista de issues, un pull request fusionado (con `Closes #n`), pestaña *Actions* con las pruebas en verde, *Insights → Network* (ramas) y la lista de commits.
