# -*- coding: utf-8 -*-
"""
Tests para las tools del agente de búsqueda de empleo.
Ejecutar con: python manage.py test tests.test_tools
"""

import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch, MagicMock

User = get_user_model()


class CVAnalyzerToolTest(TestCase):
    """Tests para la tool de análisis de CV"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_cv_analyzer_initialization(self):
        """Test que la tool se inicializa correctamente"""
        from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool

        tool = CVAnalyzerTool(llm=None)
        self.assertEqual(tool.name, 'analyze_cv')
        self.assertIn('CV', tool.description)

    def test_cv_analyzer_schema(self):
        """Test que el schema es correcto"""
        from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool

        tool = CVAnalyzerTool(llm=None)
        schema = tool.get_schema()

        self.assertEqual(schema['name'], 'analyze_cv')
        self.assertIn('cv_text', schema['parameters']['properties'])
        self.assertIn('cv_text', schema['parameters']['required'])

    def test_cv_analyzer_short_text_error(self):
        """Test que rechaza CV muy corto"""
        from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool

        tool = CVAnalyzerTool(llm=None)
        result = tool.run("Hola")

        self.assertFalse(result['success'])
        self.assertIn('corto', result['error'].lower())

    def test_cv_analyzer_with_valid_cv(self):
        """Test analisis de CV valido"""
        from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool

        # Mock del LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps({
            'skills': ['Python', 'Django', 'JavaScript'],
            'experience': [{'company': 'Test Corp', 'position': 'Developer'}],
            'education': [{'institution': 'Universidad', 'degree': 'Informatica'}],
            'languages': [{'language': 'Espanol', 'level': 'Nativo'}],
            'professional_summary': 'Desarrollador con experiencia'
        })
        mock_llm.invoke.return_value = mock_response

        tool = CVAnalyzerTool(llm=mock_llm)
        result = tool.run("CV largo con mas de 50 caracteres de contenido para pasar la validacion inicial")

        self.assertTrue(result['success'])
        self.assertIn('skills', result['data'])


class JobSearchToolTest(TestCase):
    """Tests para la tool de búsqueda de empleo"""

    def test_job_search_initialization(self):
        """Test inicialización"""
        from agent_ia_core.tools.job_search_tool import JobSearchTool

        tool = JobSearchTool(llm=None, web_search_tool=None)
        self.assertEqual(tool.name, 'search_jobs')

    def test_job_search_schema(self):
        """Test schema correcto"""
        from agent_ia_core.tools.job_search_tool import JobSearchTool

        tool = JobSearchTool()
        schema = tool.get_schema()

        self.assertEqual(schema['name'], 'search_jobs')
        self.assertIn('query', schema['parameters']['properties'])
        self.assertIn('location', schema['parameters']['properties'])

    def test_job_search_no_web_search_error(self):
        """Test error cuando no hay web search"""
        from agent_ia_core.tools.job_search_tool import JobSearchTool

        tool = JobSearchTool(web_search_tool=None)
        result = tool.run(query="programador python")

        self.assertFalse(result['success'])
        self.assertIn('Web search no disponible', result['error'])

    def test_job_search_with_mock_web_search(self):
        """Test búsqueda con web search mockeado"""
        from agent_ia_core.tools.job_search_tool import JobSearchTool

        mock_web_search = Mock()
        mock_web_search.run.return_value = {
            'success': True,
            'data': {
                'results': [
                    {'title': 'Programador Python', 'snippet': 'Oferta...', 'url': 'http://test.com'}
                ]
            }
        }

        tool = JobSearchTool(web_search_tool=mock_web_search)
        result = tool.run(query="programador python", location="Madrid")

        self.assertTrue(result['success'])
        self.assertIn('jobs', result['data'])


class CompanySearchToolTest(TestCase):
    """Tests para la tool de búsqueda de empresas"""

    def test_company_search_initialization(self):
        """Test inicialización"""
        from agent_ia_core.tools.job_search_tool import CompanySearchTool

        tool = CompanySearchTool()
        self.assertEqual(tool.name, 'search_companies')

    def test_company_search_schema(self):
        """Test schema"""
        from agent_ia_core.tools.job_search_tool import CompanySearchTool

        tool = CompanySearchTool()
        schema = tool.get_schema()

        self.assertIn('sector', schema['parameters']['properties'])
        self.assertIn('location', schema['parameters']['properties'])
        self.assertIn('company_name', schema['parameters']['properties'])


class LinkedInRecruiterToolTest(TestCase):
    """Tests para la tool de búsqueda de reclutadores"""

    def test_linkedin_recruiter_initialization(self):
        """Test inicialización"""
        from agent_ia_core.tools.linkedin_tool import LinkedInRecruiterTool

        tool = LinkedInRecruiterTool()
        self.assertEqual(tool.name, 'find_linkedin_recruiters')

    def test_linkedin_recruiter_schema(self):
        """Test schema"""
        from agent_ia_core.tools.linkedin_tool import LinkedInRecruiterTool

        tool = LinkedInRecruiterTool()
        schema = tool.get_schema()

        self.assertIn('company_name', schema['parameters']['properties'])
        self.assertIn('company_name', schema['parameters']['required'])

    def test_linkedin_recruiter_no_web_search(self):
        """Test error sin web search"""
        from agent_ia_core.tools.linkedin_tool import LinkedInRecruiterTool

        tool = LinkedInRecruiterTool(web_search_tool=None)
        result = tool.run(company_name="Indra")

        self.assertFalse(result['success'])

    def test_linkedin_recruiter_with_mock(self):
        """Test con web search mockeado"""
        from agent_ia_core.tools.linkedin_tool import LinkedInRecruiterTool

        mock_web_search = Mock()
        mock_web_search.run.return_value = {
            'success': True,
            'data': {
                'results': [
                    {
                        'title': 'María García - Recruiter | LinkedIn',
                        'snippet': 'Talent Acquisition at Indra',
                        'url': 'https://linkedin.com/in/maria-garcia'
                    }
                ]
            }
        }

        tool = LinkedInRecruiterTool(web_search_tool=mock_web_search)
        result = tool.run(company_name="Indra")

        self.assertTrue(result['success'])
        self.assertIn('recruiters', result['data'])
        self.assertIn('search_tips', result['data'])


class JobMatchToolTest(TestCase):
    """Tests para la tool de match perfil-oferta"""

    def test_job_match_initialization(self):
        """Test inicialización"""
        from agent_ia_core.tools.job_search_tool import JobMatchTool

        tool = JobMatchTool()
        self.assertEqual(tool.name, 'match_job_profile')

    def test_job_match_no_llm_error(self):
        """Test error sin LLM"""
        from agent_ia_core.tools.job_search_tool import JobMatchTool

        tool = JobMatchTool(llm=None)
        result = tool.run(job_description="Desarrollador Python con 3 años de experiencia")

        self.assertFalse(result['success'])
        self.assertIn('LLM no configurado', result['error'])


class ProfileSuggestionsToolTest(TestCase):
    """Tests para la tool de sugerencias de perfil"""

    def test_profile_suggestions_initialization(self):
        """Test inicialización"""
        from agent_ia_core.tools.linkedin_tool import ProfileSuggestionsTool

        tool = ProfileSuggestionsTool()
        self.assertEqual(tool.name, 'suggest_profile_improvements')

    def test_profile_suggestions_no_llm_error(self):
        """Test error sin LLM"""
        from agent_ia_core.tools.linkedin_tool import ProfileSuggestionsTool

        tool = ProfileSuggestionsTool(llm=None)
        result = tool.run(target_role="Data Scientist")

        self.assertFalse(result['success'])


class ToolRegistryTest(TestCase):
    """Tests para el registro de tools"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_registry_initialization(self):
        """Test que el registry se inicializa con todas las tools"""
        from agent_ia_core.tools.registry import ToolRegistry

        registry = ToolRegistry(user=self.user)

        # Verificar tools básicas
        self.assertIn('get_user_profile', registry.tools)
        self.assertIn('analyze_cv', registry.tools)
        self.assertIn('search_jobs', registry.tools)
        self.assertIn('search_companies', registry.tools)
        self.assertIn('find_linkedin_recruiters', registry.tools)

    def test_registry_get_tool(self):
        """Test obtener tool por nombre"""
        from agent_ia_core.tools.registry import ToolRegistry

        registry = ToolRegistry(user=self.user)
        tool = registry.get_tool('analyze_cv')

        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, 'analyze_cv')

    def test_registry_get_nonexistent_tool(self):
        """Test obtener tool que no existe"""
        from agent_ia_core.tools.registry import ToolRegistry

        registry = ToolRegistry(user=self.user)
        tool = registry.get_tool('nonexistent_tool')

        self.assertIsNone(tool)

    def test_registry_get_all_schemas(self):
        """Test obtener schemas de todas las tools"""
        from agent_ia_core.tools.registry import ToolRegistry

        registry = ToolRegistry(user=self.user)
        schemas = registry.get_all_schemas()

        self.assertIsInstance(schemas, list)
        self.assertGreater(len(schemas), 0)

        # Verificar formato de schema
        for schema in schemas:
            self.assertIn('name', schema)
            self.assertIn('description', schema)
            self.assertIn('parameters', schema)
