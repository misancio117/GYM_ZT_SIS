from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Usuario, Auditoria
from .utils import log_auditoria
from django.contrib.auth.hashers import check_password
from .forms import UsuarioCrearForm, UsuarioEditarForm, UsuarioCambioPasswordAdminForm, RecuperarPaso1Form, RecuperarPaso2Form
from django.shortcuts import get_object_or_404


class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        log_auditoria(
            request=self.request,
            accion='login',
            modulo='Core',
            descripcion=f'Usuario {self.request.user.username} inició sesión'
        )
        return respuesta


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            log_auditoria(
                request=request,
                accion='logout',
                modulo='Core',
                descripcion=f'Usuario {request.user.username} cerró sesión'
            )
        return super().dispatch(request, *args, **kwargs)


class UsuarioListView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'core/usuarios_lista.html'
    context_object_name = 'usuarios'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class UsuarioCrearView(LoginRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCrearForm
    template_name = 'core/usuario_form.html'
    success_url = reverse_lazy('core:usuarios_lista')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Usuario creado exitosamente.')
        return super().form_valid(form)


class UsuarioEditarView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioEditarForm
    template_name = 'core/usuario_form.html'
    success_url = reverse_lazy('core:usuarios_lista')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Usuario {form.instance.username} actualizado exitosamente.')
        log_auditoria(
            request=self.request,
            accion='update',
            modulo='Usuarios',
            descripcion=f'Editó al usuario {form.instance.username}'
        )
        return super().form_valid(form)


class UsuarioPasswordChangeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/usuario_password.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        ctx['form'] = UsuarioCambioPasswordAdminForm(admin_user=self.request.user)
        return ctx

    def post(self, request, *args, **kwargs):
        target_user = get_object_or_404(Usuario, pk=self.kwargs['pk'])
        form = UsuarioCambioPasswordAdminForm(request.POST, admin_user=request.user)
        
        if form.is_valid():
            new_pass = form.cleaned_data['new_password1']
            target_user.set_password(new_pass)
            target_user.save()
            
            messages.success(request, f'La contraseña de {target_user.username} ha sido actualizada.')
            log_auditoria(
                request=request,
                accion='update',
                modulo='Usuarios',
                descripcion=f'Cambió la contraseña del usuario {target_user.username}'
            )
            return redirect('core:usuarios_lista')
            
        return self.render_to_response(self.get_context_data(form=form))


class RecuperarPasswordView(View):
    """Two-step password recovery via security question. No login required."""

    def get(self, request):
        username = request.session.get('recuperar_username')
        if username:
            try:
                usuario = Usuario.objects.get(username=username, is_active=True)
                if not usuario.pregunta_secreta:
                    request.session.pop('recuperar_username', None)
                    return self._render_paso1(request, RecuperarPaso1Form())
                return self._render_paso2(request, RecuperarPaso2Form(), usuario)
            except Usuario.DoesNotExist:
                request.session.pop('recuperar_username', None)
        return self._render_paso1(request, RecuperarPaso1Form())

    def post(self, request):
        if 'paso1' in request.POST:
            form = RecuperarPaso1Form(request.POST)
            if form.is_valid():
                request.session['recuperar_username'] = form.cleaned_data['username']
                return redirect('core:recuperar_password')
            return self._render_paso1(request, form)

        if 'paso2' in request.POST:
            username = request.session.get('recuperar_username')
            if not username:
                return redirect('core:recuperar_password')
            try:
                usuario = Usuario.objects.get(username=username, is_active=True)
            except Usuario.DoesNotExist:
                del request.session['recuperar_username']
                return redirect('core:recuperar_password')

            form = RecuperarPaso2Form(request.POST)
            if form.is_valid():
                respuesta = form.cleaned_data['respuesta'].strip().lower()
                if not check_password(respuesta, usuario.respuesta_secreta):
                    form.add_error('respuesta', 'Respuesta incorrecta.')
                    return self._render_paso2(request, form, usuario)
                usuario.set_password(form.cleaned_data['nueva_password'])
                usuario.save()
                del request.session['recuperar_username']
                log_auditoria(
                    request=request,
                    accion='update',
                    modulo='Usuarios',
                    descripcion=f'Recuperación de contraseña por pregunta secreta: {usuario.username}',
                )
                messages.success(request, 'Contraseña actualizada correctamente. Ya puedes iniciar sesión.')
                return redirect('core:login')
            return self._render_paso2(request, form, usuario)

        return redirect('core:recuperar_password')

    def _render_paso1(self, request, form):
        return render(request, 'core/recuperar_password.html', {'form': form, 'paso': 1})

    def _render_paso2(self, request, form, usuario=None):
        if usuario is None:
            username = request.session.get('recuperar_username', '')
            try:
                usuario = Usuario.objects.get(username=username)
            except Usuario.DoesNotExist:
                return redirect('core:recuperar_password')
        pregunta = usuario.pregunta_secreta
        return render(request, 'core/recuperar_password.html', {
            'form': form, 'paso': 2,
            'pregunta': pregunta,
            'nombre_usuario': usuario.get_full_name() or usuario.username,
        })


class AuditoriaListView(LoginRequiredMixin, ListView):
    model = Auditoria
    template_name = 'core/auditoria_lista.html'
    context_object_name = 'registros'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)
