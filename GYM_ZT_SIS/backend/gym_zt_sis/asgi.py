"""
ASGI config for gym_zt_sis project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
os.environ.setdefault('GYM_ZT_SIS_BACKEND_ROOT', str(_backend))

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_zt_sis.settings')

application = get_asgi_application()
