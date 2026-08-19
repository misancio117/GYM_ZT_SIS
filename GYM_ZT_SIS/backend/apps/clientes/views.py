from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import Cliente
from .forms import ClienteForm
from apps.core.utils import log_auditoria
from apps.membresias.models import ClienteMembresia, Membresia


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/lista.html'
    context_object_name = 'clientes'
    paginate_by = 20

    def get_queryset(self):
        qs = Cliente.objects.prefetch_related(
            Prefetch(
                'membresias',
                queryset=ClienteMembresia.objects.filter(
                    estado='activa'
                ).select_related('membresia'),
                to_attr='_membresias_prefetch',
            )
        )
        q = self.request.GET.get('q', '')
        membresia_filter = self.request.GET.get('membresia', '')
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(telefono__icontains=q))
        if membresia_filter == 'sin':
            con_activa = ClienteMembresia.objects.filter(estado='activa').values('cliente_id')
            qs = qs.exclude(pk__in=con_activa)
        elif membresia_filter:
            qs = qs.filter(
                membresias__estado='activa',
                membresias__membresia__pk=membresia_filter,
            ).distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['membresia_filter'] = self.request.GET.get('membresia', '')
        ctx['membresias_disponibles'] = Membresia.objects.filter(estado=True).order_by('nombre')
        return ctx


class ClienteCrearView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes:lista')

    def get_context_data(self, **kwargs):
        from apps.membresias.models import Membresia
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Cliente'
        ctx['membresias_disponibles'] = Membresia.objects.filter(estado=True)
        return ctx

    def form_valid(self, form):
        from django.contrib import messages
        from django.db import transaction
        from datetime import date, datetime, time
        from apps.membresias.models import Membresia, ClienteMembresia
        from apps.ventas.models import Venta, DetalleVenta
        from apps.caja.models import Caja, MovimientoCaja
        import logging
        logger = logging.getLogger(__name__)

        # Save the client first
        form.instance.usuario = self.request.user
        response = super().form_valid(form)
        cliente = self.object

        log_auditoria(
            request=self.request,
            accion='create',
            modulo='Clientes',
            descripcion=f'Registro de cliente: {cliente.nombre} (ID: {cliente.pk})'
        )

        # Check if membership was selected
        membresia_id = self.request.POST.get('membresia_id')
        if membresia_id:
            try:
                membresia = Membresia.objects.get(pk=membresia_id, estado=True)
                metodo_pago = self.request.POST.get('metodo_pago', 'efectivo')
                fecha_inicio_str = self.request.POST.get('fecha_inicio_membresia', '')
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                except Exception:
                    fecha_inicio = date.today()

                today = date.today()
                es_historico = fecha_inicio < today

                if es_historico:
                    caja = Caja.objects.filter(fecha_apertura__date=fecha_inicio).first()
                    if not caja:
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
                        messages.warning(
                            self.request,
                            f'Cliente "{cliente.nombre}" registrado, pero no hay caja abierta para registrar '
                            f'la membresía de hoy. Abre la caja y asigna la membresía desde el perfil del cliente.'
                        )
                        return response
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
                            usuario=self.request.user,
                            notas='Membresía asignada al registrar cliente.',
                            fecha=fecha_venta,
                        )
                        DetalleVenta.objects.create(
                            venta=venta,
                            tipo_item='membresia',
                            membresia=membresia,
                            descripcion=membresia.nombre,
                            cantidad=1,
                            precio_unitario=membresia.precio,
                            costo_unitario=0,
                            subtotal=membresia.precio,
                            costo_subtotal=0,
                        )
                        ClienteMembresia.objects.create(
                            cliente=cliente,
                            membresia=membresia,
                            fecha_inicio=fecha_inicio,
                            estado='activa',
                            venta=venta,
                            peso_registro=cliente.peso_inicial,
                            usuario=self.request.user,
                        )
                        MovimientoCaja.objects.create(
                            caja=caja,
                            tipo='ingreso',
                            descripcion=f'Membresía: {membresia.nombre} ({cliente.nombre})',
                            monto=membresia.precio,
                            referencia=f'Venta #{venta.pk}',
                            fecha=fecha_movimiento,
                            usuario=self.request.user,
                        )
                        if es_historico:
                            caja.monto_final = caja.saldo_calculado
                            caja.save(update_fields=['monto_final'])

                    log_auditoria(
                        request=self.request,
                        accion='create',
                        modulo='Membresías',
                        descripcion=f'Asignación de membresía "{membresia.nombre}" al cliente {cliente.nombre} - Fecha: {fecha_inicio}'
                    )
                    messages.success(
                        self.request,
                        f'Cliente registrado y membresía "{membresia.nombre}" asignada para el '
                        f'{fecha_inicio.strftime("%d/%m/%Y")}. Venta #{venta.pk} generada (Bs.{membresia.precio}).'
                    )
                except Exception as e:
                    logger.error(f'Error al asignar membresía en nuevo cliente: {e}', exc_info=True)
                    messages.warning(
                        self.request,
                        f'Cliente registrado, pero ocurrió un error al asignar la membresía: {e}'
                    )
            except Membresia.DoesNotExist:
                messages.warning(self.request, 'Cliente registrado. No se pudo asignar la membresía seleccionada.')
        else:
            messages.success(self.request, 'Cliente registrado exitosamente.')

        return response


