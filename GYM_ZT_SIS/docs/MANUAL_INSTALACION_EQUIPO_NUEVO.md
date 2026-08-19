# Manual de instalación — GYM ZT SIS en un equipo nuevo

Documento detallado para **técnicos de instalación**, **soporte** y **administradores de TI**. Complementa `GUIA_USUARIO_FINAL.md` con especificaciones, rutas, variables y resolución de incidencias.

---

## 1. Alcance del producto

| Aspecto | Detalle |
|--------|---------|
| **Nombre** | GYM ZT SIS (aplicación de escritorio) |
| **Arquitectura** | Ventana **Electron** + servidor web local **Django 4.2** servido con **Waitress** en `127.0.0.1:8000` |
| **Base de datos** | **PostgreSQL** (local al equipo; no sustituye la instalación del servidor PostgreSQL) |
| **Modo de red** | Uso previsto **local/offline**; no requiere Internet para operación normal |
| **Instalador típico** | `GYM ZT SIS-Setup-x.x.x.exe` (NSIS, Windows x64) |

---

## 2. Requisitos del equipo

### 2.1 Hardware (orientativo)

| Recurso | Mínimo recomendado |
|--------|---------------------|
| **CPU** | x64, 2 núcleos |
| **RAM** | 4 GB (8 GB si PostgreSQL y otras apps pesadas comparten el mismo PC) |
| **Disco** | ~2 GB libres para app + PostgreSQL + datos iniciales (más espacio para crecimiento de BD y medios) |
| **Pantalla** | Resolución que permita ver formularios web cómodamente (p. ej. 1366×768 o superior) |

### 2.2 Sistema operativo

- **Microsoft Windows 10 o 11**, arquitectura **64 bits (x64)**.
- Cuenta de usuario con permiso para **instalar software** y **escribir** en el perfil (AppData).
- Hora y zona horarias correctas (el sistema usa `America/La_Paz` en configuración Django).

### 2.3 Software obligatorio en el equipo cliente

| Componente | Versión / notas |
|------------|-----------------|
| **PostgreSQL para Windows** | Versión acordada con la organización (compatible con **libpq** usada por `psycopg2-binary` en el proyecto). Instalación típica **64 bits**. |
| **Servicio PostgreSQL** | Debe estar en estado **En ejecución** y, recomendable, **Inicio automático**. |
| **Puerto PostgreSQL** | Por defecto **5432** (si se usa otro, debe reflejarse en `DB_PORT` del `.env`). |

### 2.4 Python en el equipo cliente (según el paquete que distribuya)

Hay **dos escenarios**:

| Escenario | ¿Instala Python el usuario? | Descripción |
|-----------|----------------------------|-------------|
| **A — Instalador con Python embebido** | **No** (recomendado para usuario final) | El build incluye `resources\python\python.exe` y las librerías ya instaladas en esa carpeta. El instalador se genera con `scripts\setup_embedded_python.ps1` antes de `npm run dist`. |
| **B — Instalador sin Python embebido** | **Sí** | Debe instalarse **Python 3.10 o 3.11 (64 bits)** y ejecutarse `pip install -r requirements.txt` contra el `requirements.txt` del **backend** incluido en la instalación (ruta típica bajo `C:\Users\...\AppData\Local\Programs\GYM ZT SIS\resources\backend\requirements.txt` o la carpeta elegida en el asistente). |

**Variable opcional:** si la app no encuentra Python, defina **`GYM_PYTHON`** (variable de entorno de usuario o del sistema) con la ruta completa a `python.exe`, por ejemplo:

`C:\Users\Usuario\AppData\Local\Programs\Python\Python311\python.exe`

---

## 3. Dependencias Python (solo escenario B)

Si el cliente instala Python por separado, las versiones fijadas en el proyecto son:

| Paquete | Versión |
|---------|---------|
| Django | 4.2.9 |
| djangorestframework | 3.14.0 |
| psycopg2-binary | 2.9.9 |
| Pillow | 10.2.0 |
| reportlab | 4.1.0 |
| django-crispy-forms | 2.1 |
| crispy-bootstrap5 | 0.7 |
| django-widget-tweaks | 1.5.0 |
| python-decouple | 3.8 |
| waitress | 3.0.0 |
| whitenoise | 6.6.0 |

Comando de referencia (ajustar rutas):

```powershell
"C:\Ruta\a\python.exe" -m pip install -r "C:\Ruta\al\backend\requirements.txt"
```

---

## 4. Instalación de PostgreSQL (resumen operativo)

