from django.contrib import admin
from .models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'employees', 'is_complete', 'created_at']
    list_filter = ['is_complete', 'created_at']
    search_fields = ['company_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'company_name', 'company_description_text')
        }),
        ('Filtros de Búsqueda', {
            'fields': ('sectors', 'employees', 'preferred_cpv_codes', 'preferred_nuts_regions', 'budget_range')
        }),
        ('Metadata', {
            'fields': ('is_complete', 'created_at', 'updated_at')
        }),
    )
