"""
URL configuration for TenderAI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('licitaciones/', include('tenders.urls')),
    path('chat/', include('chat.urls')),
    path('empresa/', include('company.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # En desarrollo, Django sirve archivos estáticos automáticamente desde STATICFILES_DIRS
    # No necesitamos añadir static() para STATIC_URL en desarrollo
