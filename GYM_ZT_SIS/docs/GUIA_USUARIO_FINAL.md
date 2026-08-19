# Guía de instalación y uso — GYM ZT SIS (escritorio)

Documento orientado al **usuario final** y al **soporte técnico**. Describe el comportamiento del instalador, la base de datos PostgreSQL, copias de seguridad y resolución de incidencias habituales.

Para una **guía técnica detallada** (requisitos, `.env`, puertos, Python embebido vs sistema, checklist): [MANUAL_INSTALACION_EQUIPO_NUEVO.md](MANUAL_INSTALACION_EQUIPO_NUEVO.md).

Para **cómo usar el sistema día a día** (menú, dashboard, contabilidad, reportes, orígenes de datos): [MANUAL_DE_USO_GYM_ZT_SIS.md](MANUAL_DE_USO_GYM_ZT_SIS.md).

---

## 1. Qué hace el instalador automáticamente

Al instalar **GYM ZT SIS** desde el archivo `GYM ZT SIS-Setup-x.x.x.exe` (generado con electron-builder):

1. Copia la aplicación de escritorio (**Electron**) y los recursos del **backend Django** en la carpeta de instalación elegida.
2. Crea accesos directos en el menú Inicio y, si se eligió, en el escritorio.
3. La **primera vez** que abre la aplicación, el sistema:
   - Crea la carpeta de configuración en el perfil del usuario (véase sección 4).
   - Genera un archivo **`.env`** con claves y contraseñas si no existía.
   - Intenta conectar a **PostgreSQL** con el usuario superadministrador configurado (`postgres` por defecto).
   - **Crea la base de datos** indicada en `DB_NAME` del `.env` (por defecto `gym_zt_sis`; puede usar otra, p. ej. `gym_zt_sis_desktop`, véase sección 5) y el usuario de aplicación si no existen.
   - Ejecuta **migraciones** de Django y prepara archivos estáticos.
   - Crea un **usuario administrador inicial** si aún no hay usuarios en la base.

> **PostgreSQL:** el instalador de la aplicación **no sustituye** al instalador oficial de PostgreSQL. En entornos corporativos, PostgreSQL debe estar instalado previamente o instalarse con el script/documentación incluida (`scripts/install_postgresql_silent.ps1` y carpeta `installer/`). Una vez PostgreSQL esté en ejecución, la aplicación automatiza la creación de la base y el esquema.

---

## 2. Instalación en un equipo nuevo (resumen)

1. Instale **PostgreSQL para Windows** (versión soportada por su organización) o use el paquete offline suministrado por el proveedor.
2. Asegúrese de que el **servicio PostgreSQL** está en **Inicio** (automático) y **En ejecución**.
3. Instale **GYM ZT SIS** con el `.exe` y abra el acceso directo.
4. Espere la pantalla de carga la primera vez (migraciones y creación de BD pueden tardar varios minutos).
5. Inicie sesión con las credenciales del archivo **`credenciales_iniciales.txt`** (véase abajo).

### Si falla PostgreSQL

| Síntoma | Acción recomendada |
|--------|---------------------|
| Mensaje de error al conectar al servidor | Verifique que el servicio PostgreSQL esté iniciado: `scripts/ensure_postgresql_service.ps1 -TryStart` (PowerShell como administrador si es necesario). |
| Puerto 5432 ocupado por otro programa | Cambie el puerto en la instalación de PostgreSQL o detenga el otro servicio; luego ajuste `DB_PORT` en el `.env` de la aplicación. |
| Contraseña del rol `postgres` desconocida | Restablezca la contraseña según la documentación de PostgreSQL o reinstale con una contraseña conocida; luego defina `POSTGRES_SUPERUSER_PASSWORD` en el `.env` (ruta en sección 4). |
| PostgreSQL no instalado | Ejecute el instalador EDB en modo silencioso (ver `scripts/install_postgresql_silent.ps1`) o instálelo de forma interactiva desde postgresql.org. |

---

## 3. Cómo verificar que el sistema funciona

1. Abra la aplicación; debe mostrarse la **pantalla de inicio de sesión** web en `http://127.0.0.1:8000/login/`.
2. Inicie sesión con el usuario **admin** (u otro creado por su organización).
3. Compruebe que el **Dashboard** carga sin errores y que el menú lateral responde.
4. Opcional: en el navegador del sistema, abra `http://127.0.0.1:8000/admin/` con un usuario staff/superusuario.

---

## 4. Uso básico

### Cómo abrir el sistema

- Use el acceso directo **GYM ZT SIS** en el escritorio o en el menú Inicio.
- No es necesario abrir un navegador manualmente: la ventana de Electron carga la URL interna del servidor.

### Si no carga la pantalla

1. Espere al menos **2–3 minutos** la primera vez (migraciones, `collectstatic`, creación de BD).
2. Revise el archivo de log del backend:
   - `%AppData%\GYM ZT SIS\gym_zt_sis_backend.log`  
   (ruta típica según `userData` de Electron).
