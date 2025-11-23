# -*- coding: utf-8 -*-
"""
Registro central de todas las tools disponibles para búsqueda de empleo.
"""

from typing import Dict, List, Any, Optional
from .base import BaseTool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registro central que mantiene todas las tools disponibles.
    """

    def __init__(self, user=None, llm=None):
        """
        Inicializa el registro con todas las tools.

        Args:
            user: Usuario de Django
            llm: Instancia del LLM para tools que lo necesiten
        """
        self.user = user
        self.llm = llm
        self.tools: Dict[str, BaseTool] = {}
        self._register_all_tools()

    def _register_all_tools(self):
        """Registra todas las tools disponibles."""
        logger.info("[REGISTRY] Registrando tools de búsqueda de empleo...")

        from ..agent_tools.get_user_profile import GetUserProfileTool
        from ..agent_tools.get_full_cv import GetFullCVTool
        from ..agent_tools.search_jobs import JobSearchTool, SearchRecentJobsTool
        from ..agent_tools.recommend_companies import CompanyRecommendationTool

        # Tools de contexto (solo si hay usuario)
        if self.user:
            self.tools['get_user_profile'] = GetUserProfileTool(self.user)
            self.tools['get_full_cv'] = GetFullCVTool(self.user)
            logger.info("[REGISTRY] ✓ Tools de contexto registradas")

        # Web search tool (necesaria para búsquedas)
        web_search_tool = None
        browse_tool = None

        if self.user:
            # Web Search con Google Custom Search API
            if getattr(self.user, 'use_web_search', False):
                google_search_api_key = getattr(self.user, 'google_search_api_key', None)
                google_search_engine_id = getattr(self.user, 'google_search_engine_id', None)

                if google_search_api_key and google_search_engine_id:
                    from ..agent_tools.web_search import GoogleWebSearchTool
                    web_search_tool = GoogleWebSearchTool(
                        api_key=google_search_api_key,
                        engine_id=google_search_engine_id
                    )
                    self.tools['web_search'] = web_search_tool
                    logger.info("[REGISTRY] ✓ Web search tool habilitada")

                    # Browse Webpage
                    from ..agent_tools.browse_webpage import BrowseWebpageTool
                    browse_max_chars = getattr(self.user, 'browse_max_chars', 10000)
                    browse_chunk_size = getattr(self.user, 'browse_chunk_size', 1250)
                    browse_tool = BrowseWebpageTool(
                        default_max_chars=browse_max_chars,
                        default_chunk_size=browse_chunk_size
                    )
                    self.tools['browse_webpage'] = browse_tool
                    logger.info("[REGISTRY] ✓ Browse webpage tool habilitada")

        # Obtener perfil de usuario para tools que lo necesiten
        user_profile = None
        if self.user:
            try:
                from apps.company.models import UserProfile
                profile = UserProfile.objects.filter(user=self.user).first()
                if profile:
                    user_profile = profile.to_agent_format()
                else:
                    user_profile = {}

                # Añadir datos del modelo User (ciudad, modalidad de trabajo)
                if hasattr(self.user, 'city') and self.user.city:
                    user_profile['city'] = self.user.city
                    # También añadir a preferred_locations si no existe
                    if 'preferred_locations' not in user_profile or not user_profile['preferred_locations']:
                        user_profile['preferred_locations'] = [self.user.city]

                if hasattr(self.user, 'work_mode') and self.user.work_mode:
                    user_profile['work_mode'] = self.user.work_mode
                    # Mapear a texto legible
                    work_mode_map = {
                        'any': 'Indiferente',
                        'remote': 'Remoto',
                        'onsite': 'Presencial',
                        'hybrid': 'Híbrido'
                    }
                    user_profile['work_mode_text'] = work_mode_map.get(self.user.work_mode, 'Indiferente')

            except Exception as e:
                logger.warning(f"No se pudo obtener perfil de usuario: {e}")

        # Tool de búsqueda de ofertas
        self.tools['search_jobs'] = JobSearchTool(
            llm=self.llm,
            web_search_tool=web_search_tool,
            browse_tool=browse_tool,
            user_profile=user_profile
        )
        logger.info("[REGISTRY] ✓ Tool search_jobs registrada")

        # Tool de búsqueda de ofertas recientes
        self.tools['search_recent_jobs'] = SearchRecentJobsTool(
            llm=self.llm,
            web_search_tool=web_search_tool,
            browse_tool=browse_tool,
            user_profile=user_profile
        )
        logger.info("[REGISTRY] ✓ Tool search_recent_jobs registrada")

        # Tool de recomendación de empresas (incluye reclutadores y estrategia)
        self.tools['recommend_companies'] = CompanyRecommendationTool(
            llm=self.llm,
            web_search_tool=web_search_tool,
            browse_tool=browse_tool,
            user_profile=user_profile
        )
        logger.info("[REGISTRY] ✓ Tool recommend_companies registrada")

        logger.info(f"[REGISTRY] {len(self.tools)} tools registradas: {list(self.tools.keys())}")

    def set_llm(self, llm):
        """
        Actualiza el LLM en todas las tools que lo necesiten.
        """
        self.llm = llm

        # Actualizar LLM en tools
        for tool_name, tool in self.tools.items():
            if hasattr(tool, 'llm'):
                tool.llm = llm

        logger.info("[REGISTRY] LLM actualizado en todas las tools")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Obtiene una tool por nombre."""
        return self.tools.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Obtiene todas las tools."""
        return self.tools.copy()

    def get_tool_names(self) -> List[str]:
        """Obtiene nombres de todas las tools."""
        return list(self.tools.keys())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Obtiene schemas de todas las tools en formato OpenAI."""
        return [tool.get_schema() for tool in self.tools.values()]

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """Obtiene todas las tools en formato Ollama."""
        return [tool.to_ollama_tool() for tool in self.tools.values()]

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """Ejecuta una tool por nombre."""
        tool = self.get_tool(name)

        if not tool:
            logger.error(f"[REGISTRY] Tool '{name}' no encontrada")
            return {
                'success': False,
                'error': f"Tool '{name}' no existe. Tools disponibles: {self.get_tool_names()}"
            }

        # Inyectar LLM si es necesario
        if name == 'browse_webpage' and self.llm:
            kwargs['llm'] = self.llm

        logger.info(f"[REGISTRY] Ejecutando tool '{name}'...")
        return tool.execute_safe(**kwargs)

    def execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """Ejecuta múltiples tool calls."""
        results = []

        for tool_call in tool_calls:
            function = tool_call.get('function', {})
            name = function.get('name')
            arguments = function.get('arguments', {})

            if not name:
                results.append({
                    'success': False,
                    'error': 'Tool call sin nombre'
                })
                continue

            result = self.execute_tool(name, **arguments)
            results.append({
                'tool': name,
                'arguments': arguments,
                'result': result
            })

        return results

    def __repr__(self):
        return f"<ToolRegistry({len(self.tools)} tools)>"

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Obtiene todas las tools en formato OpenAI."""
        from .schema_converters import SchemaConverter
        return [SchemaConverter.to_openai_format(tool.get_schema()) for tool in self.tools.values()]

    def get_gemini_tools(self) -> List[Dict[str, Any]]:
        """Obtiene todas las tools en formato Google Gemini."""
        from .schema_converters import SchemaConverter
        return [SchemaConverter.to_gemini_format(tool.get_schema()) for tool in self.tools.values()]

    def get_tools_for_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Obtiene todas las tools en el formato del proveedor especificado."""
        if provider == "ollama":
            return self.get_ollama_tools()
        elif provider == "openai":
            return self.get_openai_tools()
        elif provider == "google":
            return self.get_gemini_tools()
        else:
            logger.warning(f"Proveedor desconocido: {provider}, usando formato Ollama")
            return self.get_ollama_tools()
