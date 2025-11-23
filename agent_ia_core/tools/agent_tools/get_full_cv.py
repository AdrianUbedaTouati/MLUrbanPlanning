# -*- coding: utf-8 -*-
"""
Tool para obtener el CV completo del usuario.
"""

from ..core.base import BaseTool
import logging

logger = logging.getLogger(__name__)


class GetFullCVTool(BaseTool):
    """
    Obtiene el curriculum vitae completo del usuario.
    Usar cuando se necesite información detallada del CV.
    """

    name = "get_full_cv"
    description = "Obtiene el CV completo del usuario con toda la información detallada (experiencia, formación, habilidades, etc.)"

    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, user):
        self.user = user

    def run(self) -> dict:
        """Retorna el CV completo del usuario."""

        try:
            from apps.company.models import UserProfile

            profile = UserProfile.objects.filter(user=self.user).first()

            if not profile:
                return {
                    'success': False,
                    'error': 'No tienes un perfil creado. Sube tu CV en la sección de configuración.'
                }

            if not profile.curriculum_text:
                return {
                    'success': False,
                    'error': 'No tienes un CV guardado. Sube tu CV en la sección de configuración.'
                }

            # Retornar CV completo
            return {
                'success': True,
                'data': {
                    'curriculum_text': profile.curriculum_text,
                    'full_name': profile.full_name,
                    'location': profile.location,
                    'phone': profile.phone,
                    'skills': profile.skills,
                    'experience': profile.experience,
                    'education': profile.education,
                    'languages': profile.languages,
                    'professional_summary': profile.professional_summary,
                    'linkedin_url': profile.linkedin_url,
                    'github_url': profile.github_url,
                    'portfolio_url': profile.portfolio_url,
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo CV completo: {e}")
            return {
                'success': False,
                'error': f'Error al obtener el CV: {str(e)}'
            }