3. Compruebe que **ningún otro programa** use el puerto **8000** (otra instancia de GYM ZT SIS u otra aplicación).
4. Reinicie el equipo si el servicio PostgreSQL no arranca tras una instalación nueva.

---

## 5. Base de datos

### Dos bases: desarrollo y aplicación de escritorio (recomendado)

Si ya usa una base **`gym_zt_sis`** para desarrollo (terminal, Cursor, etc.) y quiere **no mezclar** datos con la app instalada (`.exe`):

1. Deje **`backend/.env`** (o el que use al correr `manage.py`) con **`DB_NAME=gym_zt_sis`** para desarrollo.
2. En el **`.env` de la app de escritorio** edite **`DB_NAME`** así:
   ```env
   DB_NAME=gym_zt_sis_desktop
   ```
   Ruta típica en Windows:
   ```text
   C:\Users\<su_usuario>\AppData\Roaming\GYM ZT SIS\.env
   ```
3. Guarde el archivo y **vuelva a abrir GYM ZT SIS**. El arranque creará la base `gym_zt_sis_desktop` (si no existe), aplicará migraciones y podrá tener un **admin y datos distintos** de su entorno de desarrollo.

> Si el `.env` de escritorio se generó automáticamente la primera vez, puede añadir o cambiar solo la línea `DB_NAME`. Mantenga **`POSTGRES_SUPERUSER_PASSWORD`** si PostgreSQL lo exige.

Los **respaldos** (`pg_dump`) debe hacerlos **por nombre de base** (`gym_zt_sis` vs `gym_zt_sis_desktop`) según cuál quiera archivar.

### Ubicación

- Los **datos** de negocio residen en el **servidor PostgreSQL local** (no en archivos sueltos de la carpeta de la aplicación).
- El nombre de la base lo define **`DB_NAME`** en el `.env` (por defecto en proyectos nuevos suele ser **`gym_zt_sis`**).
- La **configuración** (contraseñas de aplicación, `SECRET_KEY`, etc.) está en el archivo **`.env`** dentro de la carpeta de configuración del usuario de la app de escritorio:

  `%AppData%\GYM ZT SIS\.env`

- Junto al `.env` puede existir **`credenciales_iniciales.txt`** con el usuario administrador y contraseñas generadas la primera vez. **Elimínelo o protéjalo** tras anotar las credenciales.

### Cómo hacer backup

1. Use las herramientas estándar de PostgreSQL en línea de comandos:

```text
pg_dump -h 127.0.0.1 -p 5432 -U postgres -d gym_zt_sis -F c -f "C:\Respaldos\gym_zt_sis_%fecha%.backup"
```

2. Sustituya el usuario (`-U`) y la ruta de salida según su política interna.
3. Incluya en el backup la carpeta de **medios** si almacena fotos de clientes/productos:

   `%APPDATA%\GYM-ZT-SIS\data\media`

   (o la ruta definida por `GYM_ZT_SIS_DATA_DIR`).

### Cómo restaurar datos

1. Cree una base vacía o elimine la existente según procedimiento de su organización.
2. Restaure el volcado:

```text
pg_restore -h 127.0.0.1 -p 5432 -U postgres -d gym_zt_sis -c "C:\Respaldos\gym_zt_sis.backup"
```

3. Restaure la carpeta **media** si corresponde.
4. Reinicie **GYM ZT SIS**.

---

## 6. Soporte técnico — errores comunes

| Problema | Causa probable | Solución |
|----------|----------------|----------|
| Pantalla en blanco o error de conexión | Backend no levantó o PostgreSQL caído | Ver log `gym_zt_sis_backend.log`; iniciar servicio PostgreSQL. |
| Error de migraciones | Esquema inconsistente o versión distinta de la app | Copie el mensaje completo del log; restaurar backup o ejecutar migraciones con asistencia técnica. |
| No puedo iniciar sesión | Credenciales incorrectas o usuario borrado | Use `credenciales_iniciales.txt` o cree otro superusuario con `manage.py createsuperuser` desde consola (requiere conocimientos técnicos). |
| Puerto 8000 en uso | Otra instancia u otra app | Cierre la otra aplicación o cambie `GYM_WAITRESS_PORT` en el entorno (avanzado). |
| Estilos rotos o sin CSS | Staticfiles no generados | Deje que la aplicación termine el primer arranque; borre el marcador en `staticfiles` solo bajo indicación técnica. |

### Archivos útiles para diagnóstico

- Log del backend: `gym_zt_sis_backend.log` (en `userData` de la aplicación).
- Configuración: `.env` en `%APPDATA%\GYM-ZT-SIS\`.
- Instalación de PostgreSQL: registro de Windows (servicios) y logs del propio PostgreSQL.

---

## 7. Modo offline

La aplicación está pensada para funcionar **sin Internet**: el servidor y la base son locales. Solo se requiere red si su organización añade integraciones externas en el futuro.

---

## 8. Contacto

Complete con los datos de soporte de **MISACORP** o su distribuidor (teléfono, correo, horario).

---

*Documento asociado al proyecto GYM ZT SIS — Django + PostgreSQL + Electron.*
