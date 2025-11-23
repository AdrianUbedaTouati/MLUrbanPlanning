# -*- coding: utf-8 -*-
"""
Tests para las nuevas funcionalidades del chat:
- ResponseReviewer
- Integración en ChatAgentService
- Carga automática del perfil
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import json

User = get_user_model()


class ResponseReviewerTestCase(TestCase):
    """Tests para el ResponseReviewer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='google',
            llm_api_key='test-api-key'
        )

    def test_reviewer_initialization(self):
        """Test que el ResponseReviewer se inicializa correctamente"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        reviewer = ResponseReviewer(llm=mock_llm)

        self.assertIsNotNone(reviewer)
        self.assertEqual(reviewer.llm, mock_llm)

    def test_review_response_approved(self):
        """Test que el reviewer aprueba respuestas buenas"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="""STATUS: APPROVED
SCORE: 85

ISSUES:
- Ninguno

SUGGESTIONS:
- Añadir más detalles de contacto

FEEDBACK:
Respuesta correcta"""
        )

        reviewer = ResponseReviewer(llm=mock_llm)
        result = reviewer.review_response(
            user_question="Busco trabajo en Alicante",
            conversation_history=[],
            initial_response="He encontrado varias ofertas de trabajo en Alicante...",
            metadata={'tools_used': ['search_jobs']}
        )

        self.assertEqual(result['status'], 'APPROVED')
        self.assertEqual(result['score'], 85)
        self.assertEqual(len(result['issues']), 0)
        self.assertEqual(len(result['suggestions']), 1)

    def test_review_response_needs_improvement(self):
        """Test que el reviewer detecta respuestas que necesitan mejora"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="""STATUS: NEEDS_IMPROVEMENT
SCORE: 60

ISSUES:
- Falta información de requisitos
- No menciona el perfil del usuario

SUGGESTIONS:
- Incluir requisitos de cada puesto
- Relacionar con las habilidades del usuario

FEEDBACK:
La respuesta lista ofertas pero no explica por qué encajan con el perfil del usuario ni incluye requisitos específicos."""
        )

        reviewer = ResponseReviewer(llm=mock_llm)
        result = reviewer.review_response(
            user_question="Busco trabajo de programador",
            conversation_history=[],
            initial_response="Hay ofertas disponibles...",
            metadata={'tools_used': ['search_jobs']}
        )

        self.assertEqual(result['status'], 'NEEDS_IMPROVEMENT')
        self.assertEqual(result['score'], 60)
        self.assertEqual(len(result['issues']), 2)
        self.assertEqual(len(result['suggestions']), 2)
        self.assertIn('perfil del usuario', result['feedback'])

    def test_review_response_score_status_consistency(self):
        """Test que el reviewer ajusta inconsistencias entre score y status"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        # Score alto pero status incorrecto
        mock_llm.invoke.return_value = MagicMock(
            content="""STATUS: NEEDS_IMPROVEMENT
SCORE: 90

ISSUES:
- Ninguno

SUGGESTIONS:
- Ninguna

FEEDBACK:
"""
        )

        reviewer = ResponseReviewer(llm=mock_llm)
        result = reviewer.review_response(
            user_question="Test",
            conversation_history=[],
            initial_response="Test response",
            metadata={}
        )

        # Debe ajustar a APPROVED porque score >= 75
        self.assertEqual(result['status'], 'APPROVED')
        self.assertEqual(result['score'], 90)

    def test_review_response_error_handling(self):
        """Test que el reviewer maneja errores correctamente"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM Error")

        reviewer = ResponseReviewer(llm=mock_llm)
        result = reviewer.review_response(
            user_question="Test",
            conversation_history=[],
            initial_response="Test response",
            metadata={}
        )

        # Debe aprobar por defecto en caso de error
        self.assertEqual(result['status'], 'APPROVED')
        self.assertEqual(result['score'], 100)
        self.assertIn('error', result)

    def test_format_conversation_history(self):
        """Test que el historial se formatea correctamente"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        reviewer = ResponseReviewer(llm=mock_llm)

        history = [
            {'role': 'user', 'content': 'Hola'},
            {'role': 'assistant', 'content': 'Hola, ¿en qué puedo ayudarte?'}
        ]

        formatted = reviewer._format_conversation_history(history)

        self.assertIn('Usuario: Hola', formatted)
        self.assertIn('Asistente:', formatted)

    def test_format_empty_history(self):
        """Test que el historial vacío se maneja correctamente"""
        from apps.chat.response_reviewer import ResponseReviewer

        mock_llm = MagicMock()
        reviewer = ResponseReviewer(llm=mock_llm)

        formatted = reviewer._format_conversation_history([])
        self.assertEqual(formatted, "(Sin historial previo)")


