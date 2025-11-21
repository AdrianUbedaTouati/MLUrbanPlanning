# -*- coding: utf-8 -*-
"""
Agent IA Core - Motor del agente inteligente para TenderAI Platform.

Estructura:
- parser/: XML parsing y chunking
- prompts/: System prompts
- indexing/: RAG retrieval e indexacion
- tools/: Tools del agente
- download/: Descarga de licitaciones TED
- engines/: Motores especializados (recomendaciones)
"""

from . import config

# Re-exports for backward compatibility
from .agent_function_calling import FunctionCallingAgent
from .parser import EFormsXMLParser, chunk_eforms_record, XmlLookupTool
from .indexing import HybridRetriever, create_retriever, build_index
from .download import TokenTracker

__all__ = [
    'config',
    'FunctionCallingAgent',
    'EFormsXMLParser',
    'chunk_eforms_record',
    'XmlLookupTool',
    'HybridRetriever',
    'create_retriever',
    'build_index',
    'TokenTracker'
]
