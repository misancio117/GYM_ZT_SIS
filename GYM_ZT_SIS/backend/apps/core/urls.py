from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios_lista'),
    path('usuarios/nuevo/', views.UsuarioCrearView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioEditarView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/password/', views.UsuarioPasswordChangeView.as_view(), name='usuario_password'),
    path('auditoria/', views.AuditoriaListView.as_view(), name='auditoria'),
    path('recuperar-password/', views.RecuperarPasswordView.as_view(), name='recuperar_password'),
]
