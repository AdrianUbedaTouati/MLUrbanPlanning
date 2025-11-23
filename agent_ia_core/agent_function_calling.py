# -*- coding: utf-8 -*-
"""
Agente con Function Calling para búsqueda de empleo.
Soporta Ollama, OpenAI y Google Gemini.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import logging
import json

sys.path.append(str(Path(__file__).parent))
from .tools.core.registry import ToolRegistry

# Imports de LLMs
try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FunctionCallingAgent:
    """
    Agente que usa Function Calling para búsqueda de empleo.
    """

    def __init__(
        self,
        llm_provider: str,
        llm_model: str,
        llm_api_key: Optional[str],
        user=None,
        max_iterations: int = 15,
        temperature: float = 0.3,
    ):
        """
        Inicializa el agente.

        Args:
            llm_provider: Proveedor ("ollama", "openai", "google")
            llm_model: Modelo específico
            llm_api_key: API key (no necesaria para Ollama)
            user: Usuario de Django
            max_iterations: Máximo de iteraciones del loop
            temperature: Temperatura del LLM
        """
        self.llm_provider = llm_provider.lower()
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.user = user

        # Validaciones
        if self.llm_provider not in ['ollama', 'openai', 'google']:
            raise ValueError(f"Proveedor '{llm_provider}' no soportado")

        if self.llm_provider != 'ollama' and not llm_api_key:
            raise ValueError(f"API key requerida para {llm_provider}")

        # Inicializar LLM
        logger.info(f"[AGENT] Inicializando {llm_provider} - {llm_model}")
        self.llm = self._create_llm()

        # Inicializar tool registry
        logger.info(f"[AGENT] Inicializando tool registry...")
        self.tool_registry = ToolRegistry(user=user, llm=self.llm)

        logger.info(f"[AGENT] Agente inicializado con {len(self.tool_registry.tools)} tools")

    def _create_llm(self):
        """Crea la instancia del LLM según el proveedor."""
        if self.llm_provider == 'ollama':
            if not ChatOllama:
                raise ImportError("langchain-ollama no instalado")

            return ChatOllama(
                model=self.llm_model,
                temperature=self.temperature,
                base_url="http://localhost:11434"
            )

        elif self.llm_provider == 'openai':
            if not ChatOpenAI:
                raise ImportError("langchain-openai no instalado")

            return ChatOpenAI(
                model=self.llm_model,
                temperature=self.temperature,
                openai_api_key=self.llm_api_key
            )

        elif self.llm_provider == 'google':
            if not ChatGoogleGenerativeAI:
                raise ImportError("langchain-google-genai no instalado")

            model_name = self.llm_model.replace("models/", "")

            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=self.temperature,
                google_api_key=self.llm_api_key
            )

    def query(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta una query con function calling.

        Args:
            question: Pregunta del usuario
            conversation_history: Historial de conversación previo

        Returns:
            Dict con answer, tools_used, iterations, metadata
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[QUERY] {question}")
        logger.info(f"{'='*80}\n")

        # Preparar mensajes
        messages = self._prepare_messages(question, conversation_history)

        # Loop de function calling
        iteration = 0
        tools_used = []
        tool_results_history = []

        # Determinar si es el primer mensaje
        is_first_message = not conversation_history or len(conversation_history) == 0

        # En el primer mensaje, cargar automáticamente el perfil del usuario
        if is_first_message and self.user and 'get_user_profile' in self.tool_registry.tools:
            logger.info("[QUERY] Primer mensaje - Cargando automáticamente perfil del usuario...")
            profile_result = self.tool_registry.execute_tool('get_user_profile')

            if profile_result.get('success'):
                tools_used.append('get_user_profile')
                tool_results_history.append({
                    'tool': 'get_user_profile',
                    'arguments': {},
                    'result': profile_result
                })

                # Añadir el perfil al contexto de mensajes
                profile_data = profile_result.get('data', {})
                if profile_data:
                    profile_summary = self._format_profile_summary(profile_data)
                    logger.info(f"[QUERY] ✓ Perfil del usuario cargado")
                    messages.append({
                        'role': 'system',
                        'content': f"CONTEXTO AUTOMÁTICO (perfil del usuario):\n\n{profile_summary}"
                    })
            else:
                logger.warning(f"[QUERY] ⚠️ Error al cargar perfil automático: {profile_result.get('error')}")

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"\n--- ITERACIÓN {iteration} ---")

            # Llamar al LLM con tools
            response = self._call_llm_with_tools(messages)

            # ¿Hay tool calls?
            tool_calls = response.get('tool_calls', [])

            if not tool_calls:
                # Respuesta final
                final_answer = response.get('content', '')
                logger.info(f"[ANSWER] Respuesta final generada")

                return {
                    'answer': final_answer,
                    'tools_used': tools_used,
                    'tool_results': tool_results_history,
                    'iterations': iteration,
                    'metadata': {
                        'provider': self.llm_provider,
                        'model': self.llm_model,
                    }
                }

            # Ejecutar tool calls
            logger.info(f"[TOOLS] LLM solicitó {len(tool_calls)} tool(s)")
            results = self.tool_registry.execute_tool_calls(tool_calls)

            # Registrar tools usadas
            for result in results:
                tool_name = result.get('tool')
                if tool_name and tool_name not in tools_used:
                    tools_used.append(tool_name)
                tool_results_history.append(result)

            # Añadir tool results al historial
            messages = self._add_tool_results_to_messages(
                messages, response, tool_calls, results
            )

        # Max iterations alcanzado
        logger.warning(f"[AGENT] Máximo de iteraciones alcanzado")

        return {
            'answer': 'Lo siento, no pude completar la búsqueda. Intenta ser más específico.',
            'tools_used': tools_used,
            'tool_results': tool_results_history,
            'iterations': iteration,
            'metadata': {
                'provider': self.llm_provider,
                'model': self.llm_model,
                'max_iterations_reached': True
            }
        }

    def _prepare_messages(
        self,
        question: str,
        conversation_history: Optional[List[Dict]]
    ) -> List[Dict]:
        """Prepara los mensajes para el LLM."""
        messages = []

        # System prompt para búsqueda de empleo
        system_prompt_parts = [
            "Eres un asistente experto en búsqueda de empleo y orientación profesional.",
            "Tu objetivo es ayudar a los usuarios a encontrar ofertas de trabajo, empresas y contactos de reclutadores.",
            "",
            "HERRAMIENTAS DISPONIBLES:",
            "- get_user_profile: Obtener el perfil profesional del usuario",
            "- search_jobs: Buscar ofertas de empleo (analiza muchas y devuelve las 10 mejores)",
            "- recommend_companies: Recomendar empresas con contactos de reclutadores y estrategia de acceso",
        ]

        # Si hay web search disponible
        if 'web_search' in self.tool_registry.tools:
            system_prompt_parts.extend([
                "- web_search: Buscar información actualizada en internet",
                "- browse_webpage: Navegar a una URL para extraer contenido",
            ])

        system_prompt_parts.extend([
            "",
            "INSTRUCCIONES IMPORTANTES:",
            "1. El perfil del usuario se carga automáticamente al inicio del chat",
            "2. Usa search_jobs para buscar las mejores ofertas de empleo",
            "3. Usa search_recent_jobs para buscar ofertas publicadas recientemente (últimas 24-48h)",
            "4. Usa recommend_companies para recomendar empresas con reclutadores",
            "5. Proporciona información práctica y actionable",
            "6. IMPORTANTE: Después de mostrar las 15 mejores ofertas con search_jobs, SIEMPRE pregunta al usuario si quiere ver las 15 ofertas más recientes",
            "",
            "FORMATO DE RESPUESTA:",
            "Presenta la información de forma visual y clara. Tienes libertad para elegir el formato que mejor se adapte:",
            "- Usa encabezados (## o ###) para separar secciones principales",
            "- Evita listas numeradas simples (1. 2. 3.) para las ofertas principales",
            "- Incluye SIEMPRE el link a cada oferta",
            "- Explica brevemente por qué cada oferta/empresa encaja con el usuario",
            "- Sé creativo con la presentación pero mantén la información esencial",
            "",
            "INFORMACIÓN ESENCIAL POR OFERTA:",
            "- Título/nombre del puesto (usa 'verified_details.title' si está disponible)",
            "- Empresa (usa 'verified_details.company' si está disponible)",
            "- Ubicación (usa 'verified_details.location' si está disponible)",
            "- Salario (usa 'verified_details.salary' si está disponible)",
            "- Por qué encaja con el perfil (usa 'fit_analysis' - debe ser ESPECÍFICO mencionando habilidades concretas)",
            "- Link directo a la oferta",
            "- Contacto del reclutador (si está disponible en 'recruiter': nombre y LinkedIn)",
            "- Estado de verificación (usa 'verification.confidence' para indicar si está verificada)",
            "",
            "EJEMPLOS DE USO:",
            '- "Busco trabajo en Alicante" → search_jobs(query="empleo", location="Alicante")',
            '- "Ofertas recientes de Python" → search_recent_jobs(query="Python")',
            '- "Recomiéndame empresas de tecnología" → recommend_companies(sector="Tecnología")',
            '- "Empresas que encajen conmigo en Madrid" → recommend_companies(location="Madrid")',
            "",
            "FLUJO RECOMENDADO:",
            "Cuando el usuario pida ofertas de empleo:",
            "1. Usa search_jobs para mostrar las 15 mejores ofertas",
            "2. Al final de la respuesta, pregunta: '¿Te gustaría ver las 15 ofertas más recientes publicadas en las últimas 24-48 horas?'",
            "3. Si acepta, usa search_recent_jobs con los mismos parámetros",
        ])

        system_prompt = "\n".join(system_prompt_parts)

        messages.append({
            'role': 'system',
            'content': system_prompt
        })

        # Añadir historial si existe
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })

        # Añadir pregunta actual
        messages.append({
            'role': 'user',
            'content': question
        })

        return messages

    def _call_llm_with_tools(self, messages: List[Dict]) -> Dict[str, Any]:
        """Llama al LLM con las tools disponibles."""
        if self.llm_provider == 'ollama':
            return self._call_ollama_with_tools(messages)
        elif self.llm_provider == 'openai':
            return self._call_openai_with_tools(messages)
        elif self.llm_provider == 'google':
            return self._call_gemini_with_tools(messages)

    def _call_ollama_with_tools(self, messages: List[Dict]) -> Dict[str, Any]:
        """Llama a Ollama con function calling."""
        import ollama

        try:
            response = ollama.chat(
                model=self.llm_model,
                messages=messages,
                tools=self.tool_registry.get_ollama_tools()
            )

            message = response.get('message', {})

            return {
                'content': message.get('content', ''),
                'tool_calls': message.get('tool_calls', [])
            }

        except Exception as e:
            logger.error(f"[OLLAMA] Error: {e}", exc_info=True)
            return {
                'content': f'Error con Ollama: {str(e)}',
                'tool_calls': []
            }

    def _call_openai_with_tools(self, messages: List[Dict]) -> Dict[str, Any]:
        """Llama a OpenAI con function calling."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        try:
            lc_messages = []
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content', '')

                if role == 'system':
                    lc_messages.append(SystemMessage(content=content))
                elif role == 'user':
                    lc_messages.append(HumanMessage(content=content))
                elif role == 'assistant':
                    tool_calls = msg.get('tool_calls', [])
                    if tool_calls:
                        formatted_tool_calls = []
                        for tc in tool_calls:
                            func = tc.get('function', {})
                            tc_id = tc.get('id', f"call_{func.get('name')}_{id(tc)}")
                            formatted_tool_calls.append({
                                "name": func.get('name'),
                                "args": func.get('arguments', {}),
                                "id": tc_id
                            })
                        lc_messages.append(AIMessage(content=content, tool_calls=formatted_tool_calls))
                    else:
                        lc_messages.append(AIMessage(content=content))
                elif role == 'tool':
                    tool_call_id = msg.get('tool_call_id', 'default')
                    lc_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))

            tools = self.tool_registry.get_openai_tools()
            llm_with_tools = self.llm.bind_tools(tools)
            response = llm_with_tools.invoke(lc_messages)

            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        'id': tc.get('id', f"call_{tc.get('name')}_{id(tc)}"),
                        'function': {
                            'name': tc.get('name'),
                            'arguments': tc.get('args', {})
                        }
                    })

            return {
                'content': response.content if hasattr(response, 'content') else '',
                'tool_calls': tool_calls
            }

        except Exception as e:
            logger.error(f"[OPENAI] Error: {e}", exc_info=True)
            return {
                'content': f'Error con OpenAI: {str(e)}',
                'tool_calls': []
            }

    def _call_gemini_with_tools(self, messages: List[Dict]) -> Dict[str, Any]:
        """Llama a Gemini con function calling."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        try:
            lc_messages = []
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content', '')

                if role == 'system':
                    lc_messages.append(SystemMessage(content=content))
                elif role == 'user':
                    lc_messages.append(HumanMessage(content=content))
                elif role == 'assistant':
                    tool_calls = msg.get('tool_calls', [])
                    if tool_calls:
                        formatted_tool_calls = []
                        for tc in tool_calls:
                            func = tc.get('function', {})
                            tc_id = tc.get('id', f"call_{func.get('name')}_{id(tc)}")
                            formatted_tool_calls.append({
                                "name": func.get('name'),
                                "args": func.get('arguments', {}),
                                "id": tc_id
                            })
                        lc_messages.append(AIMessage(content=content, tool_calls=formatted_tool_calls))
                    else:
                        lc_messages.append(AIMessage(content=content))
                elif role == 'tool':
                    tool_call_id = msg.get('tool_call_id', 'default')
                    lc_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))

            tools = self.tool_registry.get_gemini_tools()
            llm_with_tools = self.llm.bind_tools(tools)
            response = llm_with_tools.invoke(lc_messages)

            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        'id': tc.get('id', f"call_{tc.get('name')}_{id(tc)}"),
                        'function': {
                            'name': tc.get('name'),
                            'arguments': tc.get('args', {})
                        }
                    })

            return {
                'content': response.content if hasattr(response, 'content') else '',
                'tool_calls': tool_calls
            }

        except Exception as e:
            logger.error(f"[GEMINI] Error: {e}", exc_info=True)
            return {
                'content': f'Error con Gemini: {str(e)}',
                'tool_calls': []
            }

    def _add_tool_results_to_messages(
        self,
        messages: List[Dict],
        llm_response: Dict,
        tool_calls: List[Dict],
        tool_results: List[Dict]
    ) -> List[Dict]:
        """Añade los resultados de las tools al historial."""

        messages.append({
            'role': 'assistant',
            'content': llm_response.get('content', ''),
            'tool_calls': tool_calls
        })

        for idx, result in enumerate(tool_results):
            tool_call_id = "default"
            if idx < len(tool_calls):
                tool_call_id = tool_calls[idx].get('id', f"call_{result.get('tool', 'unknown')}_{idx}")

            messages.append({
                'role': 'tool',
                'content': json.dumps(result, ensure_ascii=False),
                'tool_call_id': tool_call_id
            })

        return messages

    def _format_profile_summary(self, profile_data: Dict[str, Any]) -> str:
        """
        Formatea el perfil del usuario para el contexto.

        Args:
            profile_data: Datos del perfil del usuario

        Returns:
            Resumen formateado del perfil
        """
        parts = []

        if profile_data.get('full_name'):
            parts.append(f"Nombre: {profile_data['full_name']}")

        if profile_data.get('title'):
            parts.append(f"Título profesional: {profile_data['title']}")

        if profile_data.get('location'):
            parts.append(f"Ubicación: {profile_data['location']}")

        if profile_data.get('preferred_location'):
            parts.append(f"Ubicación preferida para trabajo: {profile_data['preferred_location']}")

        if profile_data.get('skills'):
            skills = profile_data['skills']
            if isinstance(skills, list):
                parts.append(f"Habilidades: {', '.join(skills)}")
            else:
                parts.append(f"Habilidades: {skills}")

        if profile_data.get('experience'):
            parts.append(f"Experiencia: {profile_data['experience']}")

        if profile_data.get('education'):
            parts.append(f"Educación: {profile_data['education']}")

        if profile_data.get('preferred_sectors'):
            sectors = profile_data['preferred_sectors']
            if isinstance(sectors, list):
                parts.append(f"Sectores de interés: {', '.join(sectors)}")
            else:
                parts.append(f"Sectores de interés: {sectors}")

        if profile_data.get('job_type'):
            parts.append(f"Tipo de trabajo buscado: {profile_data['job_type']}")

        if profile_data.get('salary_expectation'):
            parts.append(f"Expectativa salarial: {profile_data['salary_expectation']}")

        # Incluir curriculum completo si está disponible
        if profile_data.get('curriculum_text'):
            parts.append(f"\nCURRICULUM/CV:\n{profile_data['curriculum_text']}")

        if not parts:
            return "Perfil del usuario no completado. Sugiere que complete su perfil para mejores recomendaciones."

        return "\n".join(parts)
