from django.urls import path
from . import views

app_name = 'apps_core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfil/', views.edit_profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    # Ollama verification
    path('ollama/check/', views.ollama_check_view, name='ollama_check'),
    path('ollama/test/', views.ollama_test_api, name='ollama_test'),
    path('ollama/models/', views.ollama_models_api, name='ollama_models'),
    # CV Analysis
    path('profile/analyze-cv/', views.analyze_cv_image_view, name='analyze_cv'),
    path('profile/analyze-cv/ajax/', views.analyze_cv_ajax_view, name='analyze_cv_ajax'),
    path('profile/save-cv-text/', views.save_cv_text_view, name='save_cv_text'),
    path('profile/save-preferences/', views.save_preferences_view, name='save_preferences'),
    path('profile/save-social/', views.save_social_view, name='save_social'),
]