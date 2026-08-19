from django.db.models import Sum, F
from apps.ventas.models import Venta, DetalleVenta


def calcular_ganancia_neta(ventas_qs):
    """
    Retorna un float con la ganancia neta total:
    - Productos/Mixto: campo 'ganancia' (precio_venta - precio_compra)
    - Membresías/Ocasionales: campo 'total' (ingreso directo del gym)
    """
    ganancia_productos = ventas_qs.filter(
        tipo__in=['producto', 'mixto']
    ).aggregate(g=Sum('ganancia'))['g'] or 0

    ingresos_gym = ventas_qs.filter(
        tipo__in=['membresia', 'ocasional']
    ).aggregate(t=Sum('total'))['t'] or 0

    return float(ganancia_productos) + float(ingresos_gym)


def calcular_ganancia_desglosada(ventas_qs):
    """
    Retorna un dict con el desglose completo por categoría:
    {
        'neta', 'ingresos_gym',
        'ingresos_snacks', 'ganancia_snacks',
        'ingresos_suplementos', 'ganancia_suplementos'
    }
    """
    ingresos_gym = ventas_qs.filter(
        tipo__in=['membresia', 'ocasional']
    ).aggregate(t=Sum('total'))['t'] or 0

    detalles = DetalleVenta.objects.filter(venta__in=ventas_qs, tipo_item='producto')

    rs_snack = detalles.filter(producto__categoria='snack').aggregate(
        i=Sum('subtotal'), g=Sum(F('subtotal') - F('costo_subtotal')))
    ingresos_snacks = rs_snack['i'] or 0
    ganancia_snacks = rs_snack['g'] or 0

    rs_sup = detalles.filter(producto__categoria='suplemento').aggregate(
        i=Sum('subtotal'), g=Sum(F('subtotal') - F('costo_subtotal')))
    ingresos_suplementos = rs_sup['i'] or 0
    ganancia_suplementos = rs_sup['g'] or 0

    ganancia_neta = float(ingresos_gym) + float(ganancia_snacks) + float(ganancia_suplementos)

    return {
        'neta': ganancia_neta,
        'ingresos_gym': float(ingresos_gym),
        'ingresos_snacks': float(ingresos_snacks),
        'ganancia_snacks': float(ganancia_snacks),
        'ingresos_suplementos': float(ingresos_suplementos),
        'ganancia_suplementos': float(ganancia_suplementos),
    }
