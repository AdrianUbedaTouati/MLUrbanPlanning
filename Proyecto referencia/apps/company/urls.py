from django.urls import path
from . import views

app_name = 'apps_company'

urlpatterns = [
    # Perfil de empresa (edición y visualización)
    path('perfil/', views.CompanyProfileView.as_view(), name='profile'),

    # Extracción de información con IA (AJAX)
    path('perfil/extraer-info/', views.ExtractCompanyInfoView.as_view(), name='extract_info'),

    # Autocompletado API
    path('api/autocomplete/nuts/', views.AutocompleteNUTSView.as_view(), name='autocomplete_nuts'),
    path('api/autocomplete/cpv/', views.AutocompleteCPVView.as_view(), name='autocomplete_cpv'),
]
