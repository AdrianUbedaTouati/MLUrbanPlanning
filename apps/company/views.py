import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from .models import CompanyProfile
from .services import CompanyProfileAIService


class CompanyProfileView(LoginRequiredMixin, View):
    """Vista para ver y editar el perfil de empresa"""
    template_name = 'company/profile.html'

    def get(self, request):
        # Obtener o crear el perfil de empresa del usuario
        profile, created = CompanyProfile.objects.get_or_create(user=request.user)

        # Preparar datos para el template
        context = {
            'form': profile,  # Usamos el objeto directamente
            'cpv_codes_json': json.dumps(profile.preferred_cpv_codes or []),
            'nuts_regions_json': json.dumps(profile.preferred_nuts_regions or []),
            'budget_min': profile.budget_range.get('min', '') if profile.budget_range else '',
            'budget_max': profile.budget_range.get('max', '') if profile.budget_range else '',
        }

        return render(request, self.template_name, context)

    def post(self, request):
        # Obtener o crear el perfil de empresa del usuario
        profile, created = CompanyProfile.objects.get_or_create(user=request.user)

        try:
            # Campos básicos
            profile.company_name = request.POST.get('company_name', '').strip()
            profile.company_description_text = request.POST.get('company_description_text', '').strip()

            # Número de empleados
            employees_str = request.POST.get('employees', '').strip()
            profile.employees = int(employees_str) if employees_str else None

            # Campos JSON (tags)
            # Los campos vienen como JSON strings desde los inputs ocultos
            cpv_codes_json = request.POST.get('preferred_cpv_codes', '[]')
            profile.preferred_cpv_codes = json.loads(cpv_codes_json) if cpv_codes_json else []

            nuts_regions_json = request.POST.get('preferred_nuts_regions', '[]')
            nuts_regions = json.loads(nuts_regions_json) if nuts_regions_json else []

            # Si incluye "ES-ALL" (Toda España), expandir a todas las regiones
            if 'ES-ALL' in nuts_regions:
                # Importar lista completa de regiones NUTS españolas
                from agent_ia_core.prompts_config import NUTS_CODES_LIST
                # Obtener solo los códigos (primer elemento de cada tupla)
                all_spain_codes = [code for code, name in NUTS_CODES_LIST if code.startswith('ES')]
                # Combinar con las regiones seleccionadas manualmente (sin duplicados)
                nuts_regions = list(set(nuts_regions + all_spain_codes))
                # Remover el marcador "ES-ALL"
                nuts_regions = [r for r in nuts_regions if r != 'ES-ALL']

            profile.preferred_nuts_regions = nuts_regions

            # Budget range
            budget_min = request.POST.get('budget_min', '').strip()
            budget_max = request.POST.get('budget_max', '').strip()

            if budget_min or budget_max:
                profile.budget_range = {
                    'min': int(budget_min) if budget_min else 0,
                    'max': int(budget_max) if budget_max else 0
                }
            else:
                profile.budget_range = {}

            # Marcar como completo si tiene nombre
            profile.is_complete = bool(profile.company_name)

            profile.save()

            messages.success(request, 'Perfil de empresa actualizado correctamente.')
            return redirect('company:profile')

        except json.JSONDecodeError as e:
            messages.error(request, f'Error al procesar los datos: {str(e)}')
            return redirect('company:profile')

        except ValueError as e:
            messages.error(request, f'Error en los datos numéricos: {str(e)}')
            return redirect('company:profile')

        except Exception as e:
            messages.error(request, f'Error al guardar el perfil: {str(e)}')
            return redirect('company:profile')


class ExtractCompanyInfoView(LoginRequiredMixin, View):
    """Vista AJAX para extraer información de texto libre con IA"""

    def post(self, request):
        """
        Extrae información estructurada del texto libre usando LLM

        Expected POST data:
            - company_text: str (texto libre sobre la empresa)

        Returns:
            JSON response with extracted fields
        """
        company_text = request.POST.get('company_text', '').strip()

        if not company_text:
            return JsonResponse({
                'success': False,
                'error': 'El texto de la empresa no puede estar vacío.'
            }, status=400)

        # Verificar que el usuario tenga API key configurada
        if not request.user.llm_api_key:
            return JsonResponse({
                'success': False,
                'error': 'No tienes configurada una API key. Por favor, configúrala en tu perfil de usuario.'
            }, status=400)

        try:
            # Initialize service with user's API key
            service = CompanyProfileAIService(request.user)

            # Extract information
            extracted_data = service.extract_company_info(company_text)

            # Validate data
            validated_data = service.validate_extracted_data(extracted_data)

            return JsonResponse({
                'success': True,
                'data': validated_data,
                'message': 'Información extraída correctamente. Revisa y ajusta los campos si es necesario.'
            })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

        except Exception as e:
            # Log the error for debugging
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'success': False,
                'error': f'Error al procesar la información: {str(e)}'
            }, status=500)