class ChatAgentServiceTestCase(TestCase):
    """Tests para la integración del ResponseReviewer en ChatAgentService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='google',
            llm_api_key='test-api-key'
        )

        # Crear perfil de usuario
        from apps.company.models import UserProfile
        UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            location='Alicante',
            skills='Python, Django'
        )

    @patch('apps.chat.services.ChatAgentService._create_agent')
    def test_get_reviewer_initialization(self, mock_create_agent):
        """Test que el reviewer se inicializa correctamente desde el service"""
        from apps.chat.services import ChatAgentService

        mock_agent = MagicMock()
        mock_agent.llm = MagicMock()
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService(self.user)
        reviewer = service._get_reviewer()

        self.assertIsNotNone(reviewer)

    @patch('apps.chat.services.ChatAgentService._create_agent')
    def test_reviewer_caching(self, mock_create_agent):
        """Test que el reviewer se cachea correctamente"""
        from apps.chat.services import ChatAgentService

        mock_agent = MagicMock()
        mock_agent.llm = MagicMock()
        mock_create_agent.return_value = mock_agent

        service = ChatAgentService(self.user)

        reviewer1 = service._get_reviewer()
        reviewer2 = service._get_reviewer()

        # Debe ser la misma instancia
        self.assertIs(reviewer1, reviewer2)

    @patch('apps.chat.services.ChatAgentService._create_agent')
    @patch('apps.chat.services.ChatAgentService._get_reviewer')
    def test_process_message_with_review(self, mock_get_reviewer, mock_create_agent):
        """Test que process_message usa el reviewer"""
        from apps.chat.services import ChatAgentService

        # Mock del agente
        mock_agent = MagicMock()
        mock_agent.query.return_value = {
            'answer': 'Respuesta inicial',
            'tools_used': ['search_jobs'],
            'iterations': 1
        }
        mock_create_agent.return_value = mock_agent

        # Mock del reviewer
        mock_reviewer = MagicMock()
        mock_reviewer.review_response.return_value = {
            'status': 'APPROVED',
            'score': 85,
            'feedback': '',
            'issues': [],
            'suggestions': []
        }
        mock_get_reviewer.return_value = mock_reviewer

        service = ChatAgentService(self.user)
        result = service.process_message("Busco trabajo")

        # Verificar que se llamó al reviewer
        mock_reviewer.review_response.assert_called_once()

        # Verificar metadata
        self.assertIn('review', result['metadata'])
        self.assertEqual(result['metadata']['review']['score'], 85)

    @patch('apps.chat.services.ChatAgentService._create_agent')
    @patch('apps.chat.services.ChatAgentService._get_reviewer')
    def test_process_message_with_improvement(self, mock_get_reviewer, mock_create_agent):
        """Test que process_message ejecuta mejora cuando hay feedback"""
        from apps.chat.services import ChatAgentService

        # Mock del agente
        mock_agent = MagicMock()
        mock_agent.query.side_effect = [
            {
                'answer': 'Respuesta inicial',
                'tools_used': ['search_jobs'],
                'iterations': 1
            },
            {
                'answer': 'Respuesta mejorada con más detalles',
                'tools_used': [],
                'iterations': 1
            }
        ]
        mock_create_agent.return_value = mock_agent

        # Mock del reviewer con feedback
        mock_reviewer = MagicMock()
        mock_reviewer.review_response.return_value = {
            'status': 'NEEDS_IMPROVEMENT',
            'score': 65,
            'feedback': 'Falta incluir requisitos del puesto',
            'issues': ['Sin requisitos'],
            'suggestions': ['Añadir requisitos']
        }
        mock_get_reviewer.return_value = mock_reviewer

        service = ChatAgentService(self.user)
        result = service.process_message("Busco trabajo")

        # Verificar que se ejecutó la mejora
        self.assertEqual(mock_agent.query.call_count, 2)
        self.assertIn('Respuesta mejorada', result['content'])
        self.assertTrue(result['metadata'].get('improvement_applied'))


class AgentAutoContextTestCase(TestCase):
    """Tests para la carga automática del perfil en el agente"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='google',
            llm_api_key='test-api-key'
        )

        # Crear perfil de usuario
        from apps.company.models import UserProfile
        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            location='Alicante',
            skills='Python, Django, JavaScript',
            experience='5 años en desarrollo web'
        )

    def test_format_profile_summary(self):
        """Test que el perfil se formatea correctamente"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        profile_data = {
            'full_name': 'Test User',
            'location': 'Alicante',
            'skills': ['Python', 'Django', 'JavaScript'],
            'preferred_location': 'Valencia',
            'experience': '5 años en desarrollo web'
        }

        # Crear instancia mock para probar el método
        agent = MagicMock(spec=FunctionCallingAgent)
        agent._format_profile_summary = FunctionCallingAgent._format_profile_summary

        summary = agent._format_profile_summary(agent, profile_data)

        self.assertIn('Nombre: Test User', summary)
        self.assertIn('Ubicación: Alicante', summary)
        self.assertIn('Python, Django, JavaScript', summary)
        self.assertIn('Ubicación preferida para trabajo: Valencia', summary)

    def test_format_empty_profile(self):
        """Test que un perfil vacío muestra mensaje apropiado"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        agent = MagicMock(spec=FunctionCallingAgent)
        agent._format_profile_summary = FunctionCallingAgent._format_profile_summary

        summary = agent._format_profile_summary(agent, {})

        self.assertIn('no completado', summary)

    @patch('agent_ia_core.agent_function_calling.ChatGoogleGenerativeAI')
    def test_auto_profile_load_on_first_message(self, mock_llm_class):
        """Test que el perfil se carga automáticamente en el primer mensaje"""
        from agent_ia_core.agent_function_calling import FunctionCallingAgent

        # Mock del LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content='Respuesta de prueba')
        mock_llm_class.return_value = mock_llm

        # Mock del tool registry
        with patch('agent_ia_core.agent_function_calling.ToolRegistry') as mock_registry_class:
            mock_registry = MagicMock()
            mock_registry.tools = {
                'get_user_profile': MagicMock(),
                'search_jobs': MagicMock()
            }
            mock_registry.execute_tool.return_value = {
                'success': True,
                'data': {
                    'full_name': 'Test User',
                    'title': 'Desarrollador'
                }
            }
            mock_registry.get_ollama_tools.return_value = []
            mock_registry.get_openai_tools.return_value = []
            mock_registry.get_gemini_tools.return_value = []
            mock_registry_class.return_value = mock_registry

            agent = FunctionCallingAgent(
                llm_provider='google',
                llm_model='gemini-2.0-flash-exp',
                llm_api_key='test-key',
                user=self.user,
                max_iterations=1
            )

            # Ejecutar query (primer mensaje, sin historial)
            agent.query("Busco trabajo", conversation_history=None)

            # Verificar que se llamó a get_user_profile
            mock_registry.execute_tool.assert_any_call('get_user_profile')


