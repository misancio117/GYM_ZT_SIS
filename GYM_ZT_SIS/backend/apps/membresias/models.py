from django.db import models
from django.utils import timezone
from datetime import timedelta, date


class Membresia(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_dias = models.PositiveIntegerField(verbose_name='Duración (días)')
    estado = models.BooleanField(default=True, verbose_name='Activa')
    descripcion = models.TextField(blank=True)
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Membresía'
        verbose_name_plural = 'Membresías'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.duracion_dias} días - Bs.{self.precio}"


class ClienteMembresia(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('expirada', 'Expirada'),
        ('cancelada', 'Cancelada'),
    ]
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='membresias')
    membresia = models.ForeignKey(Membresia, on_delete=models.PROTECT)
    fecha_inicio = models.DateField(default=date.today)
    fecha_fin = models.DateField(blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activa')
    venta = models.ForeignKey('ventas.Venta', on_delete=models.SET_NULL, null=True, blank=True)
    peso_registro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Peso (Kg)')
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Membresía de Cliente'
        verbose_name_plural = 'Membresías de Clientes'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.cliente} - {self.membresia} ({self.estado})"

    def save(self, *args, **kwargs):
        if not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timedelta(days=self.membresia.duracion_dias)
        self.verificar_estado()
        super().save(*args, **kwargs)

    def verificar_estado(self):
        hoy = timezone.now().date()
        if self.estado == 'activa' and self.fecha_fin < hoy:
            self.estado = 'expirada'

    @property
    def dias_restantes(self):
        hoy = timezone.now().date()
        delta = self.fecha_fin - hoy
        return delta.days

    @property
    def por_vencer(self):
        from django.conf import settings
        dias = getattr(settings, 'DIAS_ALERTA_MEMBRESIA', 5)
        return 0 <= self.dias_restantes <= dias
