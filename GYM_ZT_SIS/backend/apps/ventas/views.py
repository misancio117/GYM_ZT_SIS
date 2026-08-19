import json
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, TemplateView, DetailView
from django.views import View
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import Venta, DetalleVenta
from apps.inventario.models import Producto
from apps.membresias.models import Membresia, ClienteMembresia
from apps.clientes.models import Cliente
from apps.caja.models import Caja, MovimientoCaja
from apps.core.utils import log_auditoria


class POSView(LoginRequiredMixin, TemplateView):
    template_name = 'ventas/pos.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['snacks'] = Producto.objects.filter(activo=True, stock__gt=0, categoria='snack')
        ctx['suplementos'] = Producto.objects.filter(activo=True, stock__gt=0, categoria='suplemento')
        ctx['caja_activa'] = Caja.objects.filter(estado='abierta').first()
        return ctx


class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/lista.html'
    context_object_name = 'ventas'
    paginate_by = 30

    def get_queryset(self):
        qs = Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles').order_by('-fecha')
        fecha = self.request.GET.get('fecha', '')
        metodo = self.request.GET.get('metodo', '')
        if fecha:
            qs = qs.filter(fecha__date=fecha)
        if metodo:
            qs = qs.filter(metodo_pago=metodo)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['fecha_filter'] = self.request.GET.get('fecha', '')
        ctx['metodo_filter'] = self.request.GET.get('metodo', '')
        ctx['total_filtrado'] = self.get_queryset().count()
        return ctx


class VentaDetalleView(LoginRequiredMixin, DetailView):
    model = Venta
    template_name = 'ventas/detalle.html'
    context_object_name = 'venta'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['detalles'] = self.object.detalles.all()
        return ctx


class ProcesarVentaView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            metodo_pago = data.get('metodo_pago', 'efectivo')
            cliente_id = data.get('cliente_id')
            notas = data.get('notas', '')

            if not items:
                return JsonResponse({'success': False, 'error': 'No hay items en el carrito.'})

            # Verificar caja abierta ANTES de procesar
            caja = Caja.objects.filter(estado='abierta').first()
            if not caja:
                return JsonResponse({
                    'success': False,
                    'error': '⚠️ No hay caja abierta. Debes abrir la caja antes de realizar ventas.'
                })

            cliente = Cliente.objects.get(pk=cliente_id) if cliente_id else None

            total_general = 0
            ventas_registradas = 0
            ids_registrados = []

            with transaction.atomic():
                for item in items:
                    subtotal = float(item['subtotal'])
                    costo_subtotal = float(item.get('costo_subtotal', 0))

                    venta = Venta.objects.create(
                        cliente=cliente,
                        total=subtotal,
                        costo_total=costo_subtotal,
                        ganancia=subtotal - costo_subtotal,
                        metodo_pago=metodo_pago,
                        notas=notas,
                        usuario=request.user,
                    )

                    detalle = DetalleVenta(
                        venta=venta,
                        tipo_item=item['tipo'],
                        descripcion=item['descripcion'],
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio_unitario'],
                        costo_unitario=item.get('costo_unitario', 0),
                        subtotal=subtotal,
                        costo_subtotal=costo_subtotal,
                    )
                    if item['tipo'] == 'producto' and item.get('producto_id'):
                        prod = Producto.objects.get(pk=item['producto_id'])
                        prod.stock -= item['cantidad']
                        prod.save(update_fields=['stock'])
                        detalle.producto = prod
                    detalle.save()

                    # Register individually in active cash register
                    MovimientoCaja.objects.create(
                        caja=caja, tipo='ingreso',
                        descripcion=item['descripcion'],
                        monto=subtotal,
                        referencia=f'Venta #{venta.pk} - {metodo_pago}',
                        usuario=request.user
                    )

                    log_auditoria(
                        request=request,
                        accion='create',
                        modulo='Ventas',
                        descripcion=f'Venta #{venta.pk} procesada ({item["descripcion"]}) por Bs.{subtotal}'
                    )

                    total_general += subtotal
                    ventas_registradas += 1
                    ids_registrados.append(str(venta.pk))

            ids_str = ", ".join(ids_registrados)
            return JsonResponse({'success': True, 'venta_id': ids_str, 'total': float(total_general), 'count': ventas_registradas})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@login_required
def productos_api(request):
    """Return product list as JSON for POS."""
    productos = Producto.objects.filter(activo=True, stock__gt=0).values(
        'id', 'nombre', 'precio_venta', 'precio_compra', 'stock', 'imagen'
    )
    data = []
    for p in productos:
        p['imagen'] = request.build_absolute_uri('/media/' + p['imagen']) if p['imagen'] else None
        data.append(p)
    return JsonResponse({'productos': data})
