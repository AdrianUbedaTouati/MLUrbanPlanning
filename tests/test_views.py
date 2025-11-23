# -*- coding: utf-8 -*-
"""
Tests para las vistas de la plataforma.
Ejecutar con: python manage.py test tests.test_views
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.company.models import UserProfile
from apps.chat.models import ChatSession, ChatMessage

User = get_user_model()


class UserProfileViewTest(TestCase):
    """Tests para la vista de perfil de usuario"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view_get(self):
        """Test acceso GET al perfil"""
        response = self.client.get(reverse('apps_company:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'company/profile.html')

    def test_profile_view_creates_profile(self):
        """Test que la vista crea perfil si no existe"""
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())

        response = self.client.get(reverse('apps_company:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_profile_view_post(self):
        """Test guardar perfil con POST"""
        data = {
            'full_name': 'Juan García',
            'phone': '+34 600 000 000',
            'location': 'Alicante',
            'curriculum_text': 'Mi experiencia profesional...',
            'preferred_locations': '["Alicante", "Valencia"]',
            'preferred_sectors': '["Informática/IT"]',
            'job_types': '["Remoto"]',
            'contract_types': '["Indefinido"]',
            'salary_min': '25000',
            'salary_max': '45000',
            'availability': 'Inmediata',
            'linkedin_url': 'https://linkedin.com/in/juangarcia',
        }

        response = self.client.post(reverse('apps_company:profile'), data)

        self.assertEqual(response.status_code, 302)  # Redirect

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Juan García')
        self.assertEqual(profile.location, 'Alicante')
        self.assertIn('Alicante', profile.preferred_locations)

    def test_profile_view_requires_login(self):
        """Test que requiere login"""
        self.client.logout()
        response = self.client.get(reverse('apps_company:profile'))

        self.assertEqual(response.status_code, 302)  # Redirect to login


class AnalyzeCVViewTest(TestCase):
    """Tests para la vista de análisis de CV"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='ollama',
            ollama_model='qwen2.5:7b'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_analyze_cv_empty_text(self):
        """Test error con CV vacío"""
        response = self.client.post(
            reverse('apps_company:analyze_cv'),
            {'cv_text': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_analyze_cv_short_text(self):
        """Test error con CV muy corto"""
        response = self.client.post(
            reverse('apps_company:analyze_cv'),
            {'cv_text': 'Texto corto'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('corto', data['error'].lower())


class AutocompleteViewsTest(TestCase):
    """Tests para las vistas de autocompletado"""

    def test_autocomplete_locations(self):
        """Test autocompletado de ubicaciones"""
        response = self.client.get(
            reverse('apps_company:autocomplete_locations'),
            {'q': 'mad'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)

    def test_autocomplete_locations_default(self):
        """Test autocompletado sin query"""
        response = self.client.get(reverse('apps_company:autocomplete_locations'))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data['results']), 0)

    def test_autocomplete_sectors(self):
        """Test autocompletado de sectores"""
        response = self.client.get(
            reverse('apps_company:autocomplete_sectors'),
            {'q': 'inform'}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)


class ChatSessionViewsTest(TestCase):
    """Tests para las vistas de chat"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_chat_session_list(self):
        """Test lista de sesiones"""
        response = self.client.get(reverse('apps_chat:session_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/session_list.html')

    def test_chat_session_create(self):
        """Test crear nueva sesión"""
        response = self.client.post(reverse('apps_chat:session_create'))

        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(ChatSession.objects.filter(user=self.user).exists())

    def test_chat_session_create_ajax(self):
        """Test crear sesión via AJAX"""
        response = self.client.post(
            reverse('apps_chat:session_create'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('session_id', data)

    def test_chat_session_detail(self):
        """Test detalle de sesión"""
        session = ChatSession.objects.create(user=self.user)

        response = self.client.get(
            reverse('apps_chat:session_detail', args=[session.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/session_detail.html')

    def test_chat_session_detail_other_user(self):
        """Test que no se puede ver sesión de otro usuario"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        session = ChatSession.objects.create(user=other_user)

        response = self.client.get(
            reverse('apps_chat:session_detail', args=[session.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_chat_message_empty(self):
        """Test enviar mensaje vacío"""
        session = ChatSession.objects.create(user=self.user)

        response = self.client.post(
            reverse('apps_chat:message_create', args=[session.id]),
            {'message': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_chat_session_archive(self):
        """Test archivar sesión"""
        session = ChatSession.objects.create(user=self.user)

        response = self.client.post(
            reverse('apps_chat:session_archive', args=[session.id])
        )

        session.refresh_from_db()
        self.assertTrue(session.is_archived)

    def test_chat_session_delete(self):
        """Test eliminar sesión"""
        session = ChatSession.objects.create(user=self.user)
        session_id = session.id

        response = self.client.post(
            reverse('apps_chat:session_delete', args=[session_id])
        )

        self.assertFalse(ChatSession.objects.filter(id=session_id).exists())


class AuthenticationViewsTest(TestCase):
    """Tests para vistas de autenticación"""

    def setUp(self):
        self.client = Client()

    def test_login_view(self):
        """Test acceso a login"""
        response = self.client.get(reverse('apps_authentication:login'))
        self.assertEqual(response.status_code, 200)

    def test_register_view(self):
        """Test acceso a registro"""
        response = self.client.get(reverse('apps_authentication:register'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """Test login exitoso"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        response = self.client.post(reverse('apps_authentication:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, 302)  # Redirect

    def test_login_failure(self):
        """Test login fallido"""
        response = self.client.post(reverse('apps_authentication:login'), {
            'username': 'wronguser',
            'password': 'wrongpass'
        })

        self.assertEqual(response.status_code, 200)  # Stays on page


class URLsTest(TestCase):
    """Tests para verificar que las URLs están configuradas"""

    def test_profile_url(self):
        """Test URL de perfil"""
        url = reverse('apps_company:profile')
        self.assertEqual(url, '/perfil/')

    def test_analyze_cv_url(self):
        """Test URL de análisis CV"""
        url = reverse('apps_company:analyze_cv')
        self.assertEqual(url, '/perfil/analizar-cv/')

    def test_chat_urls(self):
        """Test URLs de chat"""
        self.assertEqual(reverse('apps_chat:session_list'), '/chat/')
        self.assertEqual(reverse('apps_chat:session_create'), '/chat/nueva/')

    def test_auth_urls(self):
        """Test URLs de autenticación"""
        self.assertEqual(reverse('apps_authentication:login'), '/auth/login/')
        self.assertEqual(reverse('apps_authentication:register'), '/auth/register/')
