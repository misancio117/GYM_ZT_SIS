"""
Inicialización para modo escritorio: .env, base PostgreSQL, migraciones, superusuario.
"""
from __future__ import annotations

import os
import secrets
import sys
import time
from pathlib import Path

STATIC_VERSION = '1.0.1'


def _config_dir() -> Path:
    raw = os.environ.get('GYM_ZT_SIS_CONFIG_DIR')
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent


def _data_dir() -> Path:
    raw = os.environ.get('GYM_ZT_SIS_DATA_DIR')
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent


def _env_path() -> Path:
    return _config_dir() / '.env'


def _write_env_if_missing() -> None:
    path = _env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return

    secret = secrets.token_urlsafe(48)
    db_name = os.environ.get('GYM_DB_NAME', 'gym_zt_sis')
    db_user = os.environ.get('GYM_DB_USER', 'gym_zt_app')
    db_pass = secrets.token_urlsafe(24)
    db_host = os.environ.get('GYM_DB_HOST', '127.0.0.1')
    db_port = os.environ.get('GYM_DB_PORT', '5432')
    super_pass = os.environ.get('POSTGRES_SUPERUSER_PASSWORD', '')

    lines = [
        f'SECRET_KEY={secret}',
        'DEBUG=False',
        'ALLOWED_HOSTS=127.0.0.1,localhost',
        '',
        f'DB_NAME={db_name}',
        f'DB_USER={db_user}',
        f'DB_PASSWORD={db_pass}',
        f'DB_HOST={db_host}',
        f'DB_PORT={db_port}',
        '',
    ]
    if super_pass:
        lines.append(f'POSTGRES_SUPERUSER_PASSWORD={super_pass}')
    lines.append('POSTGRES_SUPERUSER=postgres')
    lines.append('')
    lines.append('# Superusuario Django inicial (solo si no hay usuarios)')
    lines.append('GYM_INIT_ADMIN_USER=misacorp')
    lines.append(f'GYM_INIT_ADMIN_PASSWORD={secrets.token_urlsafe(12)}')
    lines.append('GYM_INIT_ADMIN_EMAIL=admin@localhost')
    lines.append('')

    path.write_text('\n'.join(lines), encoding='utf-8')

    creds = path.parent / 'credenciales_iniciales.txt'
    try:
        admin_pwd = [l for l in lines if l.startswith('GYM_INIT_ADMIN_PASSWORD=')][0].split('=', 1)[1]
        db_pwd_line = [l for l in lines if l.startswith('DB_PASSWORD=')][0].split('=', 1)[1]
        creds.write_text(
            'GYM ZT SIS — guarde este archivo en lugar seguro y elimínelo después.\n\n'
            f'Usuario administrador inicial: admin\n'
            f'Contraseña administrador: {admin_pwd}\n\n'
            f'Usuario de base de datos aplicación: {db_user}\n'
            f'Contraseña BD aplicación: {db_pwd_line}\n\n'
            'Si la creación de la base falla, defina POSTGRES_SUPERUSER_PASSWORD en .env '
            'con la contraseña del rol postgres de su instalación PostgreSQL.\n',
            encoding='utf-8',
        )
    except Exception:
        pass


def _pg_connect_kwargs(dbname: str, user: str, password: str | None, host: str, port: str):
    kw = {
        'dbname': dbname,
        'user': user,
        'host': host,
        'port': port,
        'connect_timeout': 12,
    }
    if password:
        kw['password'] = password
    return kw