1. Descargar el instalador oficial (p. ej. **EDB** para Windows) o usar el paquete offline de la organización.
2. Durante la instalación:
   - Anotar el **puerto** (por defecto **5432**).
   - Definir y **guardar** la contraseña del superusuario **`postgres`** (o el rol que se use como superusuario).
3. Comprobar en **Servicios de Windows** (`services.msc`) que el servicio de PostgreSQL está **En ejecución**.
4. *(Opcional corporativo)* Instalación silenciosa: ver en el repositorio `scripts/install_postgresql_silent.ps1` y `installer/README.md`.

**Firewall:** en uso **solo local** (`127.0.0.1`), normalmente no hace falta abrir PostgreSQL hacia la red; si hay políticas estrictas, verificar que **localhost** no quede bloqueado para el propio equipo.

---

## 5. Instalación de GYM ZT SIS

1. Copiar al equipo el archivo **`GYM ZT SIS-Setup-x.x.x.exe`** (y, si aplica, documentación o scripts en carpeta `scripts\`).
2. Ejecutar el instalador **como usuario con permisos** (doble clic; elevar solo si Windows lo solicita).
3. Elegir carpeta de destino si el asistente lo permite (`oneClick=false` en la configuración típica del proyecto).
4. Finalizar y usar el acceso directo **GYM ZT SIS** (escritorio o menú Inicio).

**Ubicación típica de la aplicación instalada:**

`C:\Users\<Usuario>\AppData\Local\Programs\GYM ZT SIS\`

**Backend empaquetado:**

`...\GYM ZT SIS\resources\backend\`

**Python embebido (si existe):**

`...\GYM ZT SIS\resources\python\python.exe`

---

## 6. Primera ejecución y archivos de configuración

### 6.1 Carpetas en el perfil del usuario Windows

| Ruta (típica) | Uso |
|---------------|-----|
| `%AppData%\GYM ZT SIS\` o `C:\Users\<Usuario>\AppData\Roaming\GYM ZT SIS\` | Configuración: **`.env`**, log **`gym_zt_sis_backend.log`**, posible **`credenciales_iniciales.txt`**, subcarpeta **`data`** (medios y estáticos recolectados). |

Variable de entorno opcional para forzar otra carpeta: **`GYM_ZT_SIS_CONFIG_DIR`**.

### 6.2 Qué hace el arranque la primera vez

Si **no** existe `.env` en esa carpeta, el **bootstrap** puede generar uno con valores aleatorios (incluidas claves y contraseñas de aplicación y admin inicial).

Si **ya** existe `.env`, se respeta; debe estar **bien formado** (formato `CLAVE=valor`, **sin** comandos SQL dentro del archivo).

### 6.3 Archivo `credenciales_iniciales.txt`

Si se genera automáticamente junto al `.env`, contiene usuario administrador Django inicial y contraseñas útiles. **Tras anotarlas**, conviene **eliminarlo** o guardarlo en lugar seguro.

---

## 7. Especificación del archivo `.env` (aplicación de escritorio)

Ubicación: **`%AppData%\GYM ZT SIS\.env`**

| Variable | Obligatoriedad | Descripción |
|----------|----------------|-------------|
| `SECRET_KEY` | Sí en producción | Clave secreta de Django. |
| `DEBUG` | Recomendado | `False` en uso normal. |
| `ALLOWED_HOSTS` | Recomendado | P. ej. `127.0.0.1,localhost`. |
| `DB_NAME` | Sí | Nombre de la base PostgreSQL (p. ej. `gym_zt_sis` o `gym_zt_sis_desktop`). |
| `DB_USER` | Sí | Usuario de conexión de la app (típico `gym_zt_app`). |
| `DB_PASSWORD` | Sí (si el rol exige clave) | **Debe coincidir** con la contraseña del rol en PostgreSQL. No vacío si el servidor exige contraseña. |
| `DB_HOST` | Sí | Típico `127.0.0.1` o `localhost`. |
| `DB_PORT` | Sí | Típico `5432`. |
| `POSTGRES_SUPERUSER` | Recomendado | Rol para crear BD/usuario (típico `postgres`). |
| `POSTGRES_SUPERUSER_PASSWORD` | Casi siempre sí | Contraseña del rol anterior. **Imprescindible** si PostgreSQL no acepta conexión local sin contraseña para ese rol. |
| `GYM_INIT_ADMIN_USER` | Opcional | Usuario Django inicial si la base no tiene usuarios. |
| `GYM_INIT_ADMIN_PASSWORD` | Opcional | Contraseña del admin inicial (solo si no hay usuarios). |
| `GYM_INIT_ADMIN_EMAIL` | Opcional | Email del admin inicial. |

**Reglas importantes:**

- El `.env` **no** debe contener sentencias **SQL** (`ALTER USER`, etc.). Esas se ejecutan solo en **pgAdmin** o **psql**.
- Si el rol **`gym_zt_app`** ya existía con otra contraseña, o bien se ejecuta en PostgreSQL `ALTER USER gym_zt_app WITH PASSWORD '...'` igual a `DB_PASSWORD`, o se usa una versión reciente del **bootstrap** que sincroniza la contraseña del rol con `DB_PASSWORD` al arrancar (requiere reinstalar app actualizada desde un build reciente).

---

## 8. Puertos y conflictos

| Puerto | Servicio |
|--------|----------|
| **5432** | PostgreSQL (por defecto). |
| **8000** | Servidor web local de GYM ZT SIS (Waitress). |

Si otro programa usa **8000**, la ventana puede no cargar hasta liberar el puerto o ajustar configuración avanzada (consultar soporte).

---

## 9. Lista de verificación post-instalación

- [ ] PostgreSQL instalado y **servicio en ejecución**.
- [ ] Puerto **5432** (o el configurado) accesible en **127.0.0.1**.
- [ ] Escenario **A** o **B** de Python resuelto (embebido en el `.exe` o Python + `pip install -r requirements.txt`).
- [ ] Instalador **GYM ZT SIS** ejecutado correctamente.
- [ ] Primera apertura: esperar **varios minutos** si hay migraciones y `collectstatic`.
- [ ] Archivo `.env` con **`POSTGRES_SUPERUSER_PASSWORD`** si `postgres` tiene contraseña.
- [ ] **`DB_PASSWORD`** coherente con el usuario **`DB_USER`** en PostgreSQL.
- [ ] Inicio de sesión en `http://127.0.0.1:8000/login/` desde la ventana de la app.
- [ ] Credenciales de **`credenciales_iniciales.txt`** o admin conocido anotado de forma segura.

---

## 10. Diagnóstico ante fallos

| Síntoma en log | Causa probable | Acción |
|----------------|----------------|--------|
| `fe_sendauth: no password supplied` (usuario `postgres`) | Falta contraseña del superusuario en `.env` | Añadir `POSTGRES_SUPERUSER_PASSWORD=...` |
| `password authentication failed for user "gym_zt_app"` | `DB_PASSWORD` no coincide con PostgreSQL | Corregir `.env` o `ALTER USER gym_zt_app WITH PASSWORD '...'` |
| `spawn` / Python no encontrado | Sin Python en PATH y sin embebido | Instalar Python + pip, o usar build con embebido; o **`GYM_PYTHON`**. |
| Health check / proceso termina código 1 | Bootstrap falló (BD, migraciones, etc.) | Revisar **`gym_zt_sis_backend.log`** en `%AppData%\GYM ZT SIS\`. |
| Pantalla en blanco prolongada | Primer arranque largo o puerto 8000 ocupado | Esperar; revisar log y cerrar otras apps en 8000. |

---

## 11. Copias de seguridad (recordatorio)

- **Base de datos:** `pg_dump` / `pg_restore` usando el nombre real de `DB_NAME`.
- **Archivos:** carpeta de **medios** bajo `%AppData%\GYM ZT SIS\data\` (o `GYM_ZT_SIS_DATA_DIR`).

Detalle de comandos: `GUIA_USUARIO_FINAL.md`.

---

## 12. Desinstalación y reinstalación

- **Desinstalar** la app desde “Agregar o quitar programas” **no** borra por defecto la base PostgreSQL ni el `.env` en Roaming; los datos persisten hasta que se eliminen explícitamente.
- **Reinstalar** el mismo `.exe` suele bastar; no es obligatorio borrar la BD salvo que se quiera empezar desde cero.
- Si se borra **solo la base** pero el rol `gym_zt_app` sigue existiendo, la contraseña del rol debe seguir coincidiendo con `DB_PASSWORD`.

---

## 13. Material de apoyo en el repositorio

| Ruta | Contenido |
|------|-----------|
| `docs/GUIA_USUARIO_FINAL.md` | Guía de usuario y soporte |
| `docs/MANUAL_INSTALACION_EQUIPO_NUEVO.md` | Este manual |
| `installer/README.md` | Empaquetado, Python embebido, firma |
| `scripts/` | PostgreSQL, venv, servicios |

---

## 14. Datos de contacto / soporte

*(Completar con teléfono, correo y horario de **MISACORP** o distribuidor.)*

---

*GYM ZT SIS — Django 4.2 + PostgreSQL + Electron + Waitress + WhiteNoise.*
