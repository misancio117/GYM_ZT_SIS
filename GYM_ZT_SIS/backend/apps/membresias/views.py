import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.views import View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from datetime import date, datetime, time

logger = logging.getLogger(__name__)
from .models import Membresia, ClienteMembresia
from apps.clientes.models import Cliente
from .forms import MembresiaForm, AsignarMembresiaForm
from apps.core.utils import log_auditoria
from apps.caja.models import Caja, MovimientoCaja
from apps.ventas.models import Venta, DetalleVenta


class MembresiaListView(LoginRequiredMixin, ListView):
    model = Membresia
    template_name = 'membresias/lista.html'
    context_object_name = 'membresias'


class MembresiaCrearView(LoginRequiredMixin, CreateView):
    model = Membresia
    form_class = MembresiaForm
    template_name = 'membresias/form.html'
    success_url = reverse_lazy('membresias:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Membresía'
        return ctx

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        response = super().form_valid(form)
        log_auditoria(
            request=self.request,
            accion='create',
            modulo='Membresías',
            descripcion=f'Creación de plan de membresía: {self.object.nombre}'
        )
        messages.success(self.request, 'Membresía creada exitosamente.')
        return response


class MembresiaEditarView(LoginRequiredMixin, UpdateView):
    model = Membresia
    form_class = MembresiaForm
    template_name = 'membresias/form.html'
    success_url = reverse_lazy('membresias:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar: {self.object.nombre}'
        return ctx
        
    def form_valid(self, form):
        response = super().form_valid(form)
        log_auditoria(
            request=self.request,
            accion='update',
            modulo='Membresías',
            descripcion=f'Edición de plan de membresía: {self.object.nombre}'
        )
        messages.success(self.request, 'Membresía actualizada exitosamente.')
        return response


class ClienteMembresiaListView(LoginRequiredMixin, ListView):
    model = ClienteMembresia
    template_name = 'membresias/asignaciones.html'
    context_object_name = 'asignaciones'
    paginate_by = 30

    def get_queryset(self):
        qs = ClienteMembresia.objects.select_related('cliente', 'membresia').order_by('-fecha_inicio')
        # Update expired statuses
        from django.utils import timezone
        qs.filter(estado='activa', fecha_fin__lt=timezone.now().date()).update(estado='expirada')
        estado = self.request.GET.get('estado', '')
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estado_filter'] = self.request.GET.get('estado', '')
        return ctx


class AsignarMembresiaView(LoginRequiredMixin, CreateView):
    model = ClienteMembresia
    form_class = AsignarMembresiaForm
    template_name = 'membresias/asignar.html'
    success_url = reverse_lazy('membresias:asignaciones')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        cliente_id = self.request.GET.get('cliente_id') or self.request.POST.get('cliente')
        if cliente_id:
            kwargs['initial'] = {'cliente': cliente_id}
        return kwargs

    def form_valid(self, form):
        metodo_pago = form.cleaned_data['metodo_pago']
        membresia = form.cleaned_data['membresia']
        cliente = form.cleaned_data['cliente']
        fecha_inicio = form.cleaned_data['fecha_inicio']

        today = date.today()
        es_historico = fecha_inicio < today

        if es_historico:
            # Busca la caja de ese día pasado (abierta o cerrada)
            caja = Caja.objects.filter(fecha_apertura__date=fecha_inicio).first()
            if not caja:
                # Crea una caja histórica cerrada para ese día
                dt_dia = datetime.combine(fecha_inicio, time.min)
                caja = Caja.objects.create(
                    usuario=self.request.user,
                    fecha_apertura=dt_dia,
                    fecha_cierre=datetime.combine(fecha_inicio, time(23, 59, 59)),
                    monto_inicial=0,
                    estado='cerrada',
                    observacion='Caja histórica (migración de datos)',
                )
            fecha_venta = datetime.combine(fecha_inicio, time.min)
            fecha_movimiento = datetime.combine(fecha_inicio, time.min)
        else:
            caja = Caja.objects.filter(estado='abierta').first()
            if not caja:
                messages.error(self.request, 'No hay una caja abierta. Abre la caja antes de asignar una membresía.')
                return self.form_invalid(form)
            fecha_venta = datetime.now()
            fecha_movimiento = datetime.now()

        try:
            with transaction.atomic():
                venta = Venta.objects.create(
                    cliente=cliente,
                    tipo='membresia',
                    total=membresia.precio,
                    costo_total=0,
                    ganancia=membresia.precio,
                    metodo_pago=metodo_pago,
                    fecha=fecha_venta,
                    usuario=self.request.user,
                )
                DetalleVenta.objects.create(
                    venta=venta,
                    tipo_item='membresia',
                    membresia=membresia,
                    disciplina=membresia.disciplina,
                    descripcion=f"{membresia.nombre} ({membresia.get_disciplina_display()})",
                    cantidad=1,
                    precio_unitario=membresia.precio,
                    costo_unitario=0,
                    subtotal=membresia.precio,
                    costo_subtotal=0,
                )
                MovimientoCaja.objects.create(
                    caja=caja,
                    tipo='ingreso',
                    descripcion=f'Membresía {membresia.nombre} [{membresia.get_disciplina_display()}] - {cliente.nombre} - {metodo_pago}',
                    monto=membresia.precio,
                    referencia=f'Venta #{venta.pk}',
                    fecha=fecha_movimiento,
                    usuario=self.request.user,
                )
                if es_historico:
                    caja.monto_final = caja.saldo_calculado
                    caja.save(update_fields=['monto_final'])
                form.instance.usuario = self.request.user
                form.instance.venta = venta
                response = super().form_valid(form)
        except Exception as e:
            logger.error(f'Error al asignar membresía: {e}', exc_info=True)
            messages.error(self.request, f'Error interno al registrar la membresía: {e}')
            return self.form_invalid(form)

        fecha_label = fecha_venta.strftime('%d/%m/%Y')
        log_auditoria(
            request=self.request,
            accion='create',
            modulo='Membresías',
            descripcion=f'Membresía "{membresia.nombre}" ({membresia.get_disciplina_display()}) asignada al cliente {cliente.nombre} - Venta #{venta.pk} - {metodo_pago} - Fecha: {fecha_label}'
        )
        messages.success(
            self.request,
            f'Membresía asignada. Venta #{venta.pk} registrada con fecha {fecha_label}.'
        )
        return response
