from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from apps.company.models import UserProfile
import json

User = get_user_model()


class CVAnalysisTestCase(TestCase):
    """Tests for CV analysis functionality"""

    def setUp(self):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            llm_provider='openai',
            llm_api_key='test-api-key'
        )
        self.client.login(username='testuser', password='testpass123')
        # Create job profile
        UserProfile.objects.create(user=self.user, full_name='Test User')

    def test_cv_analysis_requires_login(self):
        """Test that CV analysis requires authentication"""
        self.client.logout()
        response = self.client.post(reverse('apps_core:analyze_cv'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_cv_analysis_requires_openai_provider(self):
        """Test that CV analysis requires OpenAI as provider"""
        self.user.llm_provider = 'ollama'
        self.user.save()

        # Create a simple test file
        test_file = SimpleUploadedFile(
            "test_cv.png",
            b"fake image content",
            content_type="image/png"
        )

        response = self.client.post(
            reverse('apps_core:analyze_cv'),
            {'cv_file': test_file}
        )
        self.assertEqual(response.status_code, 302)  # Redirect back

    def test_cv_analysis_requires_api_key(self):
        """Test that CV analysis requires an API key"""
        self.user.llm_api_key = ''
        self.user.save()

        test_file = SimpleUploadedFile(
            "test_cv.png",
            b"fake image content",
            content_type="image/png"
        )

        response = self.client.post(
            reverse('apps_core:analyze_cv'),
            {'cv_file': test_file}
        )
        self.assertEqual(response.status_code, 302)

    def test_cv_analysis_without_file(self):
        """Test CV analysis behavior without file upload"""
        response = self.client.post(reverse('apps_core:analyze_cv'))
        # Returns 200 (form page) or 302 (redirect) depending on implementation
        self.assertIn(response.status_code, [200, 302])

    @patch('apps.core.views.OpenAI')
    def test_cv_analysis_success_with_image(self, mock_openai_class):
        """Test successful CV analysis with image file using base64"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Extracted CV text content"
        mock_client.chat.completions.create.return_value = mock_response

        # Create test image
        test_file = SimpleUploadedFile(
            "test_cv.png",
            b"fake image content",
            content_type="image/png"
        )

        response = self.client.post(
            reverse('apps_core:analyze_cv'),
            {'cv_file': test_file}
        )

        # Check redirect and profile update
        self.assertEqual(response.status_code, 302)
        self.user.job_profile.refresh_from_db()
        self.assertEqual(self.user.job_profile.curriculum_text, "Extracted CV text content")
        self.assertTrue(self.user.job_profile.cv_analyzed)

        # Verify OpenAI was called with base64 encoded image
        call_args = mock_client.chat.completions.create.call_args
        message_content = call_args.kwargs['messages'][0]['content']
        # Find the image content in the message
        image_content = [c for c in message_content if c.get('type') == 'image_url']
        self.assertEqual(len(image_content), 1)
        self.assertIn('image_url', image_content[0])
        # URL should be base64 data URL
        url = image_content[0]['image_url']['url']
        self.assertTrue(url.startswith('data:image/'))
        self.assertIn('base64', url)

    @patch('apps.core.views.convert_from_bytes')
    @patch('apps.core.views.OpenAI')
    def test_cv_analysis_success_with_pdf(self, mock_openai_class, mock_convert):
        """Test successful CV analysis with PDF file"""
        # Mock PDF conversion
        mock_image = MagicMock()
        mock_buffer = MagicMock()
        mock_image.save = MagicMock()
        mock_convert.return_value = [mock_image]

        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PDF CV content"
        mock_client.chat.completions.create.return_value = mock_response

        # Create test PDF
        test_file = SimpleUploadedFile(
            "test_cv.pdf",
            b"%PDF-1.4 fake pdf content",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('apps_core:analyze_cv'),
            {'cv_file': test_file}
        )

        self.assertEqual(response.status_code, 302)

    @patch('apps.core.views.OpenAI')
    def test_cv_analysis_handles_api_error(self, mock_openai_class):
        """Test CV analysis handles OpenAI API errors gracefully"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        test_file = SimpleUploadedFile(
            "test_cv.png",
            b"fake image content",
            content_type="image/png"
        )

        response = self.client.post(
            reverse('apps_core:analyze_cv'),
            {'cv_file': test_file}
        )

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)


class SaveCVTextTestCase(TestCase):
    """Tests for saving CV text"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        UserProfile.objects.create(user=self.user, full_name='Test User')

    def test_save_cv_text_success(self):
        """Test saving CV text successfully"""
        response = self.client.post(
            reverse('apps_core:save_cv_text'),
            {'curriculum_text': 'My professional experience...'}
        )

        self.assertEqual(response.status_code, 302)
        self.user.job_profile.refresh_from_db()
        self.assertEqual(self.user.job_profile.curriculum_text, 'My professional experience...')


class SavePreferencesTestCase(TestCase):
    """Tests for saving user preferences"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        UserProfile.objects.create(user=self.user, full_name='Test User')

    def test_save_preferences_success(self):
        """Test saving preferences successfully"""
        response = self.client.post(
            reverse('apps_core:save_preferences'),
            {
                'preferred_locations': '["Madrid", "Barcelona"]',
                'preferred_sectors': '["Tech", "Finance"]',
                'job_types': '["Remote"]',
                'salary_min': '30000'
            }
        )

        self.assertEqual(response.status_code, 302)
        self.user.job_profile.refresh_from_db()
        self.assertEqual(self.user.job_profile.preferred_locations, ["Madrid", "Barcelona"])
        self.assertEqual(self.user.job_profile.salary_min, 30000)


class SaveSocialTestCase(TestCase):
    """Tests for saving social networks"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        UserProfile.objects.create(user=self.user, full_name='Test User')

    def test_save_social_success(self):
        """Test saving social links successfully"""
        response = self.client.post(
            reverse('apps_core:save_social'),
            {
                'linkedin_url': 'https://linkedin.com/in/test',
                'github_url': 'https://github.com/test',
                'portfolio_url': 'https://myportfolio.com'
            }
        )

        self.assertEqual(response.status_code, 302)
        self.user.job_profile.refresh_from_db()
        self.assertEqual(self.user.job_profile.linkedin_url, 'https://linkedin.com/in/test')
