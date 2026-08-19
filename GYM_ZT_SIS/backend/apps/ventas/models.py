from django.db import models
from django.utils import timezone


class Venta(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('qr', 'QR'),
    ]
    TIPO_VENTA_CHOICES = [
        ('producto', 'Producto'),
        ('membresia', 'Membresía'),
        ('ocasional', 'Entrada Ocasional'),
        ('mixto', 'Mixto'),
    ]
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='ventas')
    tipo = models.CharField(max_length=15, choices=TIPO_VENTA_CHOICES, default='producto')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ganancia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo')
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.pk} - Bs.{self.total} ({self.fecha.strftime('%d/%m/%Y')})"

    def calcular_totales(self):
        from apps.ventas.models import DetalleVenta
        detalles = self.detalles.all()
        self.total = sum(d.subtotal for d in detalles)
        self.costo_total = sum(d.costo_subtotal for d in detalles)
        self.ganancia = self.total - self.costo_total
        self.save(update_fields=['total', 'costo_total', 'ganancia'])


class DetalleVenta(models.Model):
    TIPO_ITEM_CHOICES = [
        ('producto', 'Producto'),
        ('membresia', 'Membresía'),
        ('ocasional', 'Entrada Ocasional'),
    ]
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    tipo_item = models.CharField(max_length=15, choices=TIPO_ITEM_CHOICES, default='producto')
    producto = models.ForeignKey('inventario.Producto', on_delete=models.PROTECT,
                                 null=True, blank=True)
    membresia = models.ForeignKey('membresias.Membresia', on_delete=models.PROTECT,
                                  null=True, blank=True)
    descripcion = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    costo_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad}"

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        self.costo_subtotal = self.costo_unitario * self.cantidad
        super().save(*args, **kwargs)
