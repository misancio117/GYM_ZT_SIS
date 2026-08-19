from django.db import models


class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ('snack', 'Snack'),
        ('suplemento', 'Suplemento'),
    ]
    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='snack')
    descripcion = models.TextField(blank=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5, verbose_name='Stock mínimo alerta')
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    @property
    def ganancia_unitaria(self):
        return self.precio_venta - self.precio_compra
