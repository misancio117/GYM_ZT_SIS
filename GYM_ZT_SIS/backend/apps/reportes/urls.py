from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.ReportesView.as_view(), name='reportes'),
    path('pdf/', views.reporte_pdf, name='pdf'),
]
