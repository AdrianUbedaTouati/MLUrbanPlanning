import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile


class UserProfileView(LoginRequiredMixin, View):
    """Vista para ver y editar el perfil del usuario/candidato"""
    template_name = 'company/profile.html'

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.username}
        )

        context = {
            'profile': profile,
            'skills_json': json.dumps(profile.skills or []),
            'preferred_locations_json': json.dumps(profile.preferred_locations or []),
            'preferred_sectors_json': json.dumps(profile.preferred_sectors or []),
            'job_types_json': json.dumps(profile.job_types or []),
            'contract_types_json': json.dumps(profile.contract_types or []),
        }

        return render(request, self.template_name, context)

    def post(self, request):
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.username}
        )

        try:
            # Información personal
            profile.full_name = request.POST.get('full_name', '').strip()
            profile.phone = request.POST.get('phone', '').strip()
            profile.location = request.POST.get('location', '').strip()

            # CV
            profile.curriculum_text = request.POST.get('curriculum_text', '').strip()

            # Archivo CV (si se sube)
            if 'curriculum_file' in request.FILES:
                profile.curriculum_file = request.FILES['curriculum_file']

            # Preferencias de búsqueda (JSONFields)
            preferred_locations = request.POST.get('preferred_locations', '[]')
            profile.preferred_locations = json.loads(preferred_locations) if preferred_locations else []

            preferred_sectors = request.POST.get('preferred_sectors', '[]')
            profile.preferred_sectors = json.loads(preferred_sectors) if preferred_sectors else []

            job_types = request.POST.get('job_types', '[]')
            profile.job_types = json.loads(job_types) if job_types else []

            contract_types = request.POST.get('contract_types', '[]')
            profile.contract_types = json.loads(contract_types) if contract_types else []

            # Salario
            salary_min = request.POST.get('salary_min', '').strip()
            salary_max = request.POST.get('salary_max', '').strip()
            profile.salary_min = int(salary_min) if salary_min else None
            profile.salary_max = int(salary_max) if salary_max else None

            # Disponibilidad
            profile.availability = request.POST.get('availability', '').strip()

            # Redes profesionales
            profile.linkedin_url = request.POST.get('linkedin_url', '').strip()
            profile.github_url = request.POST.get('github_url', '').strip()
            profile.portfolio_url = request.POST.get('portfolio_url', '').strip()

            # Verificar completitud
            profile.check_completeness()

            profile.save()

            messages.success(request, 'Profil mis a jour correctement.')
            return redirect('apps_company:profile')

        except json.JSONDecodeError as e:
            messages.error(request, f'Erreur lors du traitement des donnees : {str(e)}')
            return redirect('apps_company:profile')

        except ValueError as e:
            messages.error(request, f'Erreur dans les donnees numeriques : {str(e)}')
            return redirect('apps_company:profile')

        except Exception as e:
            messages.error(request, f'Erreur lors de la sauvegarde du profil : {str(e)}')
            return redirect('apps_company:profile')


class AnalyzeCVView(LoginRequiredMixin, View):
    """Vista AJAX para analizar CV con IA"""

    def post(self, request):
        """
        Analiza el CV del usuario y extrae información estructurada
        """
        cv_text = request.POST.get('cv_text', '').strip()

        if not cv_text:
            return JsonResponse({
                'success': False,
                'error': 'Le texte du CV ne peut pas etre vide.'
            }, status=400)

        if len(cv_text) < 100:
            return JsonResponse({
                'success': False,
                'error': 'Le CV est trop court. Fournissez plus d\'informations sur votre experience.'
            }, status=400)

        # Verificar API key
        if not request.user.llm_api_key and request.user.llm_provider != 'ollama':
            return JsonResponse({
                'success': False,
                'error': 'Vous n\'avez pas configure de cle API. Configurez-la dans votre profil utilisateur.'
            }, status=400)

        try:
            # Crear agente para análisis
            from agent_ia_core.tools.cv_analyzer_tool import CVAnalyzerTool
            from agent_ia_core.agent_function_calling import FunctionCallingAgent

            # Determinar modelo
            if request.user.llm_provider == 'ollama':
                model = request.user.ollama_model or 'qwen2.5:7b'
            elif request.user.llm_provider == 'openai':
                model = request.user.openai_model or 'gpt-4o-mini'
            else:
                model = 'gemini-2.0-flash-exp'

            # Crear agente temporal para usar su LLM
            agent = FunctionCallingAgent(
                llm_provider=request.user.llm_provider,
                llm_model=model,
                llm_api_key=request.user.llm_api_key if request.user.llm_provider != 'ollama' else None,
                user=request.user,
            )

            # Usar la tool de análisis
            cv_tool = CVAnalyzerTool(llm=agent.llm)
            result = cv_tool.run(cv_text)

            # Verificar resultado
            if not result.get('success'):
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Error desconocido')
                }, status=400)

            extracted_data = result.get('data', {})

            # Actualizar perfil con datos extraídos
            profile, _ = UserProfile.objects.get_or_create(user=request.user)

            if extracted_data.get('skills'):
                profile.skills = extracted_data['skills']

            if extracted_data.get('experience'):
                profile.experience = extracted_data['experience']

            if extracted_data.get('education'):
                profile.education = extracted_data['education']

            if extracted_data.get('languages'):
                profile.languages = extracted_data['languages']

            if extracted_data.get('professional_summary'):
                profile.professional_summary = extracted_data['professional_summary']

            if extracted_data.get('preferred_sectors'):
                profile.preferred_sectors = extracted_data['preferred_sectors']

            profile.cv_analyzed = True
            profile.check_completeness()
            profile.save()

            return JsonResponse({
                'success': True,
                'data': extracted_data,
                'message': 'CV analyse correctement. Votre profil a ete mis a jour.'
            })

        except Exception as e:
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de l\'analyse du CV : {str(e)}'
            }, status=500)


