# -*- coding: utf-8 -*-
"""
Tests para los servicios de la plataforma.
Ejecutar con: python manage.py test tests.test_services
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock

User = get_user_model()


class ChatAgentServiceTest(TestCase):
    """Tests para el servicio del agente de chat"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='ollama',
            ollama_model='qwen2.5:7b'
        )

    def test_service_initialization(self):
        """Test inicialización del servicio"""
        from apps.chat.services import ChatAgentService

        service = ChatAgentService(self.user)

        self.assertEqual(service.user, self.user)
        self.assertEqual(service.provider, 'ollama')

    def test_service_no_api_key_ollama(self):
        """Test que Ollama no requiere API key"""
        from apps.chat.services import ChatAgentService

        self.user.llm_provider = 'ollama'
        self.user.llm_api_key = ''
        self.user.save()

        service = ChatAgentService(self.user)

        # No deberia dar error porque Ollama no necesita API key
        self.assertEqual(service.api_key, '')

    def test_service_requires_api_key_for_others(self):
        """Test que otros proveedores requieren API key"""
        from apps.chat.services import ChatAgentService

        self.user.llm_provider = 'openai'
        self.user.llm_api_key = ''
        self.user.save()

        service = ChatAgentService(self.user)
        result = service.process_message("Hola")

        self.assertIn('API key', result['content'])

    @patch('apps.chat.services.ChatAgentService._verify_ollama_availability')
    @patch('agent_ia_core.agent_function_calling.FunctionCallingAgent')
    def test_service_process_message(self, mock_agent_class, mock_verify):
        """Test procesar mensaje"""
        from apps.chat.services import ChatAgentService

        # Mock del agente
        mock_agent = MagicMock()
        mock_agent.query.return_value = {
            'answer': 'Respuesta de prueba',
            'tools_used': ['search_jobs'],
            'iterations': 1
        }
        mock_agent.tool_registry.tools = {'search_jobs': Mock()}
        mock_agent_class.return_value = mock_agent

        service = ChatAgentService(self.user)
        result = service.process_message("Busco trabajo en Madrid")

        self.assertIn('content', result)
        self.assertIn('metadata', result)

    def test_service_reset_agent(self):
        """Test resetear agente"""
        from apps.chat.services import ChatAgentService

        service = ChatAgentService(self.user)
        service._agent = "fake_agent"

        service.reset_agent()

        self.assertIsNone(service._agent)


class FunctionCallingAgentTest(TestCase):
    """Tests para el agente de function calling"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_agent_invalid_provider(self):
        """Test error con proveedor inválido"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        with self.assertRaises(ValueError) as context:
            FunctionCallingAgent(
                llm_provider='invalid_provider',
                llm_model='test',
                llm_api_key='test'
            )

        self.assertIn('no soportado', str(context.exception))

    def test_agent_requires_api_key(self):
        """Test que requiere API key para OpenAI/Google"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        with self.assertRaises(ValueError) as context:
            FunctionCallingAgent(
                llm_provider='openai',
                llm_model='gpt-4o-mini',
                llm_api_key=None
            )

        self.assertIn('API key', str(context.exception))

    @patch('agent_ia_core.agent_function_calling.ChatOllama')
    def test_agent_ollama_initialization(self, mock_ollama):
        """Test inicialización con Ollama"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        mock_ollama.return_value = MagicMock()

        agent = FunctionCallingAgent(
            llm_provider='ollama',
            llm_model='qwen2.5:7b',
            llm_api_key=None,
            user=self.user
        )

        self.assertEqual(agent.llm_provider, 'ollama')
        self.assertIsNotNone(agent.tool_registry)

    def test_agent_prepare_messages(self):
        """Test preparación de mensajes"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        with patch('agent_ia_core.agent_function_calling.ChatOllama'):
            agent = FunctionCallingAgent(
                llm_provider='ollama',
                llm_model='qwen2.5:7b',
                llm_api_key=None
            )

            messages = agent._prepare_messages(
                "Busco trabajo",
                conversation_history=[
                    {'role': 'user', 'content': 'Hola'},
                    {'role': 'assistant', 'content': 'Hola, ¿en qué puedo ayudarte?'}
                ]
            )

            # Debe tener system + history + current
            self.assertGreaterEqual(len(messages), 3)
            self.assertEqual(messages[0]['role'], 'system')
            self.assertEqual(messages[-1]['content'], 'Busco trabajo')


class ContextToolsTest(TestCase):
    """Tests para las tools de contexto"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_get_user_profile_tool_no_profile(self):
        """Test get_user_profile sin perfil"""
        from agent_ia_core.tools.context_tools import GetUserProfileTool

        tool = GetUserProfileTool(self.user)
        result = tool.run()

        self.assertFalse(result['success'])
        self.assertIn('no tiene un perfil', result['error'])

    def test_get_user_profile_tool_with_profile(self):
        """Test get_user_profile con perfil"""
        from agent_ia_core.tools.context_tools import GetUserProfileTool
        from apps.company.models import UserProfile

        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            skills=['Python', 'Django']
        )

        tool = GetUserProfileTool(self.user)
        result = tool.run()

        self.assertTrue(result['success'])
        self.assertIn('formatted_context', result['data'])
        self.assertIn('structured_data', result['data'])

    def test_get_search_history_tool(self):
        """Test get_search_history sin historial"""
        from agent_ia_core.tools.context_tools import GetSearchHistoryTool

        tool = GetSearchHistoryTool(self.user)
        result = tool.run()

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']['sessions']), 0)

    def test_get_search_history_with_sessions(self):
        """Test get_search_history con sesiones"""
        from agent_ia_core.tools.context_tools import GetSearchHistoryTool
        from apps.chat.models import ChatSession, ChatMessage

        # Crear sesión con mensaje
        session = ChatSession.objects.create(user=self.user, title='Búsqueda test')
        ChatMessage.objects.create(
            session=session,
            role='user',
            content='Busco trabajo en Alicante'
        )

        tool = GetSearchHistoryTool(self.user)
        result = tool.run()

        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']['sessions']), 1)
