"""
Service layer for integrating Job Search Agent with Chat functionality
"""
import os
import sys
from typing import Dict, Any, List
from django.conf import settings

# Add agent_ia_core to Python path
agent_ia_path = os.path.join(settings.BASE_DIR, 'agent_ia_core')
if agent_ia_path not in sys.path:
    sys.path.insert(0, agent_ia_path)


class ChatAgentService:
    """Service to interact with the Job Search Agent"""

    def __init__(self, user, session_id=None):
        """
        Initialize the chat agent service

        Args:
            user: Django User instance with llm_api_key, llm_provider, etc.
            session_id: Optional session ID for logging purposes
        """
        self.user = user
        self.api_key = user.llm_api_key if hasattr(user, 'llm_api_key') else None
        self.provider = user.llm_provider if hasattr(user, 'llm_provider') else 'google'
        self.openai_model = user.openai_model if hasattr(user, 'openai_model') else 'gpt-4o-mini'
        self.ollama_model = user.ollama_model if hasattr(user, 'ollama_model') else 'qwen2.5:7b'
        self._agent = None
        self._reviewer = None

    def _get_agent(self):
        """
        Initialize and return FunctionCallingAgent
        """
        if self._agent is not None:
            return self._agent

        # Ollama doesn't need API key
        if not self.api_key and self.provider != 'ollama':
            raise ValueError("No API key configured for user")

        return self._create_agent()

    def _create_agent(self):
        """
        Create and return a FunctionCallingAgent instance
        """
        try:
            from agent_ia_core.agent_function_calling import FunctionCallingAgent

            print(f"[SERVICE] Creando FunctionCallingAgent...", file=sys.stderr)
            print(f"[SERVICE] Proveedor: {self.provider}", file=sys.stderr)

            # Verificar Ollama si es necesario
            if self.provider == 'ollama':
                self._verify_ollama_availability()

            # Determinar el modelo según el proveedor
            if self.provider == 'ollama':
                model = self.ollama_model
            elif self.provider == 'openai':
                model = self.openai_model
            elif self.provider == 'google':
                model = 'gemini-2.0-flash-exp'
            else:
                model = self.ollama_model

            # Crear agente
            self._agent = FunctionCallingAgent(
                llm_provider=self.provider,
                llm_model=model,
                llm_api_key=None if self.provider == 'ollama' else self.api_key,
                user=self.user,
                max_iterations=15,
                temperature=0.3,
            )

            print(f"[SERVICE] ✓ FunctionCallingAgent creado con {len(self._agent.tool_registry.tools)} tools", file=sys.stderr)
            return self._agent

        except Exception as e:
            raise Exception(f"Error creating FunctionCallingAgent: {e}")

    def _get_reviewer(self):
        """
        Initialize and return ResponseReviewer
        """
        if self._reviewer is not None:
            return self._reviewer

        try:
            from .response_reviewer import ResponseReviewer

            # Usar el mismo LLM del agente
            agent = self._get_agent()
            self._reviewer = ResponseReviewer(llm=agent.llm)
            print(f"[SERVICE] ✓ ResponseReviewer inicializado", file=sys.stderr)
            return self._reviewer

        except Exception as e:
            print(f"[SERVICE] ⚠ Error inicializando ResponseReviewer: {e}", file=sys.stderr)
            return None

    def _verify_ollama_availability(self):
        """
        Verify Ollama is running and model is available
        """
        import requests
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code != 200:
                raise ValueError("Ollama no está respondiendo en http://localhost:11434")

            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            if self.ollama_model not in model_names:
                available = ', '.join(model_names[:5]) if model_names else 'ninguno'
                raise ValueError(
                    f"El modelo '{self.ollama_model}' no está descargado en Ollama. "
                    f"Modelos disponibles: {available}. "
                    f"Descárgalo con: ollama pull {self.ollama_model}"
                )
        except requests.exceptions.ConnectionError:
            raise ValueError(
                "No se puede conectar con Ollama. "
                "Verifica que Ollama esté ejecutándose: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise ValueError("Timeout al conectar con Ollama.")

    def process_message(self, message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process a user message through the Job Search Agent

        Args:
            message: User's question/message
            conversation_history: Previous messages in the conversation

        Returns:
            Dict with content and metadata
        """
        # Ollama doesn't need API key
        if not self.api_key and self.provider != 'ollama':
            return {
                'content': 'Por favor, configura tu API key de LLM en tu perfil.',
                'metadata': {
                    'error': 'NO_API_KEY',
                    'tools_used': [],
                    'iterations': 0,
                }
            }

        try:
            print(f"\n[SERVICE] Iniciando process_message...", file=sys.stderr)
            print(f"[SERVICE] Proveedor: {self.provider.upper()}", file=sys.stderr)
            print(f"[SERVICE] Mensaje: {message[:60]}...", file=sys.stderr)

            # Get the agent
            agent = self._get_agent()

            if agent is None:
                raise ValueError("El agente no pudo ser inicializado")

            # Set API key in environment
            if self.provider != 'ollama':
                env_var_map = {
                    'google': 'GOOGLE_API_KEY',
                    'openai': 'OPENAI_API_KEY',
                }
                env_var = env_var_map.get(self.provider, 'GOOGLE_API_KEY')
                os.environ[env_var] = self.api_key

            # Prepare conversation history
            formatted_history = []
            if conversation_history and len(conversation_history) > 0:
                max_history = int(os.getenv('MAX_CONVERSATION_HISTORY', '10'))
                recent_history = conversation_history[-max_history:]
                for msg in recent_history:
                    formatted_history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })

            # Execute query
            print(f"[SERVICE] Ejecutando query en el agente...", file=sys.stderr)
            result = agent.query(message, conversation_history=formatted_history)
            print(f"[SERVICE] ✓ Query ejecutado correctamente", file=sys.stderr)

            # Extract response
            response_content = result.get('answer', 'No se pudo generar una respuesta.')
            tools_used = result.get('tools_used', [])

            # Build metadata
            metadata = {
                'provider': self.provider,
                'iterations': result.get('iterations', 0),
                'tools_used': tools_used,
            }

            # Log
            if tools_used:
                print(f"[SERVICE] Herramientas usadas ({len(tools_used)}): {' → '.join(tools_used)}", file=sys.stderr)
            print(f"[SERVICE] ✓ Respuesta inicial: {len(response_content)} caracteres", file=sys.stderr)

            # Review and improve response
            reviewer = self._get_reviewer()
            if reviewer:
                print(f"[SERVICE] Iniciando revisión de respuesta...", file=sys.stderr)

                review_result = reviewer.review_response(
                    user_question=message,
                    conversation_history=formatted_history,
                    initial_response=response_content,
                    metadata={'tools_used': tools_used}
                )

                review_score = review_result.get('score', 100)
                review_status = review_result.get('status', 'APPROVED')
                review_feedback = review_result.get('feedback', '')

                print(f"[SERVICE] Review - Status: {review_status}, Score: {review_score}/100", file=sys.stderr)

                # Always run second iteration for improvement
                if review_feedback:
                    print(f"[SERVICE] Ejecutando 2da iteración con feedback...", file=sys.stderr)

                    # Add feedback to conversation for improvement
                    improvement_prompt = (
                        f"Tu respuesta anterior fue evaluada con {review_score}/100 puntos.\n"
                        f"Feedback del revisor: {review_feedback}\n\n"
                        f"Por favor, mejora tu respuesta teniendo en cuenta este feedback. "
                        f"Mantén la información correcta y añade lo que falta."
                    )

                    # Create history with original response
                    improved_history = formatted_history.copy()
                    improved_history.append({'role': 'user', 'content': message})
                    improved_history.append({'role': 'assistant', 'content': response_content})

                    # Execute improvement query
                    improved_result = agent.query(improvement_prompt, conversation_history=improved_history)
                    improved_content = improved_result.get('answer', response_content)

                    # Use improved response
                    response_content = improved_content
                    metadata['iterations'] += improved_result.get('iterations', 0)
                    metadata['improvement_applied'] = True

                    print(f"[SERVICE] ✓ Respuesta mejorada: {len(response_content)} caracteres", file=sys.stderr)

                # Add review info to metadata
                metadata['review'] = {
                    'score': review_score,
                    'status': review_status,
                    'issues': review_result.get('issues', []),
                    'suggestions': review_result.get('suggestions', [])
                }

            print(f"[SERVICE] ✓ Respuesta final: {len(response_content)} caracteres", file=sys.stderr)

            return {
                'content': response_content,
                'metadata': metadata
            }

        except ValueError as e:
            return {
                'content': f'Error de configuración: {str(e)}',
                'metadata': {
                    'error': 'CONFIGURATION_ERROR',
                    'tools_used': [],
                    'iterations': 0
                }
            }

        except Exception as e:
            return {
                'content': f'Lo siento, ocurrió un error: {str(e)}',
                'metadata': {
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'tools_used': [],
                    'iterations': 0
                }
            }

    def reset_agent(self):
        """Reset the cached agent instance"""
        self._agent = None
