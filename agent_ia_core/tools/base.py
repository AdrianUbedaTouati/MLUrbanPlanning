# -*- coding: utf-8 -*-
"""
Clase base para todas las tools del sistema de Function Calling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Clase base abstracta para todas las tools.

    Cada tool debe:
    1. Definir name y description
    2. Implementar run() para ejecutar la acción
    3. Implementar get_schema() para definir los parámetros
    """

    # Cada subclase debe definir estos atributos
    name: str = None
    description: str = None

    def __init__(self):
        """Inicializa la tool."""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} debe definir 'name'")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} debe definir 'description'")

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la tool con los parámetros dados.

        Args:
            **kwargs: Parámetros específicos de cada tool

        Returns:
            Dict con el resultado de la ejecución
            Formato estándar: {'success': bool, 'data': Any, 'error': str (opcional)}
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Retorna el schema de la tool en formato OpenAI Function Calling.

        Returns:
            Dict con estructura:
            {
                'name': str,
                'description': str,
                'parameters': {
                    'type': 'object',
                    'properties': {...},
                    'required': [...]
                }
            }
        """
        pass

    def to_ollama_tool(self) -> Dict[str, Any]:
        """
        Convierte el schema a formato de Ollama.

        Returns:
            Dict en formato Ollama:
            {
                'type': 'function',
                'function': {...schema...}
            }
        """
        return {
            'type': 'function',
            'function': self.get_schema()
        }

    def execute_safe(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la tool con manejo de errores.

        Args:
            **kwargs: Parámetros de la tool

        Returns:
            Dict con resultado o error
        """
        try:
            logger.info(f"[TOOL] Ejecutando {self.name} con args: {kwargs}")
            result = self.run(**kwargs)
            logger.info(f"[TOOL] {self.name} completado exitosamente")
            return result
        except Exception as e:
            logger.error(f"[TOOL] Error en {self.name}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error ejecutando {self.name}: {str(e)}'
            }

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"
