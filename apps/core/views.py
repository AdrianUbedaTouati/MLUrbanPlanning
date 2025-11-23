from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import JsonResponse
from .forms import EditProfileForm, CVImageUploadForm
from .ollama_checker import OllamaHealthChecker
from apps.company.models import UserProfile
import uuid
import json
import os
import base64
from openai import OpenAI
from pdf2image import convert_from_bytes
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def home_view(request):
    """Vista principal de la aplicación"""
    print(f"[HOME DEBUG] Usuario autenticado: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"[HOME DEBUG] Usuario: {request.user.username} (ID: {request.user.id})")
        print(f"[HOME DEBUG] Session key: {request.session.session_key}")
        print(f"[HOME DEBUG] User ID en sesión: {request.session.get('_auth_user_id')}")
    else:
        print(f"[HOME DEBUG] Usuario NO autenticado (AnonymousUser)")
        print(f"[HOME DEBUG] Session key: {request.session.session_key}")
        print(f"[HOME DEBUG] Contenido de sesión: {dict(request.session.items())}")

    context = {
        'total_users': 0,  # Placeholder for future statistics
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    """Vista de información sobre la aplicación"""
    return render(request, 'core/about.html')


def contact_view(request):
    """Vista de contacto"""
    return render(request, 'core/contact.html')


@login_required
def dashboard_view(request):
    """Dashboard para usuarios autenticados"""
    context = {
        'user': request.user,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def profile_view(request):
    """Vista del perfil del usuario con formulario de edición integrado"""
    form = EditProfileForm(instance=request.user)
    return render(request, 'core/profile.html', {'user': request.user, 'form': form})


@login_required
def edit_profile_view(request):
    """Vista para editar el perfil del usuario"""
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            # Si el email cambió, marcar como no verificado
            old_email = request.user.email
            user = form.save(commit=False)

            # Si el email cambió y la verificación está habilitada
            if old_email != user.email and settings.EMAIL_VERIFICATION_REQUIRED:
                user.email_verified = False
                user.verification_token = uuid.uuid4()

                # Enviar nuevo email de verificación
                subject = 'Confirma tu nuevo correo'
                html_message = render_to_string('authentication/email/verify_email.html', {
                    'user': user,
                    'domain': settings.SITE_URL.replace('http://', '').replace('https://', ''),
                    'protocol': 'https' if 'https' in settings.SITE_URL else 'http',
                    'token': user.verification_token,
                })
                plain_message = strip_tags(html_message)

                try:
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    messages.warning(request, 'Tu correo ha cambiado. Por favor revisa tu bandeja de entrada para confirmar el nuevo correo.')
                except Exception as e:
                    messages.warning(request, 'Perfil actualizado pero no se pudo enviar el email de confirmación.')

            user.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('apps_core:profile')
    else:
        form = EditProfileForm(instance=request.user)

    # Obtener datos de preferencias del perfil
    profile = getattr(request.user, 'job_profile', None)
    context = {
        'form': form,
        'preferred_locations_json': json.dumps(profile.preferred_locations if profile and profile.preferred_locations else []),
        'preferred_sectors_json': json.dumps(profile.preferred_sectors if profile and profile.preferred_sectors else []),
        'job_types_json': json.dumps(profile.job_types if profile and profile.job_types else []),
    }
    return render(request, 'core/edit_profile.html', context)


@login_required
def ollama_check_view(request):
    """
    Página de verificación de Ollama
    Muestra el estado de instalación, servidor y modelos
    """
    # Get user's configured models (use empty string check instead of 'or')
    user_chat_model = request.user.ollama_model if request.user.ollama_model else "qwen2.5:72b"
    user_embedding_model = request.user.ollama_embedding_model if request.user.ollama_embedding_model else "nomic-embed-text"

    # Debug info
    print(f"[OLLAMA CHECK] Usuario: {request.user.username}")
    print(f"[OLLAMA CHECK] Chat model DB: [{request.user.ollama_model}]")
    print(f"[OLLAMA CHECK] Chat model usado: [{user_chat_model}]")
    print(f"[OLLAMA CHECK] Embed model DB: [{request.user.ollama_embedding_model}]")
    print(f"[OLLAMA CHECK] Embed model usado: [{user_embedding_model}]")

    # Perform full health check
    health_status = OllamaHealthChecker.full_health_check(
        user_chat_model=user_chat_model,
        user_embedding_model=user_embedding_model
    )

    # Get recommendations
    recommendations = OllamaHealthChecker.get_recommendations()

    context = {
        'health_status': health_status,
        'recommendations': recommendations,
        'user_chat_model': user_chat_model,
        'user_embedding_model': user_embedding_model,
        'user': request.user,
        'debug_info': {
            'username': request.user.username,
            'db_chat_model': request.user.ollama_model,
            'db_embed_model': request.user.ollama_embedding_model,
        }
    }

    return render(request, 'core/ollama_check.html', context)


@login_required
def ollama_test_api(request):
    """
    API endpoint to test Ollama model
    """
    if request.method == 'POST':
        model_name = request.POST.get('model', 'qwen2.5:72b')
        test_prompt = request.POST.get('prompt', '¿Cuál es la capital de España?')

        # Test the model
        test_result = OllamaHealthChecker.test_model(model_name, test_prompt)

        return JsonResponse(test_result)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def ollama_models_api(request):
    """
    API endpoint to get installed Ollama models
    Returns list of available models for dropdowns
    """
    try:
        models_info = OllamaHealthChecker.get_installed_models()

        if models_info["success"]:
            # Separate models into chat and embedding categories
            chat_models = []
            embedding_models = []

            for model in models_info["models"]:
                model_name = model["name"]

                # Check if it's an embedding model (usually contains 'embed' in name)
                if 'embed' in model_name.lower():
                    embedding_models.append({
                        'name': model_name,
                        'size': model.get('size', ''),
                        'modified': model.get('modified', '')
                    })
                else:
                    chat_models.append({
                        'name': model_name,
                        'size': model.get('size', ''),
                        'modified': model.get('modified', '')
                    })

            return JsonResponse({
                'success': True,
                'chat_models': chat_models,
                'embedding_models': embedding_models,
                'total_count': models_info['count'],
                'recommended_chat': 'qwen2.5:72b',
                'recommended_embedding': 'nomic-embed-text',
                'message': models_info['message']
            })
        else:
            return JsonResponse({
                'success': False,
                'chat_models': [],
                'embedding_models': [],
                'message': models_info['message']
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'chat_models': [],
            'embedding_models': [],
            'message': f'Error obteniendo modelos: {str(e)}'
        })


@login_required
def analyze_cv_image_view(request):
    """
    Vista para analizar una imagen del CV usando GPT-4 Vision.
    Extrae información y genera un resumen del curriculum.
    """
    if request.method == 'POST':
        form = CVImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Verificar que el usuario tiene API key de OpenAI configurada
            if not request.user.llm_api_key or request.user.llm_provider != 'openai':
                messages.error(request, 'Debes configurar tu API key de OpenAI en tu perfil para usar esta función.')
                return redirect('apps_core:profile')

            # Obtener o crear el perfil del usuario
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'full_name': request.user.get_full_name() or request.user.username}
            )

            # Procesar el archivo (imagen o PDF)
            cv_file = form.cleaned_data['cv_file']
            file_ext = cv_file.name.lower().split('.')[-1]

            # Preparar la imagen para GPT-4 Vision
            if file_ext == 'pdf':
                # Convertir PDF a imagen
                try:
                    pdf_bytes = cv_file.read()
                    images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
                    if images:
                        img_buffer = BytesIO()
                        images[0].save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        image_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                        media_type = "image/png"
                    else:
                        messages.error(request, 'No se pudo procesar el PDF.')
                        return redirect('apps_core:profile')
                except Exception as e:
                    messages.error(request, f'Error al procesar PDF: {str(e)}')
                    return redirect('apps_core:profile')
            else:
                # Es una imagen - codificar en base64
                image_data = base64.b64encode(cv_file.read()).decode('utf-8')
                # Determinar tipo de imagen
                if file_ext in ['jpg', 'jpeg']:
                    media_type = "image/jpeg"
                elif file_ext == 'png':
                    media_type = "image/png"
                elif file_ext == 'gif':
                    media_type = "image/gif"
                elif file_ext == 'webp':
                    media_type = "image/webp"
                else:
                    media_type = "image/png"

            # Crear contenido de imagen en base64
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"}
            }

            try:
                # Inicializar cliente OpenAI
                client = OpenAI(api_key=request.user.llm_api_key)

                # Prompt único para extraer el texto completo del CV
                extraction_prompt = """Analiza esta imagen de un curriculum vitae y extrae TODO el texto que aparece en el documento.

Transcribe el contenido completo del CV de forma clara y organizada, manteniendo la estructura original:
- Datos personales (nombre, teléfono, email, ubicación)
- Resumen profesional o perfil
- Experiencia laboral (empresa, puesto, fechas, responsabilidades)
- Formación académica
- Habilidades técnicas y blandas
- Idiomas y niveles
- Certificaciones
- Cualquier otra información relevante

Devuelve el texto de forma legible y bien estructurada, NO en formato JSON. El objetivo es tener una transcripción completa del CV."""

                # Única llamada a GPT-4 Vision para extracción
                extraction_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": extraction_prompt},
                                image_content
                            ]
                        }
                    ],
                    max_tokens=4000
                )

                # Guardar el texto completo del CV
                cv_text = extraction_response.choices[0].message.content
                profile.curriculum_text = cv_text
                profile.cv_analyzed = True
                profile.save()

                messages.success(request, 'CV analizado correctamente. El texto ha sido extraído.')

            except Exception as e:
                messages.error(request, f'Error al analizar el CV: {str(e)}')

            return redirect('apps_core:profile')
    else:
        form = CVImageUploadForm()

    return render(request, 'core/analyze_cv.html', {'form': form})


