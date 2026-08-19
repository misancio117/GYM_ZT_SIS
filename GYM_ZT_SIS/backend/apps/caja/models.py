from django.db import models
from django.utils import timezone


class Caja(models.Model):
    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True)
    fecha_apertura = models.DateTimeField(default=timezone.now)
    monto_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_final = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='abierta')
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Caja'
        verbose_name_plural = 'Cajas'
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f"Caja #{self.pk} - {self.estado} - {self.fecha_apertura.strftime('%d/%m/%Y')}"

    @property
    def total_ingresos(self):
        return sum(m.monto for m in self.movimientos.filter(tipo='ingreso'))

    @property
    def total_egresos(self):
        return sum(m.monto for m in self.movimientos.filter(tipo='egreso'))

    @property
    def saldo_calculado(self):
        return self.monto_inicial + self.total_ingresos - self.total_egresos


class MovimientoCaja(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    referencia = models.CharField(max_length=100, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Movimiento de Caja'
        verbose_name_plural = 'Movimientos de Caja'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo.upper()} - Bs.{self.monto} - {self.descripcion}"
