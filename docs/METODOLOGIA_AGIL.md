# Metodología ágil: Scrum ligero con tablero Kanban

## Marco de trabajo

- **Backlog del producto**: historias de usuario (una *issue* de GitHub por historia).
- **Sprints**: cinco iteraciones, cada una con un objetivo y una rama `feature/*`, `fix/*` o `test/*`.
- **Tablero**: GitHub Projects con las columnas *Por hacer → En progreso → En revisión → Hecho*.
- **Flujo**: issue → rama → commits pequeños → pull request con `Closes #n` → revisión y fusión → la issue se cierra sola.
- **Definición de terminado**: pruebas pasando, pull request revisado, documentación actualizada y funcionando en el sitio publicado.

## Backlog por sprint

| Sprint | Objetivo | Historia de usuario | Rama |
|---|---|---|---|
| 1 | Datos que no se pierden | HU-01 Como estudiante quiero que mi perfil y mi CV se conserven tras un reinicio del servidor | `fix/persistencia-cv-perfil` |
| 1 | | HU-02 Como estudiante quiero que mi PDF no se rechace por detalles técnicos del archivo | |
| 2 | Cuentas protegidas | HU-03 Como administrador quiero que una cuenta se bloquee tras varios intentos fallidos | `feature/seguridad` |
| 2 | | HU-04 Como usuario quiero contraseñas y sesiones seguras | |
| 2 | | HU-05 Como administrador quiero que el navegador rechace scripts no autorizados | |
| 3 | Servicios de terceros | HU-06 Como administrador quiero que un robot no pueda registrarse (reCAPTCHA) | `feature/servicios-terceros` |
| 3 | | HU-07 Como estudiante quiero ver en un mapa dónde está la vacante | |
| 3 | | HU-08 Como estudiante quiero un correo cuando cambie el estado de mi postulación | |
| 4 | Servicios propios | HU-09 Como sistema externo quiero consultar vacantes por una API | `feature/api-rest` |
| 4 | | HU-10 Como estudiante quiero postularme y ver mis postulaciones por API con un token | |
| 4 | | HU-11 Como administrador quiero consultar estadísticas por API | |
| 4 | | HU-12 Como desarrollador quiero documentación interactiva de la API | |
| 5 | Calidad | HU-13 Como equipo queremos pruebas automáticas y medir la cobertura | `test/esquema-de-pruebas-y-documentacion` |
| 5 | | HU-14 Como equipo queremos ejecutar las pruebas en cada pull request | |

## Criterios de aceptación (ejemplos)

- **HU-03**: al quinto intento fallido en 15 minutos aparece el mensaje de bloqueo, incluso con la contraseña correcta; el intento queda en la bitácora del administrador; un acceso correcto reinicia el contador.
- **HU-10**: sin token la API responde 401; una cuenta de empresa recibe 403; sin CV la postulación responde 400; repetir la postulación no crea un duplicado.

## Cómo preparar el tablero en GitHub

1. En el repositorio: *Projects → New project → Board*, con las cuatro columnas.
2. *Issues → New issue* para cada historia (título y criterios de aceptación). Etiquetas sugeridas: `seguridad`, `servicio-tercero`, `api`, `pruebas`, `bug`.
3. Al abrir cada pull request, escribe `Closes #n` en la descripción.
