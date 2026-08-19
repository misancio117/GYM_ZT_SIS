from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.ProductoListView.as_view(), name='lista'),
    path('nuevo/', views.ProductoCrearView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.ProductoEditarView.as_view(), name='editar'),
    path('<int:pk>/agregar-stock/', views.AgregarStockView.as_view(), name='agregar_stock'),
    path('<int:pk>/eliminar/', views.ProductoEliminarView.as_view(), name='eliminar'),
]
