from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models.deletion import ProtectedError
from .models import Producto
from .forms import ProductoForm, AgregarStockForm
from apps.core.utils import log_auditoria, AdminRequeridoMixin


class ProductoListView(AdminRequeridoMixin, LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'inventario/lista.html'
    context_object_name = 'productos'

    def get_queryset(self):
        qs = Producto.objects.all()
        q = self.request.GET.get('q', '')
        cat = self.request.GET.get('cat', '')
        if q:
            qs = qs.filter(nombre__icontains=q)
        if cat:
            qs = qs.filter(categoria=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cat = self.request.GET.get('cat', '')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['cat'] = cat
        ctx['productos_bajo_stock'] = Producto.objects.filter(
            activo=True, stock__lte=5, categoria=cat if cat else 'snack').count()
        return ctx


class ProductoCrearView(AdminRequeridoMixin, LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'inventario/form.html'
    success_url = reverse_lazy('inventario:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nuevo Producto'
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        cat = self.request.GET.get('cat')
        if cat in ['snack', 'suplemento']:
            initial['categoria'] = cat
        return initial

    def form_valid(self, form):
        # Para que después de guardar, el usuario pueda regresar a la misma lista
        # en lugar de inventario:lista sin categoria (que muestra todo por defecto, o no? 
        # Bueno, la URL success es por defecto lista, vamos a redirigir con cat si venía)
        cat = form.cleaned_data.get('categoria')
        messages.success(self.request, 'Producto registrado exitosamente.')
        if cat:
            self.success_url = f"{reverse_lazy('inventario:lista')}?cat={cat}"
        return super().form_valid(form)


class ProductoEditarView(AdminRequeridoMixin, LoginRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'inventario/form.html'
    success_url = reverse_lazy('inventario:lista')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = f'Editar: {self.object.nombre}'
        return ctx

    def form_valid(self, form):
        cat = form.cleaned_data.get('categoria')
        messages.success(self.request, 'Producto actualizado exitosamente.')
        if cat:
            self.success_url = f"{reverse_lazy('inventario:lista')}?cat={cat}"
        return super().form_valid(form)


class AgregarStockView(AdminRequeridoMixin, LoginRequiredMixin, View):
    """View to add stock to an existing product (accumulates, does not replace)."""
    template_name = 'inventario/agregar_stock.html'

    def get(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        form = AgregarStockForm()
        return self._render(request, producto, form)

    def post(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)
        form = AgregarStockForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            stock_anterior = producto.stock
            producto.stock += cantidad
            producto.save(update_fields=['stock'])
            messages.success(
                request,
                f'Stock de "{producto.nombre}" actualizado: {stock_anterior} → {producto.stock} unidades (+{cantidad}).'
            )
            return redirect(f"{reverse('inventario:lista')}?cat={producto.categoria}")
        return self._render(request, producto, form)

    def _render(self, request, producto, form):
        from django.shortcuts import render
        return render(request, self.template_name, {
            'producto': producto,
            'form': form,
        })


class ProductoEliminarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)

        if not request.user.es_admin:
            messages.error(request, 'No tienes permisos para eliminar productos.')
            return redirect('inventario:lista')

        admin_password = request.POST.get('admin_password')
        if not admin_password or not request.user.check_password(admin_password):
            messages.error(request, 'Contraseña incorrecta. No se pudo eliminar el producto.')
            return redirect('inventario:lista')

        nombre = producto.nombre
        cat = producto.categoria

        try:
            producto.delete()
            log_auditoria(
                request=request,
                accion='delete',
                modulo='Inventario',
                descripcion=f'Eliminación de producto: {nombre} (ID: {pk})',
            )
            messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
        except ProtectedError:
            producto.activo = False
            producto.save(update_fields=['activo'])
            log_auditoria(
                request=request,
                accion='delete',
                modulo='Inventario',
                descripcion=f'Producto "{nombre}" (ID: {pk}) desactivado — tiene historial de ventas.',
            )
            messages.warning(
                request,
                f'"{nombre}" tiene historial de ventas y no puede eliminarse permanentemente. '
                f'Fue desactivado del inventario y no aparecerá más en ventas ni stock.'
            )

        return redirect(f"{reverse('inventario:lista')}?cat={cat}")
