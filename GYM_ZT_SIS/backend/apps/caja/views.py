from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import re
from .models import Caja, MovimientoCaja
from apps.core.utils import log_auditoria


class CajaView(LoginRequiredMixin, TemplateView):
    template_name = 'caja/caja.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        caja = Caja.objects.filter(estado='abierta').first()
        ctx['caja'] = caja
        if caja:
            ctx['movimientos'] = caja.movimientos.order_by('-fecha')[:50]
            ctx['resumen_cierre'] = self._calcular_resumen(caja)
        ctx['cajas_anteriores'] = Caja.objects.filter(estado='cerrada').order_by('-fecha_apertura')[:10]
        return ctx

    def _calcular_resumen(self, caja):
        from apps.ventas.models import Venta
        ingresos_qs = list(caja.movimientos.filter(tipo='ingreso'))
        egresos_qs = list(caja.movimientos.filter(tipo='egreso'))

        venta_montos = {}
        sin_ref = Decimal('0')
        for m in ingresos_qs:
            match = re.search(r'Venta #(\d+)', m.referencia)
            if match:
                venta_id = int(match.group(1))
                venta_montos[venta_id] = venta_montos.get(venta_id, Decimal('0')) + m.monto
            else:
                sin_ref += m.monto

        ventas = Venta.objects.filter(pk__in=venta_montos.keys()).values('pk', 'metodo_pago')
        venta_map = {v['pk']: v['metodo_pago'] for v in ventas}

        efectivo = Decimal('0')
        qr = Decimal('0')
        transferencia = Decimal('0')
        for venta_id, monto in venta_montos.items():
            metodo = venta_map.get(venta_id, 'efectivo')
            if metodo == 'qr':
                qr += monto
            elif metodo == 'transferencia':
                transferencia += monto
            else:
                efectivo += monto
        efectivo += sin_ref

        total_egresos = sum(m.monto for m in egresos_qs)
        total_ingresos = efectivo + qr + transferencia

        return {
            'monto_inicial': caja.monto_inicial,
            'ingresos_efectivo': efectivo,
            'ingresos_qr': qr,
            'ingresos_transferencia': transferencia,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'monto_esperado': caja.monto_inicial + total_ingresos - total_egresos,
        }

    def post(self, request):
        accion = request.POST.get('accion')
        if accion == 'abrir':
            caja_activa = Caja.objects.filter(estado='abierta').first()
            if caja_activa:
                messages.warning(request, 'Ya hay una caja abierta.')
            else:
                try:
                    monto_inicial = Decimal(request.POST.get('monto_inicial', '0') or '0')
                    if monto_inicial < 0:
                        monto_inicial = Decimal('0')
                except InvalidOperation:
                    monto_inicial = Decimal('0')
                Caja.objects.create(usuario=request.user, monto_inicial=monto_inicial)
                log_auditoria(
                    request=request,
                    accion='create',
                    modulo='Caja',
                    descripcion=f'Apertura de caja con monto inicial: Bs.{monto_inicial}'
                )
                messages.success(request, f'Caja abierta con Bs.{monto_inicial} de monto inicial.')
        elif accion == 'cerrar':
            caja = Caja.objects.filter(estado='abierta').first()
            if caja:
                caja.estado = 'cerrada'
                caja.fecha_cierre = timezone.now()
                caja.monto_final = caja.saldo_calculado
                caja.save()
                log_auditoria(
                    request=request,
                    accion='update',
                    modulo='Caja',
                    descripcion=f'Cierre de caja (Saldo Final: Bs.{caja.monto_final})'
                )
                messages.success(request, f'Caja cerrada. Saldo final: Bs.{caja.monto_final}')
            else:
                messages.error(request, 'No hay caja abierta.')
        return redirect('caja:caja')


class CajaHistorialView(LoginRequiredMixin, ListView):
    model = Caja
    template_name = 'caja/historial.html'
    context_object_name = 'cajas'
    paginate_by = 20
    ordering = ['-fecha_apertura']


class CajaDetalleView(LoginRequiredMixin, TemplateView):
    template_name = 'caja/detalle.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.shortcuts import get_object_or_404
        caja = get_object_or_404(Caja, pk=self.kwargs['pk'])
        ctx['caja'] = caja
        ctx['movimientos'] = caja.movimientos.order_by('fecha')
        ctx['resumen'] = self._calcular_resumen(caja)
        return ctx

    def _calcular_resumen(self, caja):
        from apps.ventas.models import Venta
        ingresos_qs = list(caja.movimientos.filter(tipo='ingreso'))
        egresos_qs = list(caja.movimientos.filter(tipo='egreso'))

        venta_montos = {}
        sin_ref = Decimal('0')
        for m in ingresos_qs:
            match = re.search(r'Venta #(\d+)', m.referencia)
            if match:
                venta_id = int(match.group(1))
                venta_montos[venta_id] = venta_montos.get(venta_id, Decimal('0')) + m.monto
            else:
                sin_ref += m.monto

        ventas = Venta.objects.filter(pk__in=venta_montos.keys()).values('pk', 'metodo_pago')
        venta_map = {v['pk']: v['metodo_pago'] for v in ventas}

        efectivo = Decimal('0')
        qr = Decimal('0')
        transferencia = Decimal('0')
        for venta_id, monto in venta_montos.items():
            metodo = venta_map.get(venta_id, 'efectivo')
            if metodo == 'qr':
                qr += monto
            elif metodo == 'transferencia':
                transferencia += monto
            else:
                efectivo += monto
        efectivo += sin_ref

        total_egresos = sum(m.monto for m in egresos_qs)
        total_ingresos = efectivo + qr + transferencia

        return {
            'monto_inicial': caja.monto_inicial,
            'ingresos_efectivo': efectivo,
            'ingresos_qr': qr,
            'ingresos_transferencia': transferencia,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'monto_esperado': caja.monto_inicial + total_ingresos - total_egresos,
        }