class ClienteEditarView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/form.html'
    success_url = reverse_lazy('clientes:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar: {self.object.nombre}'
        return ctx

    def form_valid(self, form):
        from django.contrib import messages
        response = super().form_valid(form)
        log_auditoria(
            request=self.request,
            accion='update',
            modulo='Clientes',
            descripcion=f'Actualización de cliente: {self.object.nombre}'
        )
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return response


class ClienteEliminarView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        cliente = get_object_or_404(Cliente, pk=self.kwargs['pk'])
        
        # 1. Check if user is admin
        if not request.user.es_admin:
            messages.error(request, 'No tienes permisos para eliminar clientes.')
            return redirect('clientes:lista')
            
        # 2. Check password
        admin_password = request.POST.get('admin_password')
        if not admin_password or not request.user.check_password(admin_password):
            messages.error(request, 'Contraseña de administrador incorrecta. No se pudo eliminar el cliente.')
            return redirect('clientes:lista')
            
        # 3. Delete and Log
        nombre_cliente = cliente.nombre
        log_auditoria(
            request=request,
            accion='delete',
            modulo='Clientes',
            descripcion=f'Eliminación de cliente: {nombre_cliente} (ID: {self.kwargs["pk"]})'
        )
        cliente.delete()
        messages.success(request, f'Cliente "{nombre_cliente}" eliminado correctamente.')
        return redirect('clientes:lista')


class ClienteDetalleView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'clientes/detalle.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cliente = self.object
        ctx['membresias'] = cliente.membresias.select_related('membresia').order_by('-fecha_inicio')
        ctx['asistencias'] = cliente.asistencias.order_by('-fecha')[:30]
        ctx['ventas'] = cliente.ventas.order_by('-fecha')[:20]
        ctx['membresia_activa'] = cliente.get_membresia_activa()
        return ctx


@login_required
def cliente_search_api(request):
    """AJAX endpoint for client search (used in POS and Attendance)."""
    from apps.membresias.models import ClienteMembresia
    q = request.GET.get('q', '')
    clientes = list(Cliente.objects.filter(
        Q(nombre__icontains=q),
        estado='activo'
    )[:10])
    ids = [c.pk for c in clientes]
    membresias_map = {
        cm.cliente_id: cm.membresia.nombre
        for cm in ClienteMembresia.objects.filter(
            cliente_id__in=ids, estado='activa'
        ).select_related('membresia')
    }
    data = [
        {
            'id': c.pk,
            'nombre': c.nombre,
            'telefono': c.telefono,
            'membresia': membresias_map.get(c.pk, 'Sin membresía activa'),
        }
        for c in clientes
    ]
    return JsonResponse({'results': data})
