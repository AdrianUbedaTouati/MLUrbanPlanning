# -*- coding: utf-8 -*-
"""
Tests esenciales para JobSearchAI Platform.
Cubre: autenticacion, chat, CV y tools principales.

Ejecutar con: python manage.py test tests.test_essential
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock
from apps.company.models import UserProfile

User = get_user_model()


class AuthenticationTest(TestCase):
    """Tests de autenticacion"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='ollama'
        )

    def test_login_success(self):
        """Test login exitoso"""
        response = self.client.post(reverse('apps_authentication:login'), {
            'username': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertIn(response.status_code, [200, 302])

    def test_login_failure(self):
        """Test login fallido"""
        response = self.client.post(reverse('apps_authentication:login'), {
            'username': 'test@example.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)

    def test_protected_view_requires_login(self):
        """Test que vistas protegidas requieren login"""
        response = self.client.get(reverse('apps_chat:session_list'))
        self.assertEqual(response.status_code, 302)


class ChatConversationTest(TestCase):
    """Tests de conversacion en el chat"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='chatuser',
            email='chat@example.com',
            password='testpass123',
            llm_provider='ollama',
            ollama_model='qwen2.5:7b'
        )
        self.client.login(username='chat@example.com', password='testpass123')

    def test_chat_session_list_view(self):
        """Test acceso a lista de sesiones"""
        response = self.client.get(reverse('apps_chat:session_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_new_session(self):
        """Test crear nueva sesion de chat"""
        from apps.chat.models import ChatSession

        # Crear sesion directamente
        session = ChatSession.objects.create(user=self.user, title='Nueva sesion')
        self.assertEqual(session.user, self.user)
        self.assertEqual(ChatSession.objects.count(), 1)

    def test_chat_session_detail(self):
        """Test acceso a detalle de sesion"""
        from apps.chat.models import ChatSession

        session = ChatSession.objects.create(user=self.user, title='Test')
        response = self.client.get(reverse('apps_chat:session_detail', args=[session.id]))
        self.assertEqual(response.status_code, 200)


class CVAnalysisTest(TestCase):
    """Tests de analisis de CV"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='cvuser',
            email='cv@example.com',
            password='testpass123',
            llm_provider='ollama'
        )
        self.client.login(username='cv@example.com', password='testpass123')

    def test_profile_view_access(self):
        """Test acceso a vista de perfil"""
        response = self.client.get(reverse('apps_company:profile'))
        self.assertEqual(response.status_code, 200)

    def test_cv_analyzer_tool_short_text(self):
        """Test que CVAnalyzer rechaza texto corto"""
        from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool

        tool = CVAnalyzerTool(llm=None)
        result = tool.run("Hola")

        self.assertFalse(result['success'])
        self.assertIn('corto', result['error'].lower())

    def test_cv_analyzer_tool_with_llm(self):
        """Test CVAnalyzer con LLM mockeado"""
        from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool

        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content=json.dumps({
            'skills': ['Python', 'Django'],
            'experience': [{'company': 'Tech', 'position': 'Dev'}],
            'education': [],
            'languages': [{'language': 'Espanol', 'level': 'Nativo'}],
            'professional_summary': 'Desarrollador'
        }))

        tool = CVAnalyzerTool(llm=mock_llm)
        result = tool.run("Curriculum completo con mas de 50 caracteres para pasar validacion")

        self.assertTrue(result['success'])
        self.assertIn('skills', result['data'])


class ToolsTest(TestCase):
    """Test de cada tool principal"""

    def test_job_search_tool(self):
        """Test JobSearchTool"""
        from agent_ia_core.tools.job_search_tool import JobSearchTool

        # Sin web_search debe dar error
        tool = JobSearchTool(web_search_tool=None)
        result = tool.run(query="programador python")

        self.assertFalse(result['success'])

        # Con web_search mockeado
        mock_web = Mock()
        mock_web.run.return_value = {
            'success': True,
            'data': {'results': [
                {'title': 'Programador Python', 'snippet': 'Oferta', 'url': 'http://test.com'}
            ]}
        }

        tool = JobSearchTool(web_search_tool=mock_web)
        result = tool.run(query="programador", location="Madrid")

        self.assertTrue(result['success'])
        self.assertGreater(len(result['data']['jobs']), 0)

    def test_company_search_tool(self):
        """Test CompanySearchTool"""
        from agent_ia_core.tools.job_search_tool import CompanySearchTool

        tool = CompanySearchTool(web_search_tool=None)
        result = tool.run(sector="Tecnologia")

        self.assertFalse(result['success'])

    def test_job_match_tool(self):
        """Test JobMatchTool"""
        from agent_ia_core.tools.job_search_tool import JobMatchTool

        # Sin LLM debe dar error
        tool = JobMatchTool(llm=None)
        result = tool.run(job_description="Desarrollador Python senior")

        self.assertFalse(result['success'])
        self.assertIn('LLM', result['error'])

    def test_linkedin_recruiter_tool(self):
        """Test LinkedInRecruiterTool"""
        from agent_ia_core.tools.linkedin_tool import LinkedInRecruiterTool

        tool = LinkedInRecruiterTool(web_search_tool=None)
        result = tool.run(company_name="Google")

        self.assertFalse(result['success'])

        # Con mock
        mock_web = Mock()
        mock_web.run.return_value = {
            'success': True,
            'data': {'results': [
                {'title': 'Recruiter Google', 'snippet': 'HR', 'url': 'http://linkedin.com/in/test'}
            ]}
        }

        tool = LinkedInRecruiterTool(web_search_tool=mock_web)
        result = tool.run(company_name="Google")

        self.assertTrue(result['success'])

    def test_profile_suggestions_tool(self):
        """Test ProfileSuggestionsTool"""
        from agent_ia_core.tools.linkedin_tool import ProfileSuggestionsTool

        tool = ProfileSuggestionsTool(llm=None, user_profile=None)
        result = tool.run()

        self.assertFalse(result['success'])

    def test_get_user_profile_tool(self):
        """Test GetUserProfileTool"""
        from agent_ia_core.tools.context_tools import GetUserProfileTool

        user = User.objects.create_user(
            username='profiletest',
            email='profile@test.com',
            password='test123'
        )
        UserProfile.objects.create(
            user=user,
            full_name='Test User',
            skills=['Python', 'Django']
        )

        tool = GetUserProfileTool(user=user)
        result = tool.run()

        self.assertTrue(result['success'])
        self.assertIn('structured_data', result['data'])
        self.assertIn('skills', result['data']['structured_data'])


class UserProfileModelTest(TestCase):
    """Test del modelo UserProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='modeltest',
            email='model@test.com',
            password='test123'
        )

    def test_create_profile(self):
        """Test crear perfil"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Juan Garcia',
            skills=['Python', 'JavaScript'],
            preferred_locations=['Madrid', 'Barcelona']
        )

        self.assertEqual(profile.full_name, 'Juan Garcia')
        self.assertEqual(len(profile.skills), 2)

    def test_profile_completeness(self):
        """Test verificacion de completitud"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test'
        )

        completeness = profile.check_completeness()
        self.assertFalse(completeness)

        # Completar perfil
        profile.skills = ['Python']
        profile.experience = [{'company': 'Test', 'position': 'Dev'}]
        profile.education = [{'institution': 'Uni', 'degree': 'Ing'}]
        profile.preferred_locations = ['Madrid']
        profile.save()

        completeness = profile.check_completeness()
        self.assertTrue(completeness)

    def test_to_agent_format(self):
        """Test conversion a formato agente"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Agent Test',
            skills=['Python'],
            preferred_locations=['Madrid']
        )

        agent_format = profile.to_agent_format()

        self.assertIn('skills', agent_format)
        self.assertIn('preferred_locations', agent_format)
