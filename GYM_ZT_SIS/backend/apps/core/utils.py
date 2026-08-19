from django.contrib import messages
from django.shortcuts import redirect
from .models import Auditoria


class AdminRequeridoMixin:
    """Bloquea el acceso a empleados; solo admins pueden entrar."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

def log_auditoria(request, accion, modulo, descripcion):
    """
    Registra una acción en la bitácora de auditoría.
    
    :param request: El request HTTP para extraer el usuario (si está autenticado) y la IP.
    :param accion: El tipo de acción ('create', 'update', 'delete', 'login', 'logout', etc).
    :param modulo: El módulo donde ocurre la acción ('Caja', 'Ventas', 'Clientes', etc).
    :param descripcion: Texto descriptivo de la acción realizada.
    """
    usuario = None
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        usuario = request.user
        
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

    Auditoria.objects.create(
        usuario=usuario,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion,
        ip=ip
    )
