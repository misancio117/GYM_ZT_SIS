from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Alerta


class AlertaListView(LoginRequiredMixin, ListView):
    model = Alerta
    template_name = 'alertas/lista.html'
    context_object_name = 'alertas'
    paginate_by = 30

    def get_queryset(self):
        return Alerta.objects.order_by('-fecha')

    def get(self, request, *args, **kwargs):
        # Regenerate alerts on each view
        Alerta.generar_alertas()
        return super().get(request, *args, **kwargs)


class MarcarAlertaLeidaView(LoginRequiredMixin, View):
    def post(self, request, pk):
        alerta = Alerta.objects.filter(pk=pk).first()
        if alerta:
            alerta.estado = 'leida'
            alerta.save()
        return redirect('alertas:lista')


class GenerarAlertasView(LoginRequiredMixin, View):
    def post(self, request):
        Alerta.generar_alertas()
        messages.success(request, 'Alertas actualizadas.')
        return redirect('alertas:lista')