class ExtractPDFTextView(LoginRequiredMixin, View):
    """Vista AJAX para extraer texto de un PDF"""

    def post(self, request):
        """Extrae texto de un archivo PDF subido"""
        if 'pdf_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Aucun fichier n\'a ete telecharge.'
            }, status=400)

        pdf_file = request.FILES['pdf_file']

        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'Le fichier doit etre un PDF.'
            }, status=400)

        try:
            # Intentar con PyPDF2
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            except ImportError:
                # Intentar con pdfminer
                try:
                    from pdfminer.high_level import extract_text
                    from io import BytesIO
                    pdf_file.seek(0)
                    text = extract_text(BytesIO(pdf_file.read()))
                except ImportError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Aucune librairie PDF installee. Installez PyPDF2 ou pdfminer.six'
                    }, status=500)

            text = text.strip()

            if not text:
                return JsonResponse({
                    'success': False,
                    'error': 'Le texte n\'a pas pu etre extrait du PDF. Il peut s\'agir d\'une image scannee.'
                }, status=400)

            return JsonResponse({
                'success': True,
                'text': text
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors du traitement du PDF : {str(e)}'
            }, status=500)


class AutocompleteLocationsView(View):
    """Vista API para autocompletado de ubicaciones"""

    def get(self, request):
        query = request.GET.get('q', '').strip().lower()

        # Ciudades principales de España
        locations = [
            "Alicante", "Barcelona", "Bilbao", "Córdoba", "Granada",
            "Las Palmas", "Madrid", "Málaga", "Murcia", "Oviedo",
            "Palma de Mallorca", "Pamplona", "San Sebastián", "Santa Cruz de Tenerife",
            "Santander", "Sevilla", "Valencia", "Valladolid", "Vigo", "Zaragoza",
            "A Coruña", "Castellón", "Cádiz", "Gijón", "Huelva", "Jerez",
            "Logroño", "Almería", "Burgos", "León", "Salamanca", "Toledo",
            "Remoto", "Híbrido", "España", "Europa"
        ]

        if query:
            results = [loc for loc in locations if query in loc.lower()]
        else:
            results = locations[:15]

        return JsonResponse({
            'results': [{'code': loc, 'name': loc, 'display': loc} for loc in results[:15]]
        })


class AutocompleteSectorsView(View):
    """Vista API para autocompletado de sectores"""

    def get(self, request):
        query = request.GET.get('q', '').strip().lower()

        sectors = [
            "Informática/IT", "Desarrollo de Software", "Data Science",
            "Ciberseguridad", "Cloud Computing", "DevOps",
            "Marketing Digital", "Marketing", "Comunicación",
            "Ventas", "Comercial", "Business Development",
            "Finanzas", "Contabilidad", "Auditoría",
            "Recursos Humanos", "RRHH", "Selección",
            "Ingeniería", "Ingeniería Civil", "Ingeniería Industrial",
            "Sanidad", "Medicina", "Enfermería",
            "Educación", "Formación", "E-learning",
            "Construcción", "Arquitectura",
            "Hostelería", "Turismo",
            "Logística", "Supply Chain",
            "Legal", "Abogacía",
            "Diseño", "UX/UI", "Diseño Gráfico",
            "Administración", "Secretariado"
        ]

        if query:
            results = [sec for sec in sectors if query in sec.lower()]
        else:
            results = sectors[:15]

        return JsonResponse({
            'results': [{'code': sec, 'name': sec, 'display': sec} for sec in results[:15]]
        })
