from apps.alertas.models import Alerta


def alertas_context(request):
    """Inject alert count and active alerts into all templates."""
    if request.user.is_authenticated:
        alertas = Alerta.objects.filter(estado='activa').order_by('-fecha')[:10]
        alertas_count = Alerta.objects.filter(estado='activa').count()
        return {
            'alertas_activas': alertas,
            'alertas_count': alertas_count,
        }
    return {}
