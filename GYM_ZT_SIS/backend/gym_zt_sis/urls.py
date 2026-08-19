"""
URL configuration for gym_zt_sis project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('', include('apps.core.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('membresias/', include('apps.membresias.urls')),
    path('asistencia/', include('apps.asistencia.urls')),
    path('inventario/', include('apps.inventario.urls')),
    path('ventas/', include('apps.ventas.urls')),
    path('contabilidad/', include('apps.contabilidad.urls')),
    path('caja/', include('apps.caja.urls')),
    path('alertas/', include('apps.alertas.urls')),
    path('reportes/', include('apps.reportes.urls')),
    # API endpoints
    path('api/', include('apps.ventas.api_urls')),
    path('api/clientes/', include('apps.clientes.api_urls')),
    path('api/dashboard/', include('apps.dashboard.api_urls')),
]

# Servir media siempre (en modo escritorio DEBUG=False pero igual se necesitan las imágenes)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