class AutocompleteNUTSView(View):
    """Vista API para autocompletado de códigos NUTS"""

    def get(self, request):
        """
        Busca códigos NUTS que coincidan con el query

        Query params:
            - q: término de búsqueda (vacío = sugerencias por defecto)
        """
        from agent_ia_core.prompts_config import NUTS_CODES_LIST, SPAIN_NUTS_MAPPING

        query = request.GET.get('q', '').strip().lower()

        results = []
        seen_codes = set()

        # Si no hay query, devolver las regiones más importantes por defecto
        if not query:
            # OPCIÓN ESPECIAL: Toda España (expande a todas las regiones)
            results.append({
                'code': 'ES-ALL',
                'name': 'TODA ESPAÑA',
                'display': '🇪🇸 TODA ESPAÑA (todas las regiones)'
            })

            # Top NUTS regions más importantes
            top_nuts_regions = [
                ("ES30", "Madrid"),
                ("ES511", "Barcelona"),
                ("ES523", "Valencia / València"),
                ("ES618", "Sevilla"),
                ("ES617", "Málaga"),
                ("ES213", "Bizkaia"),
                ("ES243", "Zaragoza"),
                ("ES521", "Alicante / Alacant"),
                ("ES61", "Andalucía"),
                ("ES51", "Cataluña"),
                ("ES52", "Comunidad Valenciana"),
                ("ES21", "País Vasco / Euskadi"),
                ("ES11", "Galicia"),
                ("ES12", "Principado de Asturias"),
                ("ES62", "Región de Murcia"),
            ]

            for code, name in top_nuts_regions:
                if code not in seen_codes:
                    results.append({
                        'code': code,
                        'name': name,
                        'display': f"{name} ({code})"
                    })
                    seen_codes.add(code)

            return JsonResponse({'results': results})

        # Si buscan "toda", "españa", "all", mostrar la opción especial primero
        if any(word in query for word in ['toda', 'españa', 'all', 'todo', 'completa']):
            results.append({
                'code': 'ES-ALL',
                'name': 'TODA ESPAÑA',
                'display': '🇪🇸 TODA ESPAÑA (todas las regiones)'
            })

        # Buscar en el mapeo de nombres
        for name, (code, official_name) in SPAIN_NUTS_MAPPING.items():
            if query in name.lower() and code not in seen_codes:
                results.append({
                    'code': code,
                    'name': official_name,
                    'display': f"{official_name} ({code})"
                })
                seen_codes.add(code)

        # Buscar en la lista de códigos
        for code, name in NUTS_CODES_LIST:
            if code not in seen_codes:
                if query in code.lower() or query in name.lower():
                    results.append({
                        'code': code,
                        'name': name,
                        'display': f"{name} ({code})"
                    })
                    seen_codes.add(code)

        # Limitar resultados a 15
        results = results[:15]

        return JsonResponse({'results': results})


class AutocompleteCPVView(View):
    """Vista API para autocompletado de códigos CPV"""

    def get(self, request):
        """
        Busca códigos CPV que coincidan con el query

        Query params:
            - q: término de búsqueda (vacío = sugerencias por defecto)
        """
        from agent_ia_core.prompts_config import CPV_CODES_LIST, CPV_CODE_KEYWORDS_EXPANDED

        query = request.GET.get('q', '').strip().lower()

        results = []
        seen_codes = set()

        # Si no hay query, devolver los códigos más importantes por defecto
        if not query:
            # Top CPV codes más usados
            top_cpv_codes = [
                "7226", "7240", "7267",  # Software
                "7210", "7220", "7114",  # Consultoría
                "4500", "4520", "4521",  # Construcción
                "7122", "7130", "7131",  # Arquitectura e Ingeniería
                "9013", "9031",          # Limpieza
                "7934", "9311",          # Seguridad
                "5523", "5524",          # Catering
                "8060", "8041",          # Formación
            ]

            for code in top_cpv_codes:
                if code not in seen_codes:
                    desc = next((d for c, d in CPV_CODES_LIST if c == code), f"CPV {code}")
                    results.append({
                        'code': code,
                        'name': desc,
                        'display': f"{code} - {desc}"
                    })
                    seen_codes.add(code)

            return JsonResponse({'results': results[:15]})

        # Si el query es numérico, buscar por código
        if query.isdigit():
            for code, description in CPV_CODES_LIST:
                if code.startswith(query) and code not in seen_codes:
                    results.append({
                        'code': code,
                        'name': description,
                        'display': f"{code} - {description}"
                    })
                    seen_codes.add(code)
        else:
            # Buscar en palabras clave primero
            for keyword, codes in CPV_CODE_KEYWORDS_EXPANDED.items():
                if query in keyword.lower():
                    for code in codes:
                        if code not in seen_codes:
                            # Encontrar la descripción del código
                            desc = next((d for c, d in CPV_CODES_LIST if c == code), f"CPV {code}")
                            results.append({
                                'code': code,
                                'name': desc,
                                'display': f"{code} - {desc}"
                            })
                            seen_codes.add(code)

            # Buscar en las descripciones de códigos
            for code, description in CPV_CODES_LIST:
                if code not in seen_codes and query in description.lower():
                    results.append({
                        'code': code,
                        'name': description,
                        'display': f"{code} - {description}"
                    })
                    seen_codes.add(code)

        # Limitar resultados a 15
        results = results[:15]

        return JsonResponse({'results': results})