@login_required
def analyze_cv_ajax_view(request):
    """
    Endpoint AJAX para analizar CV con GPT-4 Vision.
    Devuelve JSON con el resultado.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    form = CVImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        errors = ', '.join([f"{k}: {v[0]}" for k, v in form.errors.items()])
        return JsonResponse({'success': False, 'error': errors})

    # Verificar API key de OpenAI
    if not request.user.llm_api_key or request.user.llm_provider != 'openai':
        return JsonResponse({
            'success': False,
            'error': 'Debes configurar tu API key de OpenAI en tu perfil para usar esta función.'
        })

    # Obtener o crear el perfil del usuario
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name() or request.user.username}
    )

    # Procesar el archivo (imagen o PDF)
    cv_file = form.cleaned_data['cv_file']
    file_ext = cv_file.name.lower().split('.')[-1]

    try:
        # Preparar la imagen para GPT-4 Vision
        if file_ext == 'pdf':
            # Convertir PDF a imagen y guardarla
            pdf_bytes = cv_file.read()
            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
            if images:
                img_buffer = BytesIO()
                images[0].save(img_buffer, format='PNG')
                img_buffer.seek(0)

                from django.core.files.base import ContentFile
                img_name = cv_file.name.rsplit('.', 1)[0] + '.png'
                profile.cv_image.save(img_name, ContentFile(img_buffer.read()), save=True)

                image_url = request.build_absolute_uri(profile.cv_image.url)
            else:
                return JsonResponse({'success': False, 'error': 'No se pudo procesar el PDF.'})
        else:
            # Es una imagen - guardarla y usar URL
            profile.cv_image = cv_file
            profile.save()
            image_url = request.build_absolute_uri(profile.cv_image.url)

        # Inicializar cliente OpenAI
        client = OpenAI(api_key=request.user.llm_api_key)

        # Prompt para extraer información del CV
        extraction_prompt = """Analiza esta imagen de un curriculum vitae y extrae toda la información importante en formato JSON.

