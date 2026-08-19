from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.VentaListView.as_view(), name='lista'),
    path('pos/', views.POSView.as_view(), name='pos'),
    path('<int:pk>/', views.VentaDetalleView.as_view(), name='detalle'),
]
