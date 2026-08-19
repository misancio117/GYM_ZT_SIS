from django.db import models
from django.utils import timezone


class Alerta(models.Model):
    TIPO_CHOICES = [
        ('membresia_por_vencer', 'Membresía por Vencer'),
        ('membresia_vencida', 'Membresía Vencida'),
        ('stock_bajo', 'Stock Bajo'),
        ('caja_abierta', 'Caja Abierta'),
        ('otro', 'Otro'),
    ]
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('leida', 'Leída'),
        ('resuelta', 'Resuelta'),
    ]
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activa')
    fecha = models.DateTimeField(default=timezone.now)
    referencia_id = models.PositiveIntegerField(null=True, blank=True)
    referencia_modelo = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-fecha']

    def __str__(self):
        return f"[{self.tipo}] {self.mensaje[:50]}"

    @classmethod
    def generar_alertas(cls):
        """Generate all alerts: expiring memberships, low stock."""
        from django.conf import settings
        from apps.membresias.models import ClienteMembresia
        from apps.inventario.models import Producto
        from django.utils import timezone

        dias_alerta = getattr(settings, 'DIAS_ALERTA_MEMBRESIA', 5)
        hoy = timezone.now().date()

        # Clear old alerts of same type to avoid duplicates
        cls.objects.filter(tipo__in=['membresia_por_vencer', 'membresia_vencida', 'stock_bajo']).delete()

        # Memberships about to expire
        proximas = ClienteMembresia.objects.filter(
            estado='activa',
            fecha_fin__range=[hoy, hoy + timezone.timedelta(days=dias_alerta)]
        )
        for cm in proximas:
            cls.objects.create(
                tipo='membresia_por_vencer',
                mensaje=f"La membresía de {cm.cliente.nombre} vence el {cm.fecha_fin.strftime('%d/%m/%Y')} ({cm.dias_restantes} días restantes)",
                referencia_id=cm.pk,
                referencia_modelo='ClienteMembresia'
            )

        # Expired memberships
        vencidas = ClienteMembresia.objects.filter(
            estado='activa', fecha_fin__lt=hoy
        )
        for cm in vencidas:
            cm.estado = 'expirada'
            cm.save(update_fields=['estado'])
            cls.objects.create(
                tipo='membresia_vencida',
                mensaje=f"La membresía de {cm.cliente.nombre} venció el {cm.fecha_fin.strftime('%d/%m/%Y')}",
                referencia_id=cm.pk,
                referencia_modelo='ClienteMembresia'
            )

        # Low stock
        productos_bajo = Producto.objects.filter(activo=True, stock__lte=models.F('stock_minimo'))
        for prod in productos_bajo:
            cls.objects.create(
                tipo='stock_bajo',
                mensaje=f"Stock bajo: {prod.nombre} tiene solo {prod.stock} unidades (mínimo: {prod.stock_minimo})",
                referencia_id=prod.pk,
                referencia_modelo='Producto'
            )
