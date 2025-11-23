# -*- coding: utf-8 -*-
"""
Tests para los modelos de la plataforma.
Ejecutar con: python manage.py test tests.test_models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.company.models import UserProfile

User = get_user_model()


class UserProfileModelTest(TestCase):
    """Tests para el modelo UserProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_user_profile(self):
        """Test crear perfil de usuario"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Juan García',
            location='Alicante',
            phone='+34 600 000 000'
        )

        self.assertEqual(profile.full_name, 'Juan García')
        self.assertEqual(profile.location, 'Alicante')
        self.assertEqual(str(profile), 'Juan García (test@example.com)')

    def test_profile_json_fields(self):
        """Test campos JSON del perfil"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            skills=['Python', 'Django', 'JavaScript'],
            preferred_locations=['Madrid', 'Barcelona', 'Remoto'],
            preferred_sectors=['Informática/IT', 'Marketing']
        )

        self.assertEqual(len(profile.skills), 3)
        self.assertIn('Python', profile.skills)
        self.assertEqual(len(profile.preferred_locations), 3)

    def test_profile_experience_structure(self):
        """Test estructura de experiencia laboral"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            experience=[
                {
                    'company': 'Tech Corp',
                    'position': 'Senior Developer',
                    'duration': '2020-2023',
                    'description': 'Desarrollo de aplicaciones web'
                },
                {
                    'company': 'Startup Inc',
                    'position': 'Junior Developer',
                    'duration': '2018-2020',
                    'description': 'Frontend development'
                }
            ]
        )

        self.assertEqual(len(profile.experience), 2)
        self.assertEqual(profile.experience[0]['company'], 'Tech Corp')

    def test_profile_education_structure(self):
        """Test estructura de educación"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            education=[
                {
                    'institution': 'Universidad de Alicante',
                    'degree': 'Ingeniería Informática',
                    'year': '2018'
                }
            ]
        )

        self.assertEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0]['degree'], 'Ingeniería Informática')

    def test_profile_languages_structure(self):
        """Test estructura de idiomas"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            languages=[
                {'language': 'Español', 'level': 'Nativo'},
                {'language': 'Inglés', 'level': 'Avanzado'},
                {'language': 'Francés', 'level': 'Intermedio'}
            ]
        )

        self.assertEqual(len(profile.languages), 3)

    def test_profile_salary_range(self):
        """Test rango salarial"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            salary_min=25000,
            salary_max=45000
        )

        self.assertEqual(profile.salary_min, 25000)
        self.assertEqual(profile.salary_max, 45000)

    def test_to_agent_format(self):
        """Test conversión a formato del agente"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Juan García',
            location='Alicante',
            skills=['Python', 'Django'],
            preferred_locations=['Alicante', 'Remoto'],
            salary_min=30000,
            salary_max=50000
        )

        agent_format = profile.to_agent_format()

        self.assertIsInstance(agent_format, dict)
        self.assertEqual(agent_format['full_name'], 'Juan García')
        self.assertEqual(agent_format['location'], 'Alicante')
        self.assertIn('Python', agent_format['skills'])
        self.assertEqual(agent_format['salary_range']['min'], 30000)

    def test_get_chat_context(self):
        """Test generación de contexto para chat"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Juan García',
            location='Alicante',
            professional_summary='Desarrollador con 5 años de experiencia',
            skills=['Python', 'Django', 'React'],
            preferred_locations=['Alicante', 'Valencia'],
            preferred_sectors=['Informática/IT']
        )

        context = profile.get_chat_context()

        self.assertIn('Juan García', context)
        self.assertIn('Alicante', context)
        self.assertIn('Python', context)

    def test_check_completeness_incomplete(self):
        """Test perfil incompleto"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name=''
        )

        is_complete = profile.check_completeness()
        self.assertFalse(is_complete)
        self.assertFalse(profile.is_complete)

    def test_check_completeness_complete(self):
        """Test perfil completo"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Juan García',
            location='Alicante',
            skills=['Python']
        )

        is_complete = profile.check_completeness()
        self.assertTrue(is_complete)
        self.assertTrue(profile.is_complete)

    def test_profile_urls(self):
        """Test URLs profesionales"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            linkedin_url='https://linkedin.com/in/testuser',
            github_url='https://github.com/testuser',
            portfolio_url='https://testuser.dev'
        )

        self.assertEqual(profile.linkedin_url, 'https://linkedin.com/in/testuser')
        self.assertEqual(profile.github_url, 'https://github.com/testuser')

    def test_profile_cv_analyzed_flag(self):
        """Test flag de CV analizado"""
        profile = UserProfile.objects.create(
            user=self.user,
            full_name='Test User',
            cv_analyzed=False
        )

        self.assertFalse(profile.cv_analyzed)

        profile.cv_analyzed = True
        profile.save()

        profile.refresh_from_db()
        self.assertTrue(profile.cv_analyzed)


class UserModelTest(TestCase):
    """Tests para el modelo User personalizado"""

    def test_create_user(self):
        """Test crear usuario"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))

    def test_user_llm_settings(self):
        """Test configuración LLM del usuario"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Verificar campos LLM existen
        self.assertTrue(hasattr(user, 'llm_provider'))
        self.assertTrue(hasattr(user, 'llm_api_key'))

    def test_user_profile_relationship(self):
        """Test relación usuario-perfil"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        profile = UserProfile.objects.create(
            user=user,
            full_name='Test User'
        )

        # Acceder al perfil desde el usuario
        self.assertEqual(user.job_profile, profile)
