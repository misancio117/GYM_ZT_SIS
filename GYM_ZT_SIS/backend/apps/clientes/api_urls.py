from django.urls import path
from . import views

app_name = 'clientes_api'

urlpatterns = [
    path('search/', views.cliente_search_api, name='search'),
]
