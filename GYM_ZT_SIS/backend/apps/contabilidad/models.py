from django.db import models
from django.utils import timezone


class Egreso(models.Model):
    TIPO_CHOICES = [
        ('compra_producto', 'Compra de Producto'),
        ('sueldos', 'Sueldos'),
        ('alquiler', 'Alquiler'),
        ('servicios', 'Servicios (Luz/Agua/Internet)'),
        ('mantenimiento', 'Mantenimiento'),
        ('otros', 'Otros'),
    ]
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default='otros')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField(default=timezone.now)
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Egreso'
        verbose_name_plural = 'Egresos'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - Bs.{self.monto} ({self.fecha})"
