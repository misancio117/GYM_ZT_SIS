from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('empleado', 'Empleado'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='empleado')
    pregunta_secreta = models.CharField(max_length=200, blank=True, default='')
    respuesta_secreta = models.CharField(max_length=128, blank=True, default='')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == 'admin'

    @property
    def es_empleado(self):
        return self.rol == 'empleado'


class Auditoria(models.Model):
    ACCION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('login', 'Iniciar sesión'),
        ('logout', 'Cerrar sesión'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    modulo = models.CharField(max_length=50)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.modulo} ({self.fecha})"
