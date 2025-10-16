from django.db import models
from django.conf import settings


class CompanyProfile(models.Model):
    """Perfil de empresa para búsqueda de licitaciones"""

    # Relación OneToOne con User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_profile'
    )

    # ============================================
    # INFORMACIÓN BÁSICA
    # ============================================
    company_name = models.CharField(
        max_length=200,
        verbose_name='Nombre de la empresa'
    )

    # Descripción libre - Se pasa al chat como contexto inicial
    company_description_text = models.TextField(
        blank=True,
        verbose_name='Cuéntanos sobre tu empresa',
        help_text='Describe tu empresa: qué hacéis, en qué sectores trabajáis, ubicación, etc. Esta información ayudará a encontrar las licitaciones más relevantes.'
    )

    # ============================================
    # CAMPOS PARA FILTRADO Y BÚSQUEDA
    # ============================================

    # Sectores de actividad (tags)
    sectors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Sectores',
        help_text='Ej: Tecnología, Construcción, Consultoría'
    )

    # Número de empleados
    employees = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Número de empleados'
    )

    # Códigos CPV preferidos (tags)
    preferred_cpv_codes = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Códigos CPV de interés',
        help_text='Códigos CPV relacionados con tu actividad'
    )

    # Regiones NUTS preferidas (tags)
    preferred_nuts_regions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Regiones de interés (NUTS)',
        help_text='Ej: ES30 (Madrid), ES51 (Barcelona)'
    )

    # Rango de presupuesto
    budget_range = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Rango de presupuesto',
        help_text='{"min": 50000, "max": 500000}'
    )

    # ============================================
    # METADATOS
    # ============================================
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Empresa'
        verbose_name_plural = 'Perfiles de Empresas'

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"

    def to_agent_format(self):
        """
        Convierte el perfil al formato esperado por Agent_IA.
        Solo incluye los campos relevantes para búsqueda y filtrado.
        """
        return {
            "company_name": self.company_name,
            "description": self.company_description_text,
            "sectors": self.sectors,
            "employees": self.employees,
            "preferred_cpv_codes": self.preferred_cpv_codes,
            "preferred_nuts_regions": self.preferred_nuts_regions,
            "budget_range": self.budget_range or {"min": 50000, "max": 500000},
        }

    def get_chat_context(self):
        """
        Devuelve el contexto de empresa para el chat.
        Este método usa la configuración de prompts centralizada.
        """
        from agent_ia_core.prompts_config import format_company_context
        return format_company_context(self)
