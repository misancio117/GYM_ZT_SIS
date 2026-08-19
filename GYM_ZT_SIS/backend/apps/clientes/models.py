from django.db import models


class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    nombre = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=255, blank=True, verbose_name='Ubicación')
    peso_inicial = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Peso Inicial (Kg)')
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to='clientes/', blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')
    fecha_registro = models.DateField(auto_now_add=True)
    notas = models.TextField(blank=True)
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def get_membresia_activa(self):
        if hasattr(self, '_membresias_prefetch'):
            lst = self._membresias_prefetch
            return lst[0] if lst else None
        from apps.membresias.models import ClienteMembresia
        return ClienteMembresia.objects.filter(
            cliente=self, estado='activa'
        ).first()
