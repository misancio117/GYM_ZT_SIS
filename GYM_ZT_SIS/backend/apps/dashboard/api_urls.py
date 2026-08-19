from django.urls import path
from . import views

app_name = 'dashboard_api'

urlpatterns = [
    path('stats/', views.dashboard_stats_api, name='stats'),
]
