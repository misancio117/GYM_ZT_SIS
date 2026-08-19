from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import date, timedelta
from apps.ventas.models import Venta
from apps.asistencia.models import Asistencia, ClienteOcasional
from apps.clientes.models import Cliente
from apps.membresias.models import ClienteMembresia
from apps.contabilidad.models import Egreso
from apps.caja.models import Caja
from apps.alertas.models import Alerta
from apps.ventas.utils import calcular_ganancia_neta
import json
import logging

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hoy = date.today()
        # Regenerate alerts
        try:
            Alerta.generar_alertas()
        except Exception:
            logger.exception('Error al generar alertas automáticas')

        # --------------- KPIs today ---------------
        ventas_hoy = Venta.objects.filter(fecha__date=hoy)
        egresos_hoy = Egreso.objects.filter(fecha=hoy)

        ingresos_hoy = ventas_hoy.aggregate(t=Sum('total'))['t'] or 0
        egresos_total_hoy = egresos_hoy.aggregate(t=Sum('monto'))['t'] or 0
        ganancia_hoy = calcular_ganancia_neta(ventas_hoy)

        asistencias_hoy = Asistencia.objects.filter(fecha=hoy).count()
        ocasionales_hoy = ClienteOcasional.objects.filter(fecha=hoy).count()
        membresias_activas = ClienteMembresia.objects.filter(estado='activa').count()

        # --------------- Chart data ---------------
        # Last 7 days income
        labels_7dias = []
        datos_7dias = []
        for i in range(6, -1, -1):
            d = hoy - timedelta(days=i)
            labels_7dias.append(d.strftime('%d/%m'))
            total = Venta.objects.filter(fecha__date=d).aggregate(t=Sum('total'))['t'] or 0
            datos_7dias.append(float(total))

        # Top 5 products sold this month
        top_productos = (
            Venta.objects.filter(fecha__year=hoy.year, fecha__month=hoy.month)
            .values('detalles__producto__nombre')
            .annotate(total_vendido=Sum('detalles__cantidad'))
            .exclude(detalles__producto__nombre=None)
            .order_by('-total_vendido')[:5]
        )

        # Payment method distribution — usar MONTO en vez de cantidad de transacciones
        metodos = Venta.objects.filter(fecha__date=hoy).values('metodo_pago').annotate(
            monto_total=Sum('total')
        )
        metodos_data = {m['metodo_pago']: float(m['monto_total']) for m in metodos}

        # Ventas recientes con el primer ítem del detalle — solo de hoy
        ventas_recientes_qs = Venta.objects.filter(fecha__date=hoy).select_related('cliente', 'usuario').prefetch_related('detalles').order_by('-fecha')[:8]
        ventas_recientes = []
        for v in ventas_recientes_qs:
            primer_detalle = v.detalles.first()
            producto_label = primer_detalle.descripcion if primer_detalle else 'N/A'
            ventas_recientes.append({
                'pk': v.pk,
                'producto_label': producto_label,
                'total': v.total,
                'metodo_pago': v.get_metodo_pago_display(),
                'hora': v.fecha.strftime('%H:%M'),
                'usuario_name': v.usuario.username if v.usuario else '-',
            })

        ctx.update({
            'ingresos_hoy': ingresos_hoy,
            'egresos_hoy': egresos_total_hoy,
            'ganancia_hoy': ganancia_hoy,
            'asistencias_hoy': asistencias_hoy,
            'ocasionales_hoy': ocasionales_hoy,
            'membresias_activas': membresias_activas,
            'total_clientes': Cliente.objects.filter(estado='activo').count(),
            'caja_activa': Caja.objects.filter(estado='abierta').first(),
            'labels_7dias': json.dumps(labels_7dias),
            'datos_7dias': json.dumps(datos_7dias),
            'top_productos': list(top_productos),
            'metodos_data': json.dumps(metodos_data),
            'ventas_recientes': ventas_recientes,
        })
        return ctx


@login_required
def dashboard_stats_api(request):
    """Real-time KPI API for dashboard AJAX refresh."""
    hoy = date.today()
    ventas_hoy = Venta.objects.filter(fecha__date=hoy)
    ingresos = float(ventas_hoy.aggregate(t=Sum('total'))['t'] or 0)
    egresos = float(Egreso.objects.filter(fecha=hoy).aggregate(t=Sum('monto'))['t'] or 0)
    ganancia = calcular_ganancia_neta(ventas_hoy)
    return JsonResponse({
        'ingresos': ingresos,
        'egresos': egresos,
        'ganancia': ganancia,
        'asistencias': Asistencia.objects.filter(fecha=hoy).count(),
        'ocasionales': ClienteOcasional.objects.filter(fecha=hoy).count(),
        'alertas': Alerta.objects.filter(estado='activa').count(),
    })
