from django.urls import path
from . import views

app_name = 'apps_company'

urlpatterns = [
    # Perfil del usuario/candidato
    path('', views.UserProfileView.as_view(), name='profile'),

    # Análisis de CV con IA (AJAX)
    path('analizar-cv/', views.AnalyzeCVView.as_view(), name='analyze_cv'),

    # Extracción de texto de PDF (AJAX)
    path('extraer-pdf/', views.ExtractPDFTextView.as_view(), name='extract_pdf'),

    # Autocompletado API
    path('api/autocomplete/locations/', views.AutocompleteLocationsView.as_view(), name='autocomplete_locations'),
    path('api/autocomplete/sectors/', views.AutocompleteSectorsView.as_view(), name='autocomplete_sectors'),
]
