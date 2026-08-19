from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.CajaView.as_view(), name='caja'),
    path('historial/', views.CajaHistorialView.as_view(), name='historial'),
    path('<int:pk>/', views.CajaDetalleView.as_view(), name='detalle'),
]
