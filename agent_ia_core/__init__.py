# -*- coding: utf-8 -*-
"""
Agent IA Core - Motor del agente inteligente para JobSearchAI Platform.

Estructura:
- tools/: Tools del agente (búsqueda empleo, análisis CV, LinkedIn)
- prompts/: System prompts
"""

from . import config
from .agent_function_calling import FunctionCallingAgent

__all__ = [
    'config',
    'FunctionCallingAgent',
]