Devuelve SOLO un JSON válido con esta estructura exacta:
{
    "full_name": "nombre completo de la persona",
    "phone": "teléfono si aparece",
    "email": "email si aparece",
    "location": "ciudad/ubicación si aparece",
    "skills": ["lista", "de", "habilidades", "técnicas", "y", "blandas"],
    "experience": [
        {
            "company": "nombre empresa",
            "position": "puesto",
            "duration": "periodo (ej: 2020-2023)",
            "description": "responsabilidades principales"
        }
    ],
    "education": [
        {
            "institution": "universidad/centro",
            "degree": "título obtenido",
            "year": "año de finalización"
        }
    ],
    "languages": [
        {
            "language": "idioma",
            "level": "nivel (nativo, avanzado, intermedio, básico)"
        }
    ],
    "certifications": ["certificaciones", "si", "las", "hay"]
}

Si algún campo no está disponible en la imagen, usa un string vacío o lista vacía según corresponda."""

        # Llamada a GPT-4 Vision para extracción
        extraction_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": extraction_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=2000
        )

        # Parsear la respuesta JSON
        extracted_text = extraction_response.choices[0].message.content
        if "```json" in extracted_text:
            extracted_text = extracted_text.split("```json")[1].split("```")[0]
        elif "```" in extracted_text:
            extracted_text = extracted_text.split("```")[1].split("```")[0]

        extracted_data = json.loads(extracted_text.strip())

        # Actualizar el perfil con los datos extraídos
        if extracted_data.get('full_name'):
            profile.full_name = extracted_data['full_name']
        if extracted_data.get('phone'):
            profile.phone = extracted_data['phone']
        if extracted_data.get('location'):
            profile.location = extracted_data['location']
        if extracted_data.get('skills'):
            profile.skills = extracted_data['skills']
        if extracted_data.get('experience'):
            profile.experience = extracted_data['experience']
        if extracted_data.get('education'):
            profile.education = extracted_data['education']
        if extracted_data.get('languages'):
            profile.languages = extracted_data['languages']

        # Generar resumen con otra llamada
        summary_prompt = f"""Basándote en estos datos extraídos de un CV, genera un resumen profesional conciso (máximo 3-4 oraciones) que destaque los puntos más fuertes del candidato:

