# GYM ZT SIS

Sistema de información web para la gestión integral de un gimnasio: clientes, membresías, asistencias, inventario, punto de venta (POS), caja, contabilidad de egresos, alertas operativas y reportes. La aplicación está orientada a operación diaria en español (Bolivia) con interfaz responsive basada en **Bootstrap 5**.

---

## Tabla de contenidos

- [Características principales](#características-principales)
- [Arquitectura y módulos](#arquitectura-y-módulos)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración (variables de entorno)](#configuración-variables-de-entorno)
- [Base de datos](#base-de-datos)
- [Ejecución en desarrollo](#ejecución-en-desarrollo)
- [API REST (resumen)](#api-rest-resumen)
- [Roles de usuario](#roles-de-usuario)
- [Despliegue y buenas prácticas](#despliegue-y-buenas-prácticas)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Manual instalación equipo nuevo (escritorio)](docs/MANUAL_INSTALACION_EQUIPO_NUEVO.md)
- [Manual de uso del sistema (usuario final)](docs/MANUAL_DE_USO_GYM_ZT_SIS.md)

---

## Características principales

| Área | Descripción |
|------|-------------|
| **Dashboard** | KPIs del día, gráficos de ingresos recientes, métricas de asistencia y membresías activas; regeneración de alertas al cargar. |
| **Asistencia** | Registro de entradas por cliente (una por día), visitantes ocasionales vinculados a ventas. |
| **Punto de venta (POS)** | Ventas de productos, membresías y entradas ocasionales; métodos de pago (efectivo, transferencia, QR); cálculo de totales, costos y ganancia. |
| **Caja** | Apertura/cierre, movimientos de ingreso y egreso, saldo calculado respecto al monto inicial. |
| **Clientes** | Ficha con CI única, contacto, foto, estado y notas; integración con membresías y ventas. |
| **Membresías** | Catálogo de planes (precio, duración); asignación a clientes con fechas de inicio/fin y estados (activa, expirada, cancelada). |
| **Inventario** | Productos con precios de compra/venta, stock, stock mínimo para alertas e imágenes. |
| **Contabilidad** | Panel y registro de **egresos** por categoría (compras, sueldos, alquiler, servicios, mantenimiento, otros). |
| **Reportes** | Reportes diarios, semanales y mensuales con agregados de ventas, egresos, asistencias y exportación (incluye generación con **ReportLab** donde aplique). |
| **Alertas** | Membresías por vencer o vencidas, stock bajo; listado y contador en la barra superior. |
| **Administración** | Usuarios del sistema y **auditoría** de acciones (crear/editar/eliminar, inicio/cierre de sesión) — visible para rol administrador. |

---

## Arquitectura y módulos

El proyecto sigue el patrón de aplicaciones Django (`apps.*`), cada una con modelos, vistas, formularios y plantillas donde corresponde:

| App | Responsabilidad |
|-----|-------------------|
| `apps.core` | Usuario personalizado (`Usuario`), roles, login/logout, gestión de usuarios, auditoría. |
| `apps.clientes` | CRUD de clientes; API de búsqueda. |
| `apps.membresias` | Planes y `ClienteMembresia` (asignaciones). |
| `apps.asistencia` | Asistencias y clientes ocasionales. |
| `apps.inventario` | Catálogo de productos y stock. |
| `apps.ventas` | Ventas, detalles, POS; API de procesamiento y listado de productos. |
| `apps.contabilidad` | Modelo `Egreso` y vistas de dashboard/listado. |
| `apps.caja` | Sesiones de caja y movimientos. |
| `apps.alertas` | Modelo `Alerta`, generación masiva (`generar_alertas`) y context processor para el UI. |
| `apps.reportes` | Vistas de reportes y exportaciones. |
| `apps.dashboard` | Página principal y API de estadísticas. |

**Autenticación:** modelo de usuario personalizado `core.Usuario` (extiende `AbstractUser`) con campo `rol`.  
**API:** Django REST Framework con autenticación por sesión y permiso `IsAuthenticated` por defecto.

---

## Stack tecnológico

- **Python** — compatible con **Django 4.2** (recomendado: Python 3.10 u 3.11).
- **Django 4.2** — framework web.
- **PostgreSQL** — base de datos (driver `psycopg2-binary`).
- **Django REST Framework** — endpoints JSON para POS, dashboard y búsqueda de clientes.
- **Pillow** — imágenes (fotos de clientes, productos).
- **ReportLab** — PDFs en reportes.
- **django-crispy-forms** + **crispy-bootstrap5** — formularios.
- **django-widget-tweaks** — ajustes de widgets en plantillas.
- **python-decouple** — configuración por variables de entorno.
- **Frontend:** Bootstrap 5, Bootstrap Icons, fuentes Google (Inter), CSS propio en `static/css/gym.css`.

**Internacionalización:** `LANGUAGE_CODE = es-bo`, `TIME_ZONE = America/La_Paz`.

**Escritorio:** **Electron** + **Waitress** (WSGI) para ejecutar el backend en local; **WhiteNoise** sirve estáticos con `DEBUG=False`. Ver `desktop/`, `run_server.py` y `docs/GUIA_USUARIO_FINAL.md`.

---

## Aplicación de escritorio (Electron)

| Elemento | Descripción |
|----------|-------------|
| `desktop/` | App Electron (`main.js`, splash, empaquetado con **electron-builder**). |
| `backend/run_server.py` | Arranca **Waitress** en `127.0.0.1:8000` tras bootstrap (BD, migraciones, staticfiles). |
| `backend/gym_zt_sis/bootstrap.py` | Crea `.env` si falta, asegura base PostgreSQL, `migrate`, `collectstatic`, superusuario inicial. |
| `scripts/` | PowerShell/Python para PostgreSQL, venv y utilidades. |
| `installer/README.md` | Cómo generar el `.exe` y opciones (Python embebido, firma). |

**Desarrollo rápido:**

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# PostgreSQL en ejecución; opcional: copiar .env en %APPDATA%\GYM-ZT-SIS o en backend\.env

cd ..\desktop
npm install
npm start
```

Variable opcional: `GYM_PYTHON` apunta al `python.exe` si no está en el PATH.

**Python embebido (recomendado):** desde la raíz del repo, `.\scripts\setup_embedded_python.ps1` (descarga Python 3.11 embeddable x64, pip y `backend/requirements.txt` en `desktop/resources/python/`). Esa carpeta no va a Git; `npm run dist` exige que exista antes de empaquetar.

**Instalador:** `npm run dist` dentro de `desktop/` (salida en `dist/`). Incluye backend, scripts y, si lo generó, Python embebido. El cliente final sigue necesitando **PostgreSQL** en ejecución.

**Manual de instalación en un PC nuevo (especificaciones completas):** [docs/MANUAL_INSTALACION_EQUIPO_NUEVO.md](docs/MANUAL_INSTALACION_EQUIPO_NUEVO.md).

---

## Requisitos previos

- Python 3.10+ (con `pip` y entorno virtual recomendado).
- Servidor **PostgreSQL** instalado y en ejecución.
- Herramientas de compilación en Windows si fuera necesario para dependencias nativas (p. ej. `psycopg2`); en la mayoría de casos `psycopg2-binary` evita compilación.

---

## Instalación (solo backend / desarrollo)

```powershell
cd GYM_ZT_SIS\backend

python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

O use `.\scripts\setup_python_backend.ps1` desde la raíz del repositorio.

---

## Configuración (variables de entorno)

El proyecto usa **python-decouple**. El archivo **`.env`** debe ser un **archivo** (no un directorio) en:

- **`backend/.env`** en desarrollo, o  
- **`%AppData%\GYM ZT SIS\.env`** cuando se usa la app Electron (variable `GYM_ZT_SIS_CONFIG_DIR`).

Variables principales:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta de Django. **Obligatoria en producción.** | *(cadena larga y aleatoria)* |
| `DEBUG` | Modo depuración (`True`/`False`). | `True` en desarrollo |
| `DB_NAME` | Nombre de la base PostgreSQL. | `gym_zt_sis` (desarrollo); en escritorio puede usarse p. ej. `gym_zt_sis_desktop` para no compartir datos con el IDE |
| `DB_USER` | Usuario PostgreSQL. | `postgres` |
| `DB_PASSWORD` | Contraseña del usuario. | *(su contraseña)* |
| `DB_HOST` | Host del servidor. | `localhost` |
| `DB_PORT` | Puerto. | `5432` |
| `POSTGRES_SUPERUSER` | Rol superusuario para crear la BD (bootstrap). | `postgres` |
| `POSTGRES_SUPERUSER_PASSWORD` | Contraseña del superusuario PostgreSQL (necesaria si `postgres` tiene clave). | *(ver guía usuario)* |

> **Importante:** no suba `.env` al control de versiones. Sin `.env`, Django usa valores por defecto solo para desarrollo; en escritorio el bootstrap genera uno en AppData.

**Datos de usuario:** `GYM_ZT_SIS_DATA_DIR` (opcional) define `media/` y `staticfiles/`; por defecto `%AppData%\GYM ZT SIS\data` en modo app.

**Parámetros de negocio** (en `gym_zt_sis/settings.py`):

- `DIAS_ALERTA_MEMBRESIA` — días de anticipación para alertar membresías próximas a vencer (por defecto 5).
- `STOCK_MINIMO_ALERTA` — referencia global para alertas de inventario (el umbral por producto es `stock_minimo` en el modelo).

---

## Base de datos

1. Cree una base de datos vacía en PostgreSQL con el nombre configurado en `DB_NAME`.

2. Aplique migraciones:

```bash
cd backend
python manage.py migrate
```

3. Cree un superusuario para el admin de Django y el acceso inicial:

```bash
python manage.py createsuperuser
```

En modo escritorio, el bootstrap puede crear el primer admin; revise `credenciales_iniciales.txt` en la carpeta de configuración.

4. (Opcional) Acceda a `/admin/` para datos iniciales o use la interfaz web según el flujo del negocio.

---

## Ejecución en desarrollo

```bash
cd backend
python manage.py runserver
```

Servidor de producción local (misma pila que Electron):

```bash
cd backend
python run_server.py
```

Por defecto: `http://127.0.0.1:8000/`

- La raíz `/` redirige a **`/login/`**.
- Tras iniciar sesión, la aplicación redirige a **`/dashboard/`**.

**Archivos estáticos y media en producción:**

```bash
python manage.py collectstatic
```

Configure el servidor web (nginx, IIS, etc.) para servir `STATIC_ROOT` y `MEDIA_ROOT` según la documentación de Django.

---

## API REST (resumen)

Todas las rutas bajo `/api/` requieren usuario autenticado (sesión), salvo que se amplíe la configuración de DRF.

| Prefijo | Uso |
|---------|-----|
| `POST /api/procesar/` | Procesar venta desde el POS (`ventas`). |
| `GET /api/productos/` | Listado de productos para el POS. |
| `GET /api/clientes/search/` | Búsqueda de clientes. |
| `GET /api/dashboard/stats/` | Estadísticas para el dashboard. |

Las URLs exactas pueden consultarse en:

- `apps/ventas/api_urls.py`
- `apps/clientes/api_urls.py`
- `apps/dashboard/api_urls.py`

---

## Roles de usuario

- **Administrador (`admin`):** acceso a **Usuarios** y **Auditoría** en el menú lateral.
- **Empleado (`empleado`):** operaciones habituales (dashboard, asistencia, ventas, caja, clientes, etc.) sin el bloque de administración avanzada.

Los permisos granularizados pueden ampliarse vía Django (`permissions`) o lógica en vistas según necesidades futuras.

---

## Despliegue y buenas prácticas

1. Establezca `DEBUG=False` y un `SECRET_KEY` único y seguro.
2. Use `ALLOWED_HOSTS` acotado (por defecto `127.0.0.1,localhost` en escritorio).
3. Sirva HTTPS en producción y configure cookies seguras si aplica.
4. Realice copias de seguridad periódicas de la base PostgreSQL y del directorio `media/` (fotos de clientes y productos).
5. Revise periódicamente dependencias por actualizaciones de seguridad.

---

## Estructura del repositorio

```
GYM_ZT_SIS/
├── README.md
├── docs/
│   └── GUIA_USUARIO_FINAL.md   # Manual para usuario final e IT
├── backend/                    # Django (WSGI, API, plantillas)
│   ├── manage.py
│   ├── run_server.py           # Waitress 127.0.0.1:8000
│   ├── requirements.txt
│   ├── gym_zt_sis/
│   ├── apps/
│   ├── templates/
│   └── static/
├── desktop/                    # Electron (main.js, splash, package.json)
├── scripts/                    # PostgreSQL, venv, init DB
├── installer/                  # Notas de build y recursos del instalador
└── dist/                       # Salida de electron-builder (generada)
```

---

## Licencia y créditos

Especificar aquí la licencia del proyecto y datos de contacto o de la organización (**MISACORP** / GYM ZT) según corresponda.

---

*Documentación generada para el proyecto **GYM ZT SIS** — sistema de gestión de gimnasio.*
