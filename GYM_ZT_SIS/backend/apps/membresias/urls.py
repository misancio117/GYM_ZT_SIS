from django.urls import path
from . import views

app_name = 'membresias'

urlpatterns = [
    path('', views.MembresiaListView.as_view(), name='lista'),
    path('nuevo/', views.MembresiaCrearView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.MembresiaEditarView.as_view(), name='editar'),
    path('asignaciones/', views.ClienteMembresiaListView.as_view(), name='asignaciones'),
    path('asignar/', views.AsignarMembresiaView.as_view(), name='asignar'),
]
