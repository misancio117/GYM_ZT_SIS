"""
Django settings for gym_zt_sis project.
Soporta modo escritorio vía GYM_ZT_SIS_CONFIG_DIR (directorio del archivo .env).
"""

import os
from pathlib import Path
from decouple import Config, RepositoryEmpty, RepositoryEnv


def _resolve_base_dir() -> Path:
    """
    Carpeta del proyecto Django (donde están templates/, apps/, manage.py).

    Cubre: ejecución desde backend/, gym_zt_sis suelto en la raíz del repo,
    PYTHONPATH apuntando solo al workspace, y variable GYM_ZT_SIS_BACKEND_ROOT.
    """
    raw = os.environ.get('GYM_ZT_SIS_BACKEND_ROOT')
    if raw:
        p = Path(raw)
        if (p / 'templates').is_dir() and (p / 'manage.py').is_file():
            return p

    here = Path(__file__).resolve().parent.parent

    def _is_backend_root(d: Path) -> bool:
        return d.is_dir() and (d / 'templates').is_dir() and (d / 'manage.py').is_file()

    for candidate in (here, here / 'backend'):
        if _is_backend_root(candidate):
            return candidate

    # Subir desde la ubicación de settings.py (p. ej. .../gym_zt_sis/settings.py en raíz errónea)
    for parent in Path(__file__).resolve().parents:
        for candidate in (parent / 'backend', parent):
            if _is_backend_root(candidate):
                return candidate

    return here


BASE_DIR = _resolve_base_dir()


def _unique_existing_dirs(sub: str) -> list:
    """
    Busca `sub` (p. ej. 'templates', 'static') bajo varias raíces posibles.
    Evita TemplateDoesNotExist cuando BASE_DIR queda en la raíz del repo pero
    el código vive en backend/ (PYTHONPATH del IDE, gym_zt_sis duplicado, etc.).
    """
    settings_path = Path(__file__).resolve()
    pkg_parent = settings_path.parent.parent  # .../backend si settings es .../backend/gym_zt_sis/settings.py

    roots: list[Path | None] = [
        BASE_DIR,
        pkg_parent,
        pkg_parent / 'backend',
    ]
    env_b = os.environ.get('GYM_ZT_SIS_BACKEND_ROOT')
    if env_b:
        roots.append(Path(env_b))

    seen: set[Path] = set()
    out: list[Path] = []
    for root in roots:
        if root is None:
            continue
        for base in (root, root / 'backend'):
            try:
                candidate = (base / sub).resolve()
            except OSError:
                continue
            if candidate.is_dir() and candidate not in seen:
                seen.add(candidate)
                out.append(candidate)
    return out


_TEMPLATE_DIRS = _unique_existing_dirs('templates')
if not _TEMPLATE_DIRS:
    _TEMPLATE_DIRS = [BASE_DIR / 'templates']

_STATIC_EXTRA = _unique_existing_dirs('static')
if not _STATIC_EXTRA:
    _STATIC_EXTRA = [BASE_DIR / 'static']

# .env: 1) GYM_ZT_SIS_CONFIG_DIR (Electron/AppData), 2) backend/.env, 3) raíz del repo (padre de backend)
def _load_decouple_config():
    paths: list[Path] = []
    cfg = os.environ.get('GYM_ZT_SIS_CONFIG_DIR')
    if cfg:
        paths.append(Path(cfg) / '.env')
    paths.append(BASE_DIR / '.env')
    paths.append(BASE_DIR.parent / '.env')
    for env_file in paths:
        try:
            if env_file.is_file():
                return Config(RepositoryEnv(str(env_file)))
        except OSError:
            continue
    return Config(RepositoryEmpty())


config = _load_decouple_config()

# Datos de usuario (media, staticfiles recolectados) opcionalmente fuera del paquete
_DATA_DIR = os.environ.get('GYM_ZT_SIS_DATA_DIR')
if _DATA_DIR:
    _data_path = Path(_DATA_DIR)
    MEDIA_ROOT = _data_path / 'media'
    STATIC_ROOT = _data_path / 'staticfiles'
else:
    MEDIA_ROOT = BASE_DIR / 'media'
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Asegurar que existan los directorios de media
for folder in ['', 'clientes', 'productos']:
    path = MEDIA_ROOT / folder
    if not path.exists():
        os.makedirs(path, exist_ok=True)

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = config('DEBUG', default=False, cast=bool)

_allowed = config('ALLOWED_HOSTS', default='127.0.0.1,localhost')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'apps.core',
    'apps.clientes',
    'apps.membresias',
    'apps.asistencia',
    'apps.inventario',
    'apps.ventas',
    'apps.contabilidad',
    'apps.caja',
    'apps.alertas',
    'apps.reportes',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gym_zt_sis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': _TEMPLATE_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.alertas.context_processors.alertas_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'gym_zt_sis.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='gym_zt_sis'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-bo'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = False

STATIC_URL = '/static/'
STATICFILES_DIRS = _STATIC_EXTRA
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.Usuario'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

DIAS_ALERTA_MEMBRESIA = 5
STOCK_MINIMO_ALERTA = 5

_LOG_DIR = Path(_DATA_DIR) / 'logs' if _DATA_DIR else BASE_DIR / 'logs'
_LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(_LOG_DIR / 'app.log'),
            'formatter': 'default',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
