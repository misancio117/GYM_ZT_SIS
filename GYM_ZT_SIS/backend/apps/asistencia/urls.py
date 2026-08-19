from django.urls import path
from . import views

app_name = 'asistencia'

urlpatterns = [
    path('', views.AsistenciaRegistroView.as_view(), name='registro'),
    path('lista/', views.AsistenciaListView.as_view(), name='lista'),
    path('ocasional/nuevo/', views.OcasionalRegistroView.as_view(), name='ocasional_nuevo'),
]
