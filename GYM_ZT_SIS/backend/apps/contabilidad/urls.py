from django.urls import path
from . import views

app_name = 'contabilidad'

urlpatterns = [
    path('', views.ContabilidadDashboardView.as_view(), name='dashboard'),
    path('egresos/', views.EgresosListView.as_view(), name='egresos_lista'),
    path('egresos/nuevo/', views.EgresoCrearView.as_view(), name='egreso_crear'),
]