def ensure_postgresql_database() -> tuple[bool, str]:
    """
    Crea rol y base de datos si no existen. Requiere acceso como superusuario (postgres).
    """
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError as e:
        return False, f'psycopg2 no disponible: {e}'

    from decouple import Config, RepositoryEnv

    env_file = _env_path()
    cfg = Config(RepositoryEnv(str(env_file)))
    db_name = cfg('DB_NAME', default='gym_zt_sis')
    db_user = cfg('DB_USER', default='gym_zt_app')
    db_password = cfg('DB_PASSWORD', default='')
    db_host = cfg('DB_HOST', default='127.0.0.1')
    db_port = cfg('DB_PORT', default='5432')

    super_name = cfg('POSTGRES_SUPERUSER', default='postgres')
    super_pass = cfg('POSTGRES_SUPERUSER_PASSWORD', default='')

    conn = None
    last_err = None
    for attempt in range(4):
        try:
            conn = psycopg2.connect(
                **_pg_connect_kwargs('postgres', super_name, super_pass or None, db_host, db_port)
            )
            last_err = None
            break
        except Exception as e:
            last_err = e
            time.sleep(1.2 * (attempt + 1))
    if conn is None:
        return False, (
            f'No se pudo conectar a PostgreSQL en {db_host}:{db_port} como "{super_name}". '
            f'Último error: {last_err}. '
            'Compruebe que el servicio PostgreSQL está en ejecución, el puerto 5432 está libre '
            f'y defina POSTGRES_SUPERUSER_PASSWORD en "{env_file}" si el rol postgres tiene contraseña.'
        )

    conn.autocommit = True
    cur = conn.cursor()

    try:
        cur.execute('SELECT 1 FROM pg_roles WHERE rolname = %s', (db_user,))
        role_exists = cur.fetchone()
        if not role_exists:
            if db_user == 'postgres':
                pass
            else:
                cur.execute(
                    sql.SQL('CREATE USER {} WITH PASSWORD %s').format(sql.Identifier(db_user)),
                    [db_password],
                )
        elif db_user != 'postgres' and db_password:
            # El rol ya existía (p. ej. tras borrar solo la BD): alinear clave con .env
            cur.execute(
                sql.SQL('ALTER USER {} WITH PASSWORD %s').format(sql.Identifier(db_user)),
                [db_password],
            )

        cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (db_name,))
        if not cur.fetchone():
            owner = sql.Identifier(db_user)
            cur.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(db_name), owner))
        # Propietario de la BD = usuario app (evita "permiso denegado" en migraciones si antes era postgres)
        if db_user != 'postgres':
            cur.execute(
                sql.SQL('ALTER DATABASE {} OWNER TO {}').format(
                    sql.Identifier(db_name),
                    sql.Identifier(db_user),
                )
            )
            cur.execute(
                sql.SQL('GRANT ALL PRIVILEGES ON DATABASE {} TO {}').format(
                    sql.Identifier(db_name),
                    sql.Identifier(db_user),
                )
            )
    finally:
        cur.close()
        conn.close()

    try:
        conn2 = psycopg2.connect(
            **_pg_connect_kwargs(db_name, super_name, super_pass or None, db_host, db_port)
        )
        conn2.autocommit = True
        c2 = conn2.cursor()
        u = sql.Identifier(db_user)
        c2.execute(sql.SQL('GRANT USAGE, CREATE ON SCHEMA public TO {}').format(u))
        c2.execute(sql.SQL('GRANT ALL ON SCHEMA public TO {}').format(u))
        if db_user != 'postgres':
            try:
                c2.execute(
                    sql.SQL('REASSIGN OWNED BY {} TO {}').format(
                        sql.Identifier(super_name),
                        u,
                    )
                )
            except Exception:
                pass
        c2.execute(
            sql.SQL('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}').format(u)
        )
        c2.execute(
            sql.SQL('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}').format(u)
        )
        c2.execute(
            sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}').format(u)
        )
        c2.execute(
            sql.SQL(
                'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}'
            ).format(u)
        )
        if db_user != 'postgres':
            try:
                c2.execute(sql.SQL('ALTER SCHEMA public OWNER TO {}').format(u))
            except Exception:
                pass
        c2.close()
        conn2.close()
    except Exception:
        pass

    return True, 'Base de datos lista.'


def run_migrations() -> tuple[bool, str]:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_zt_sis.settings')
    import django

    django.setup()
    from django.core.management import call_command

    try:
        call_command('migrate', '--noinput', verbosity=0)
    except Exception as e:
        return False, f'Error en migraciones: {e}'
    return True, 'Migraciones aplicadas.'


def run_collectstatic_if_needed() -> tuple[bool, str]:
    """Ejecuta collectstatic si la versión de estáticos no coincide con STATIC_VERSION."""
    from django.conf import settings
    from django.core.management import call_command

    root = Path(settings.STATIC_ROOT)
    marker = root / f'gym_zt_sis_static_v{STATIC_VERSION}'
    if marker.exists():
        return True, f'Staticfiles v{STATIC_VERSION} ya generados.'
    # Eliminar marcadores de versiones anteriores
    for old in root.glob('gym_zt_sis_static_v*'):
        try:
            old.unlink()
        except Exception:
            pass
    # Marcador legacy
    legacy = root / 'gym_zt_sis_desktop_static_ok'
    if legacy.exists():
        try:
            legacy.unlink()
        except Exception:
            pass
    try:
        root.mkdir(parents=True, exist_ok=True)
        call_command('collectstatic', '--noinput', verbosity=0)
        marker.write_text('ok', encoding='utf-8')
    except Exception as e:
        return False, f'collectstatic: {e}'
    return True, f'Archivos estáticos v{STATIC_VERSION} recolectados.'


def ensure_superuser() -> tuple[bool, str]:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return True, 'Ya existe un superusuario.'

    from decouple import Config, RepositoryEnv

    cfg = Config(RepositoryEnv(str(_env_path())))
    username = cfg('GYM_INIT_ADMIN_USER', default='admin')
    password = cfg('GYM_INIT_ADMIN_PASSWORD', default='')
    email = cfg('GYM_INIT_ADMIN_EMAIL', default='admin@localhost')

    if not password:
        return True, 'Sin GYM_INIT_ADMIN_PASSWORD; cree el administrador manualmente.'

    User.objects.create_superuser(username=username, email=email, password=password, rol='admin')
    return True, f'Superusuario "{username}" creado.'


def ensure_media_dirs():
    data = _data_dir()
    (data / 'media').mkdir(parents=True, exist_ok=True)
    (data / 'staticfiles').mkdir(parents=True, exist_ok=True)


def bootstrap() -> tuple[bool, list[str]]:
    messages: list[str] = []
    _write_env_if_missing()
    ensure_media_dirs()

    ok, msg = ensure_postgresql_database()
    messages.append(msg)
    if not ok:
        return False, messages

    ok, msg = run_migrations()
    messages.append(msg)
    if not ok:
        return False, messages

    ok, msg = run_collectstatic_if_needed()
    messages.append(msg)
    if not ok:
        return False, messages

    ok, msg = ensure_superuser()
    messages.append(msg)

    return True, messages
