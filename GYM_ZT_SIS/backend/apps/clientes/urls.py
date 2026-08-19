from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.ClienteListView.as_view(), name='lista'),
    path('nuevo/', views.ClienteCrearView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.ClienteEditarView.as_view(), name='editar'),
    path('<int:pk>/', views.ClienteDetalleView.as_view(), name='detalle'),
    path('<int:pk>/eliminar/', views.ClienteEliminarView.as_view(), name='eliminar'),
]
