from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Prefetch
from .models import Asistencia, ClienteOcasional, DISCIPLINA_CHOICES
from apps.clientes.models import Cliente
from apps.membresias.models import ClienteMembresia
from apps.core.utils import log_auditoria


class AsistenciaRegistroView(LoginRequiredMixin, TemplateView):
    template_name = 'asistencia/registro.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.caja.models import Caja
        hoy = timezone.now().date()
        ctx['asistencias_hoy'] = Asistencia.objects.filter(fecha=hoy).select_related('cliente').prefetch_related(
            Prefetch(
                'cliente__membresias',
                queryset=ClienteMembresia.objects.filter(estado='activa').select_related('membresia'),
                to_attr='_membresias_prefetch'
            )
        ).order_by('-hora')
        ctx['total_hoy'] = ctx['asistencias_hoy'].count()
        ocasionales_qs = ClienteOcasional.objects.filter(fecha=hoy).order_by('-hora')
        ctx['ocasionales_hoy'] = ocasionales_qs.count()
        ctx['ocasionales_hoy_lista'] = ocasionales_qs
        ctx['caja_abierta'] = Caja.objects.filter(estado='abierta').exists()
        return ctx

    def post(self, request):
        cliente_id = request.POST.get('cliente_id')
        disciplina = request.POST.get('disciplina', '')
        hoy = timezone.now().date()
        try:
            cliente = get_object_or_404(Cliente, pk=cliente_id, estado='activo')
            if disciplina:
                membresia = cliente.get_membresia_activa(disciplina=disciplina)
            else:
                membresia = cliente.get_membresia_activa()

            if not membresia:
                messages.error(request, f'{cliente.nombre} no tiene membresía activa.')
                return redirect('asistencia:registro')

            disciplina_final = membresia.membresia.disciplina
            # Check duplicate per discipline on the same day
            if Asistencia.objects.filter(cliente=cliente, fecha=hoy, disciplina=disciplina_final).exists():
                messages.warning(
                    request,
                    f'{cliente.nombre} ya registró asistencia hoy a {membresia.membresia.get_disciplina_display()}.'
                )
                return redirect('asistencia:registro')

            Asistencia.objects.create(cliente=cliente, fecha=hoy, disciplina=disciplina_final)
            log_auditoria(
                request=request,
                accion='create',
                modulo='Asistencia',
                descripcion=f'Registro de asistencia: {cliente.nombre} ({membresia.membresia.get_disciplina_display()})'
            )
            messages.success(
                request,
                f'✅ Asistencia registrada: {cliente.nombre} ({membresia.membresia.get_disciplina_display()})'
            )
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('asistencia:registro')


class AsistenciaListView(LoginRequiredMixin, ListView):
    model = Asistencia
    template_name = 'asistencia/lista.html'
    context_object_name = 'asistencias'
    paginate_by = 50

    def get_queryset(self):
        qs = Asistencia.objects.select_related('cliente').prefetch_related(
            Prefetch(
                'cliente__membresias',
                queryset=ClienteMembresia.objects.filter(estado='activa').select_related('membresia'),
                to_attr='_membresias_prefetch'
            )
        ).order_by('-fecha', '-hora')
        fecha = self.request.GET.get('fecha', '')
        cliente_id = self.request.GET.get('cliente_id', '')
        disciplina = self.request.GET.get('disciplina', '')
        if fecha:
            qs = qs.filter(fecha=fecha)
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        if disciplina:
            qs = qs.filter(disciplina=disciplina)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['disciplina_filter'] = self.request.GET.get('disciplina', '')
        ctx['fecha_filter'] = self.request.GET.get('fecha', '')
        return ctx


class OcasionalRegistroView(LoginRequiredMixin, View):
    def post(self, request):
        from apps.ventas.models import Venta, DetalleVenta
        from apps.caja.models import Caja, MovimientoCaja
        caja = Caja.objects.filter(estado='abierta').first()
        if not caja:
            messages.error(request, 'No hay una caja abierta. Abre la caja para registrar entradas ocasionales.')
            return redirect('asistencia:registro')

        nombre = request.POST.get('nombre', 'Visitante') or 'Visitante'
        monto = request.POST.get('monto', 0)
        disciplina = request.POST.get('disciplina', 'gimnasio')
        if disciplina not in ['gimnasio', 'crossfit', 'kickboxing']:
            disciplina = 'gimnasio'
        metodo_pago = request.POST.get('metodo_pago', 'efectivo')
        hoy = timezone.now().date()

        disp_dict = dict(DISCIPLINA_CHOICES)
        disp_label = disp_dict.get(disciplina, 'Gimnasio')

        venta = Venta.objects.create(
            tipo='ocasional',
            total=monto,
            costo_total=0,
            ganancia=monto,
            metodo_pago=metodo_pago,
            usuario=request.user,
        )
        DetalleVenta.objects.create(
            venta=venta,
            tipo_item='ocasional',
            disciplina=disciplina,
            descripcion=f'Entrada Ocasional ({disp_label})',
            cantidad=1,
            precio_unitario=monto,
            costo_unitario=0,
            subtotal=monto,
            costo_subtotal=0,
        )
        ClienteOcasional.objects.create(
            nombre=nombre,
            disciplina=disciplina,
            fecha=hoy,
            monto_pagado=monto,
            metodo_pago=metodo_pago,
            venta=venta
        )
        MovimientoCaja.objects.create(
            caja=caja, tipo='ingreso',
            descripcion=f'Entrada ocasional {disp_label}: {nombre}',
            monto=monto, referencia=f'Venta #{venta.pk}',
            usuario=request.user
        )
        
        log_auditoria(
            request=request,
            accion='create',
            modulo='Ventas',
            descripcion=f'Entrada ocasional ({disp_label}) registrada: {nombre} por Bs.{monto}'
        )
        messages.success(request, f'✅ Entrada ocasional registrada ({disp_label}): {nombre} - Bs.{monto}')
        return redirect('asistencia:registro')
