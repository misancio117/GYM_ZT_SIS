#!/usr/bin/env python
"""
Delegación al Django real en backend/.
Úsalo si ejecutas desde la raíz del repo (Cursor/VS Code a vece pone el workspace en sys.path
y termina un servidor con rutas mal resueltas).

Desde terminal:  python manage.py runserver
(Recomendado también: cd backend && python manage.py runserver)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import subprocess

BACKEND = Path(__file__).resolve().parent / 'backend'
MANAGE = BACKEND / 'manage.py'

if not MANAGE.is_file():
    sys.stderr.write(f"No se encontró {MANAGE}\n")
    raise SystemExit(1)

os.environ.setdefault('GYM_ZT_SIS_BACKEND_ROOT', str(BACKEND))

# Mismo intérprete, cwd=backend, argumentos tras manage.py
rc = subprocess.call([sys.executable, str(MANAGE), *sys.argv[1:]], cwd=str(BACKEND))
raise SystemExit(rc)
