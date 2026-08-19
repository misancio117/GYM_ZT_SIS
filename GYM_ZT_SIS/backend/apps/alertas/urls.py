from django.urls import path
from . import views

app_name = 'alertas'

urlpatterns = [
    path('', views.AlertaListView.as_view(), name='lista'),
    path('<int:pk>/leer/', views.MarcarAlertaLeidaView.as_view(), name='marcar_leida'),
    path('generar/', views.GenerarAlertasView.as_view(), name='generar'),
]
