"""
URL configuration for TenderAI project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('auth/', include('apps.authentication.urls')),
    path('chat/', include('apps.chat.urls')),
    path('company/', include('apps.company.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # En desarrollo, Django sirve archivos estáticos automáticamente desde STATICFILES_DIRS
    # No necesitamos añadir static() para STATIC_URL en desarrollo
