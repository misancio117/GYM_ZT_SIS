from django.db import models
from django.utils import timezone


DISCIPLINA_CHOICES = [
    ('gimnasio', 'Gimnasio'),
    ('crossfit', 'Crossfit'),
    ('kickboxing', 'Kick Boxing'),
]


class Asistencia(models.Model):
    DISCIPLINA_CHOICES = DISCIPLINA_CHOICES
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='asistencias')
    disciplina = models.CharField(
        max_length=20,
        choices=DISCIPLINA_CHOICES,
        default='gimnasio',
        verbose_name='Disciplina / Área'
    )
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(auto_now_add=True)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['-fecha', '-hora']
        unique_together = ['cliente', 'fecha', 'disciplina']

    def __str__(self):
        return f"{self.cliente} - {self.get_disciplina_display()} - {self.fecha} {self.hora}"


class ClienteOcasional(models.Model):
    DISCIPLINA_CHOICES = DISCIPLINA_CHOICES
    nombre = models.CharField(max_length=150, blank=True, default='Visitante')
    disciplina = models.CharField(
        max_length=20,
        choices=DISCIPLINA_CHOICES,
        default='gimnasio',
        verbose_name='Disciplina / Área'
    )
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, default='efectivo')
    venta = models.ForeignKey('ventas.Venta', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Cliente Ocasional'
        verbose_name_plural = 'Clientes Ocasionales'
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"{self.nombre} ({self.get_disciplina_display()}) - {self.fecha} - Bs.{self.monto_pagado}"
