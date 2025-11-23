from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """Perfil de usuario para búsqueda de empleo"""

    # Relación OneToOne con User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_profile'
    )

    # ============================================
    # INFORMACIÓN PERSONAL
    # ============================================
    full_name = models.CharField(
        max_length=200,
        verbose_name='Nombre completo'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ciudad/Provincia',
        help_text='Ej: Alicante, Madrid, Barcelona'
    )

    # ============================================
    # CURRICULUM VITAE
    # ============================================
    # CV en texto - para análisis por IA
    curriculum_text = models.TextField(
        blank=True,
        verbose_name='Curriculum en texto',
        help_text='Pega aquí tu CV o descríbete profesionalmente. La IA analizará esta información.'
    )

    # CV en archivo PDF
    curriculum_file = models.FileField(
        upload_to='curriculos/',
        blank=True,
        null=True,
        verbose_name='CV en PDF'
    )

    # CV en imagen (para análisis con Vision API)
    cv_image = models.ImageField(
        upload_to='cv_images/',
        blank=True,
        null=True,
        verbose_name='CV en imagen',
        help_text='Sube una imagen de tu CV para análisis con IA Vision'
    )

    # ============================================
    # DATOS EXTRAÍDOS POR IA
    # ============================================
    # Habilidades extraídas del CV
    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Habilidades',
        help_text='Habilidades técnicas y blandas extraídas del CV'
    )

    # Experiencia laboral estructurada
    experience = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Experiencia laboral',
        help_text='[{"company": "", "position": "", "duration": "", "description": ""}]'
    )

    # Formación académica
    education = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Formación',
        help_text='[{"institution": "", "degree": "", "year": ""}]'
    )

    # Idiomas
    languages = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Idiomas',
        help_text='[{"language": "", "level": ""}]'
    )

    # Resumen profesional generado por IA
    professional_summary = models.TextField(
        blank=True,
        verbose_name='Resumen profesional',
        help_text='Resumen generado por IA basado en el CV'
    )

    # Resumen estructurado del CV para búsquedas
    cv_summary = models.TextField(
        blank=True,
        verbose_name='Resumen CV estructurado',
        help_text='Resumen optimizado para búsqueda de empleo'
    )

    # ============================================
    # PREFERENCIAS DE BÚSQUEDA
    # ============================================
    # Ubicaciones preferidas para trabajar
    preferred_locations = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Ubicaciones preferidas',
        help_text='Ej: ["Alicante", "Valencia", "Remoto"]'
    )

    # Sectores de interés
    preferred_sectors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Sectores de interés',
        help_text='Ej: ["Informática/IT", "Marketing"]'
    )

    # Tipos de trabajo
    job_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Tipos de trabajo',
        help_text='Ej: ["Remoto", "Presencial", "Híbrido"]'
    )

    # Tipos de contrato
    contract_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Tipos de contrato',
        help_text='Ej: ["Indefinido", "Temporal", "Freelance"]'
    )

    # Expectativa salarial
    salary_min = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Salario mínimo (€/año)'
    )

    salary_max = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Salario máximo (€/año)'
    )

    # Disponibilidad
    availability = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Disponibilidad',
        help_text='Ej: Inmediata, 15 días, 1 mes'
    )

    # ============================================
    # REDES PROFESIONALES
    # ============================================
    linkedin_url = models.URLField(
        blank=True,
        verbose_name='Perfil de LinkedIn'
    )

    github_url = models.URLField(
        blank=True,
        verbose_name='Perfil de GitHub'
    )

    portfolio_url = models.URLField(
        blank=True,
        verbose_name='Portfolio/Web personal'
    )

    # ============================================
    # METADATOS
    # ============================================
    is_complete = models.BooleanField(default=False)
    cv_analyzed = models.BooleanField(
        default=False,
        verbose_name='CV analizado por IA'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

    def to_agent_format(self):
        """
        Convierte el perfil al formato esperado por el Agente IA.
        """
        return {
            "full_name": self.full_name,
            "location": self.location,
            "phone": self.phone,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "languages": self.languages,
            "professional_summary": self.professional_summary,
            "preferred_locations": self.preferred_locations,
            "preferred_sectors": self.preferred_sectors,
            "job_types": self.job_types,
            "contract_types": self.contract_types,
            "salary_range": {
                "min": self.salary_min,
                "max": self.salary_max
            },
            "availability": self.availability,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "portfolio_url": self.portfolio_url,
            "curriculum_text": self.curriculum_text if self.curriculum_text else None,
        }

    def get_chat_context(self):
        """
        Devuelve el contexto del usuario para el chat.
        """
        context = f"Perfil del candidato: {self.full_name}\n"

        if self.location:
            context += f"Ubicación: {self.location}\n"

        if self.professional_summary:
            context += f"Resumen: {self.professional_summary}\n"

        if self.skills:
            context += f"Habilidades: {', '.join(self.skills)}\n"

        if self.preferred_locations:
            context += f"Busca trabajo en: {', '.join(self.preferred_locations)}\n"

        if self.preferred_sectors:
            context += f"Sectores de interés: {', '.join(self.preferred_sectors)}\n"

        if self.salary_min or self.salary_max:
            salary = ""
            if self.salary_min:
                salary += f"{self.salary_min}€"
            if self.salary_max:
                salary += f" - {self.salary_max}€"
            context += f"Expectativa salarial: {salary}/año\n"

        return context

    def check_completeness(self):
        """
        Verifica si el perfil tiene la información mínima necesaria.
        """
        required_fields = [
            self.full_name,
            self.location or self.preferred_locations,
            self.skills or self.curriculum_text,
        ]
        self.is_complete = all(required_fields)
        return self.is_complete