{json.dumps(extracted_data, ensure_ascii=False, indent=2)}

El resumen debe ser en primera persona y profesional, adecuado para presentarse a empleadores."""

        summary_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=500
        )

        profile.professional_summary = summary_response.choices[0].message.content
        profile.cv_analyzed = True
        profile.save()

        return JsonResponse({
            'success': True,
            'message': 'CV analizado correctamente',
            'data': extracted_data
        })

    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al procesar la respuesta de la IA: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al analizar el CV: {str(e)}'
        })


@login_required
def save_cv_text_view(request):
    """
    Vista para guardar el CV en texto directamente.
    """
    if request.method == 'POST':
        curriculum_text = request.POST.get('curriculum_text', '').strip()

        if not curriculum_text:
            messages.error(request, 'El texto del CV no puede estar vacío.')
            return redirect('apps_core:profile')

        # Obtener o crear el perfil del usuario
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.username}
        )

        # Guardar el texto del CV
        profile.curriculum_text = curriculum_text
        profile.cv_analyzed = True

        # Generar resumen estructurado del CV
        cv_summary = _generate_cv_summary(curriculum_text, request.user)
        if cv_summary:
            profile.cv_summary = cv_summary

        profile.save()

        messages.success(request, 'CV guardado correctamente.')
        return redirect('apps_core:profile')

    return redirect('apps_core:profile')


def _generate_cv_summary(curriculum_text: str, user) -> dict:
    """
    Genera un resumen estructurado del CV usando LLM.
    """
    try:
        # Obtener LLM del usuario
        from .llm_providers import LLMProviderFactory
        llm = LLMProviderFactory.get_llm(
            provider=user.llm_provider,
            api_key=user.llm_api_key,
            model_name=user.openai_model if user.llm_provider == 'openai' else user.ollama_model
        )

        if not llm:
            return {}

        # Extraer puestos recomendados basados en el CV
        extraction_prompt = f"""Analiza este CV y genera un RANKING de puestos de trabajo en los que encajarías, ordenados del más adecuado al menos.

Habla directamente al propietario del CV en segunda persona.

Para cada puesto incluye:
- Nombre del puesto
- Tecnologías/habilidades de tu CV que aplicarían
- Justificación breve de por qué encajas (basada en tu experiencia y proyectos reales)

Ordena de mayor a menor adecuación. Sé realista y específico. Solo incluye puestos para los que tengas experiencia demostrable en tu CV.

CV:
{curriculum_text}
"""

        response = llm.invoke(extraction_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Convertir markdown a HTML
        import markdown
        html_content = markdown.markdown(response_text.strip())

        return html_content

    except Exception as e:
        logger.error(f"Error generando resumen CV: {e}")
        return ""


@login_required
def save_preferences_view(request):
    """
    Vista para guardar las preferencias de búsqueda de empleo.
    """
    if request.method == 'POST':
        # Obtener o crear el perfil del usuario
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.username}
        )

        # Parsear datos JSON de los tags
        try:
            profile.preferred_locations = json.loads(request.POST.get('preferred_locations', '[]'))
            profile.preferred_sectors = json.loads(request.POST.get('preferred_sectors', '[]'))
            profile.job_types = json.loads(request.POST.get('job_types', '[]'))
        except json.JSONDecodeError:
            pass

        # Otros campos
        salary_min = request.POST.get('salary_min', '').strip()
        if salary_min:
            profile.salary_min = int(salary_min)

        availability = request.POST.get('availability', '').strip()
        if availability:
            profile.availability = availability

        profile.save()
        messages.success(request, 'Preferencias guardadas correctamente.')
        return redirect('apps_core:profile')

    return redirect('apps_core:profile')


@login_required
def save_social_view(request):
    """
    Vista para guardar las redes sociales/profesionales.
    """
    if request.method == 'POST':
        # Obtener o crear el perfil del usuario
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.username}
        )

        profile.linkedin_url = request.POST.get('linkedin_url', '').strip()
        profile.github_url = request.POST.get('github_url', '').strip()
        profile.portfolio_url = request.POST.get('portfolio_url', '').strip()

        profile.save()
        messages.success(request, 'Redes profesionales guardadas correctamente.')
        return redirect('apps_core:profile')

    return redirect('apps_core:profile')