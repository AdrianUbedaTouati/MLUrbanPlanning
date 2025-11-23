# -*- coding: utf-8 -*-
"""
Tools para obtener información de contexto del usuario:
- Perfil del candidato
- Historial de búsquedas
"""

from typing import Dict, Any
import logging
from ..core.base import BaseTool

logger = logging.getLogger(__name__)


class GetUserProfileTool(BaseTool):
    """
    Tool para obtener la información del perfil del usuario/candidato.
    """

    name = "get_user_profile"
    description = (
        "Obtiene información sobre el perfil profesional del usuario. "
        "**IMPORTANTE: USA ESTA TOOL SIEMPRE que el usuario pida recomendaciones personalizadas** "
        "(ej: 'busca trabajo para mí', 'qué ofertas me convienen', 'empresas que encajen conmigo'). "
        "Devuelve: nombre, habilidades, experiencia, formación, idiomas, ubicación preferida, "
        "sectores de interés, expectativa salarial. "
        "Con esta información puedes hacer búsquedas personalizadas y justificar recomendaciones."
    )

    def __init__(self, user):
        super().__init__()
        self.user = user

    def run(self, **kwargs) -> Dict[str, Any]:
        """Obtiene información del perfil del usuario."""
        try:
            from apps.company.models import UserProfile

            profile = UserProfile.objects.filter(user=self.user).first()

            if not profile:
                return {
                    'success': False,
                    'data': None,
                    'error': 'El usuario no tiene un perfil configurado. Debe completar su CV primero.'
                }

            # Obtener contexto formateado
            profile_context = profile.get_chat_context()

            # Datos estructurados
            profile_data = profile.to_agent_format()

            return {
                'success': True,
                'data': {
                    'formatted_context': profile_context,
                    'structured_data': profile_data,
                    'cv_analyzed': profile.cv_analyzed,
                    'is_complete': profile.is_complete
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo perfil de usuario: {e}")
            return {
                'success': False,
                'data': None,
                'error': f'Error al obtener perfil: {str(e)}'
            }

    def get_schema(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': []
            }
        }


class GetSearchHistoryTool(BaseTool):
    """
    Tool para obtener el historial de búsquedas del usuario.
    """

    name = "get_search_history"
    description = (
        "Obtiene el historial de búsquedas de empleo del usuario. "
        "Útil para entender qué tipo de trabajos ha buscado anteriormente "
        "y evitar repetir búsquedas."
    )

    def __init__(self, user):
        super().__init__()
        self.user = user

    def run(self, limit: int = 10) -> Dict[str, Any]:
        """Obtiene historial de búsquedas."""
        try:
            from apps.chat.models import ChatSession, ChatMessage

            # Obtener últimas sesiones de chat
            sessions = ChatSession.objects.filter(
                user=self.user
            ).order_by('-created_at')[:limit]

            if not sessions.exists():
                return {
                    'success': True,
                    'data': {
                        'message': 'No hay historial de búsquedas previas.',
                        'sessions': []
                    }
                }

            history = []
            for session in sessions:
                # Obtener primer mensaje (pregunta del usuario)
                first_message = ChatMessage.objects.filter(
                    session=session,
                    role='user'
                ).first()

                if first_message:
                    history.append({
                        'date': session.created_at.strftime('%Y-%m-%d %H:%M'),
                        'query': first_message.content[:100],
                        'title': session.title
                    })

            return {
                'success': True,
                'data': {
                    'sessions': history,
                    'total': len(history)
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }

    def get_schema(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'limit': {
                        'type': 'integer',
                        'description': 'Número máximo de búsquedas a retornar',
                        'default': 10
                    }
                },
                'required': []
            }
        }
