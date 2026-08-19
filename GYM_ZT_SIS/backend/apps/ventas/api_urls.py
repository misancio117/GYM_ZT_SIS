from django.urls import path
from . import views

app_name = 'ventas_api'

urlpatterns = [
    path('procesar/', views.ProcesarVentaView.as_view(), name='procesar'),
    path('productos/', views.productos_api, name='productos'),
]