class ReviewMetadataTestCase(TestCase):
    """Tests para verificar que la metadata de review se añade correctamente"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='google',
            llm_api_key='test-api-key'
        )

        from apps.company.models import UserProfile
        UserProfile.objects.create(user=self.user, full_name='Test User')

    @patch('apps.chat.services.ChatAgentService._create_agent')
    @patch('apps.chat.services.ChatAgentService._get_reviewer')
    def test_review_metadata_structure(self, mock_get_reviewer, mock_create_agent):
        """Test que la estructura de metadata de review es correcta"""
        from apps.chat.services import ChatAgentService

        mock_agent = MagicMock()
        mock_agent.query.return_value = {
            'answer': 'Test',
            'tools_used': [],
            'iterations': 1
        }
        mock_create_agent.return_value = mock_agent

        mock_reviewer = MagicMock()
        mock_reviewer.review_response.return_value = {
            'status': 'APPROVED',
            'score': 80,
            'feedback': '',
            'issues': ['Issue 1'],
            'suggestions': ['Suggestion 1', 'Suggestion 2']
        }
        mock_get_reviewer.return_value = mock_reviewer

        service = ChatAgentService(self.user)
        result = service.process_message("Test")

        review = result['metadata']['review']
        self.assertIn('score', review)
        self.assertIn('status', review)
        self.assertIn('issues', review)
        self.assertIn('suggestions', review)
        self.assertEqual(review['score'], 80)
        self.assertEqual(review['status'], 'APPROVED')
        self.assertEqual(len(review['issues']), 1)
        self.assertEqual(len(review['suggestions']), 2)
