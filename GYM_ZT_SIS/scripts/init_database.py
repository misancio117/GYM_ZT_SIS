"""
Inicializa PostgreSQL + migraciones + superusuario (mismo flujo que run_server bootstrap).
Ejecutar desde la raíz del backend:

  cd backend
  python ../scripts/init_database.py

O:

  python scripts/init_database.py

con PYTHONPATH apuntando al backend.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Raíz del repositorio (padre de scripts/)
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / 'backend'
if BACKEND.is_dir():
    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_zt_sis.settings')
    if not os.environ.get('GYM_ZT_SIS_CONFIG_DIR'):
        if sys.platform == 'win32':
            base = os.environ.get('APPDATA') or str(Path.home())
            os.environ['GYM_ZT_SIS_CONFIG_DIR'] = str(Path(base) / 'GYM-ZT-SIS')
        else:
            os.environ['GYM_ZT_SIS_CONFIG_DIR'] = str(Path.home() / '.config' / 'gym-zt-sis')
    if not os.environ.get('GYM_ZT_SIS_DATA_DIR'):
        os.environ['GYM_ZT_SIS_DATA_DIR'] = str(Path(os.environ['GYM_ZT_SIS_CONFIG_DIR']) / 'data')

    from gym_zt_sis.bootstrap import bootstrap

    ok, messages = bootstrap()
    for m in messages:
        print(m)
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
