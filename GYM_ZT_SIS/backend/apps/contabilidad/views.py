from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import date, datetime, time
from .models import Egreso
from .forms import EgresoForm
from apps.ventas.models import Venta
from apps.caja.models import Caja, MovimientoCaja
from apps.core.utils import log_auditoria, AdminRequeridoMixin


class ContabilidadDashboardView(AdminRequeridoMixin, LoginRequiredMixin, ListView):
    model = Egreso
    template_name = 'contabilidad/dashboard.html'
    context_object_name = 'egresos'
    paginate_by = 20

    def get_queryset(self):
        # No mostramos egresos aquí — solo para los totales del contexto
        return Egreso.objects.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mes = self.request.GET.get('mes', timezone.now().strftime('%Y-%m'))
        ctx['mes'] = mes
        try:
            año, m = mes.split('-')
            ventas_mes = Venta.objects.filter(fecha__year=año, fecha__month=m)
            egresos_mes = Egreso.objects.filter(fecha__year=año, fecha__month=m)
        except Exception:
            ventas_mes = Venta.objects.none()
            egresos_mes = Egreso.objects.none()

        # Ingresos separados por categoría
        ingresos_gym = ventas_mes.filter(
            tipo__in=['membresia', 'ocasional']
        ).aggregate(t=Sum('total'))['t'] or 0

        ingresos_productos = ventas_mes.filter(
            tipo__in=['producto', 'mixto']
        ).aggregate(t=Sum('total'))['t'] or 0

        total_ingresos = ingresos_gym + ingresos_productos
        total_egresos = egresos_mes.aggregate(t=Sum('monto'))['t'] or 0

        # Ganancia neta = margen de productos + ingresos gym
        ganancia_productos = ventas_mes.filter(
            tipo__in=['producto', 'mixto']
        ).aggregate(g=Sum('ganancia'))['g'] or 0
        ganancia_neta = ganancia_productos + ingresos_gym

        ctx['ingresos_gym'] = ingresos_gym
        ctx['ingresos_productos'] = ingresos_productos
        ctx['total_ingresos'] = total_ingresos
        ctx['total_egresos'] = total_egresos
        ctx['utilidad'] = ganancia_neta - total_egresos
        ctx['ganancia_neta'] = ganancia_neta
        return ctx


class EgresosListView(LoginRequiredMixin, ListView):
    model = Egreso
    template_name = 'contabilidad/egresos_lista.html'
    context_object_name = 'egresos'
    paginate_by = 25

    def get_queryset(self):
        qs = Egreso.objects.all()
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        tipo = self.request.GET.get('tipo', '')
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs.order_by('-fecha')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        ctx['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        ctx['tipo'] = self.request.GET.get('tipo', '')
        ctx['tipo_choices'] = Egreso.TIPO_CHOICES
        total = self.get_queryset().aggregate(t=Sum('monto'))['t'] or 0
        ctx['total_egresos'] = total
        return ctx


class EgresoCrearView(LoginRequiredMixin, CreateView):
    model = Egreso
    form_class = EgresoForm
    template_name = 'contabilidad/egreso_form.html'
    success_url = reverse_lazy('contabilidad:egresos_lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['caja_abierta'] = Caja.objects.filter(estado='abierta').exists()
        return ctx

    def form_valid(self, form):
        egreso = form.save(commit=False)
        egreso.usuario = self.request.user

        fecha_egreso = egreso.fecha
        today = date.today()
        es_historico = fecha_egreso < today

        if es_historico:
            caja = Caja.objects.filter(fecha_apertura__date=fecha_egreso).first()
            if not caja:
                dt_dia = datetime.combine(fecha_egreso, time.min)
                caja = Caja.objects.create(
                    usuario=self.request.user,
                    fecha_apertura=dt_dia,
                    fecha_cierre=datetime.combine(fecha_egreso, time(23, 59, 59)),
                    monto_inicial=0,
                    estado='cerrada',
                    observacion='Caja histórica (migración de datos)',
                )
            fecha_movimiento = datetime.combine(fecha_egreso, time.min)
        else:
            caja = Caja.objects.filter(estado='abierta').first()
            if not caja:
                messages.error(self.request, '⚠️ No hay caja abierta. Abre la caja para registrar egresos de hoy.')
                return self.form_invalid(form)
            fecha_movimiento = datetime.now()

        egreso.save()

        MovimientoCaja.objects.create(
            caja=caja,
            tipo='egreso',
            descripcion=egreso.descripcion or egreso.get_tipo_display(),
            monto=egreso.monto,
            referencia=f'Egreso #{egreso.pk}',
            fecha=fecha_movimiento,
            usuario=self.request.user,
        )

        if es_historico:
            caja.monto_final = caja.saldo_calculado
            caja.save(update_fields=['monto_final'])

        log_auditoria(
            request=self.request,
            accion='create',
            modulo='Contabilidad',
            descripcion=f'Egreso registrado: Bs.{egreso.monto} ({egreso.get_tipo_display()}) - Fecha: {fecha_egreso}'
        )
        messages.success(self.request, f'✅ Egreso registrado para el {fecha_egreso.strftime("%d/%m/%Y")}.')
        self.object = egreso
        return HttpResponseRedirect(self.get_success_url())
