"""
Servidor WSGI local para GYM ZT SIS (Waitress).
Uso: python run_server.py
Variables opcionales:
  GYM_ZT_SIS_CONFIG_DIR — directorio del .env (por defecto %APPDATA%/GYM-ZT-SIS en Windows)
  GYM_ZT_SIS_DATA_DIR — media y staticfiles (por defecto CONFIG_DIR/data)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
# Raíz fija para templates/apps (evita BASE_DIR erróneo si hay otro gym_zt_sis en PYTHONPATH)
os.environ['GYM_ZT_SIS_BACKEND_ROOT'] = str(BACKEND_ROOT)
os.chdir(BACKEND_ROOT)
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _default_config_dir() -> Path:
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA') or str(Path.home())
        return Path(base) / 'GYM-ZT-SIS'
    return Path.home() / '.config' / 'gym-zt-sis'


def _ensure_runtime_env():
    cfg = os.environ.get('GYM_ZT_SIS_CONFIG_DIR')
    if not cfg:
        os.environ['GYM_ZT_SIS_CONFIG_DIR'] = str(_default_config_dir())
    data = os.environ.get('GYM_ZT_SIS_DATA_DIR')
    if not data:
        os.environ['GYM_ZT_SIS_DATA_DIR'] = str(Path(os.environ['GYM_ZT_SIS_CONFIG_DIR']) / 'data')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_zt_sis.settings')
    os.environ.setdefault('DJANGO_DESKTOP_MODE', '1')


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s %(message)s',
    )
    _ensure_runtime_env()

    from gym_zt_sis.bootstrap import bootstrap

    ok, messages = bootstrap()
    for line in messages:
        logging.info(line)
    if not ok:
        logging.error('Bootstrap falló; no se inicia el servidor.')
        sys.exit(1)

    from waitress import serve
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
    host = os.environ.get('GYM_WAITRESS_HOST', '127.0.0.1')
    port = int(os.environ.get('GYM_WAITRESS_PORT', '8000'))
    threads = int(os.environ.get('GYM_WAITRESS_THREADS', '4'))
    logging.info('Iniciando Waitress en http://%s:%s/', host, port)
    serve(application, host=host, port=port, threads=threads, channel_timeout=120)


if __name__ == '__main__':
    main()
