from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'location', 'is_complete', 'cv_analyzed', 'created_at']
    list_filter = ['is_complete', 'cv_analyzed', 'created_at']
    search_fields = ['full_name', 'user__email', 'location']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Información Personal', {
            'fields': ('user', 'full_name', 'phone', 'location')
        }),
        ('Curriculum', {
            'fields': ('curriculum_text', 'curriculum_file', 'professional_summary')
        }),
        ('Datos Extraídos por IA', {
            'fields': ('skills', 'experience', 'education', 'languages'),
            'classes': ('collapse',)
        }),
        ('Preferencias de Búsqueda', {
            'fields': ('preferred_locations', 'preferred_sectors', 'job_types',
                      'contract_types', 'salary_min', 'salary_max', 'availability')
        }),
        ('Redes Profesionales', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Metadata', {
            'fields': ('is_complete', 'cv_analyzed', 'created_at', 'updated_at')
        }),
    )
