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
        super().__init__()

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

            # Retornar solo el texto del CV
            return {
                'success': True,
                'data': profile.curriculum_text
            }

        except Exception as e:
            logger.error(f"Error obteniendo CV completo: {e}")
            return {
                'success': False,
                'error': f'Error al obtener el CV: {str(e)}'
            }

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }
