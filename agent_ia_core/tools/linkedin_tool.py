# -*- coding: utf-8 -*-
"""
Tool para búsqueda de reclutadores y contactos en LinkedIn usando web search.
"""

import json
import logging
from typing import Any
from .base import BaseTool

logger = logging.getLogger(__name__)


class LinkedInRecruiterTool(BaseTool):
    """Busca reclutadores y contactos de RRHH en LinkedIn usando web search."""

    name = "find_linkedin_recruiters"
    description = """Busca reclutadores, talent acquisition y contactos de RRHH en LinkedIn.
    Encuentra personas clave para networking y envío de candidaturas directas.
    Proporciona URLs de perfiles de LinkedIn y consejos para contactarlos."""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        super().__init__()

    def run(self, company_name: str, location: str = "España",
            role_type: str = "recruiter") -> dict:
        """Busca reclutadores en LinkedIn."""

        results = {
            'success': True,
            'data': {
                'company': company_name,
                'location': location,
                'recruiters': [],
                'search_tips': [],
                'outreach_template': '',
                'direct_search_urls': []
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        try:
            # Búsquedas específicas para encontrar reclutadores
            search_queries = [
                f'site:linkedin.com/in "{company_name}" recruiter {location}',
                f'site:linkedin.com/in "{company_name}" talent acquisition {location}',
                f'site:linkedin.com/in "{company_name}" "recursos humanos" OR "HR" {location}',
            ]

            all_recruiters = []
            for query in search_queries:
                search_result = self.web_search_tool.run(query=query, limit=5)
                if search_result.get('success') and search_result.get('data', {}).get('results'):
                    for item in search_result['data']['results']:
                        # Filtrar solo perfiles de LinkedIn
                        url = item.get('url', '')
                        if 'linkedin.com/in/' in url:
                            all_recruiters.append({
                                'name': item.get('title', '').replace(' | LinkedIn', '').replace(' - LinkedIn', ''),
                                'description': item.get('snippet', ''),
                                'profile_url': url,
                                'search_query': query
                            })

            # Eliminar duplicados por URL
            seen_urls = set()
            unique_recruiters = []
            for r in all_recruiters:
                if r['profile_url'] not in seen_urls:
                    seen_urls.add(r['profile_url'])
                    unique_recruiters.append(r)

            results['data']['recruiters'] = unique_recruiters[:10]  # Máximo 10
            results['data']['total_found'] = len(unique_recruiters)

            # URLs de búsqueda directa en LinkedIn
            results['data']['direct_search_urls'] = [
                f"https://www.linkedin.com/search/results/people/?keywords={company_name}%20recruiter&origin=GLOBAL_SEARCH_HEADER",
                f"https://www.linkedin.com/search/results/people/?keywords={company_name}%20talent%20acquisition&origin=GLOBAL_SEARCH_HEADER",
                f"https://www.linkedin.com/search/results/people/?keywords={company_name}%20HR&origin=GLOBAL_SEARCH_HEADER",
            ]

            # Tips de búsqueda
            results['data']['search_tips'] = [
                f"Busca en LinkedIn: '{company_name} recruiter' o 'talent acquisition'",
                "Filtra por ubicación y conexiones de 2º grado",
                "Revisa quién ha publicado ofertas de la empresa recientemente",
                "Conecta con varios reclutadores, no solo uno",
                "Personaliza cada mensaje de conexión mencionando por qué te interesa la empresa"
            ]

            # Generar plantilla de mensaje con LLM
            if self.llm:
                template_prompt = f"""Crea una plantilla de mensaje corto (máximo 300 caracteres) para solicitar conexión en LinkedIn a un reclutador de {company_name}.

El mensaje debe:
1. Ser profesional y personalizado
2. Mencionar interés específico en la empresa
3. No parecer spam
4. Incluir marcadores: [NOMBRE_RECLUTADOR], [PUESTO_INTERES]

Proporciona solo la plantilla, sin explicaciones adicionales."""

                try:
                    response = self.llm.invoke(template_prompt)
                    results['data']['outreach_template'] = response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    logger.warning(f"Error generando plantilla: {e}")
                    results['data']['outreach_template'] = f"Hola [NOMBRE_RECLUTADOR], estoy muy interesado en oportunidades de [PUESTO_INTERES] en {company_name}. Me encantaría conectar y conocer más sobre la cultura y proyectos del equipo. ¡Gracias!"

        except Exception as e:
            logger.error(f"Error buscando reclutadores: {e}")
            results['success'] = False
            results['error'] = str(e)

        return results

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'company_name': {
                        'type': 'string',
                        'description': 'Nombre de la empresa donde buscar reclutadores'
                    },
                    'location': {
                        'type': 'string',
                        'description': 'Ubicación para filtrar (ej: "España", "Madrid")'
                    },
                    'role_type': {
                        'type': 'string',
                        'description': 'Tipo de rol: "recruiter", "hr", "talent"'
                    }
                },
                'required': ['company_name']
            }
        }


class LinkedInCompanyTool(BaseTool):
    """Obtiene información de empresa en LinkedIn usando web search."""

    name = "get_linkedin_company"
    description = """Obtiene información de una empresa en LinkedIn usando web search.
    Incluye datos sobre la empresa, cultura, número de empleados y ofertas abiertas.
    Útil para investigar una empresa antes de aplicar."""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        super().__init__()

    def run(self, company_name: str) -> dict:
        """Obtiene información de empresa."""

        results = {
            'success': True,
            'data': {
                'company': company_name,
                'company_info': [],
                'job_openings': [],
                'insights': ''
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        try:
            # Buscar página de empresa en LinkedIn
            company_query = f'site:linkedin.com/company "{company_name}"'
            company_result = self.web_search_tool.run(query=company_query, limit=3)
            if company_result.get('success') and company_result.get('data', {}).get('results'):
                results['data']['company_info'] = company_result['data']['results']

            # Buscar ofertas de empleo de la empresa
            jobs_query = f'site:linkedin.com/jobs "{company_name}"'
            jobs_result = self.web_search_tool.run(query=jobs_query, limit=5)
            if jobs_result.get('success') and jobs_result.get('data', {}).get('results'):
                results['data']['job_openings'] = jobs_result['data']['results']

            # Buscar información adicional (glassdoor, reviews)
            reviews_query = f'{company_name} opiniones empleados glassdoor'
            reviews_result = self.web_search_tool.run(query=reviews_query, limit=3)
            if reviews_result.get('success') and reviews_result.get('data', {}).get('results'):
                results['data']['employee_reviews'] = reviews_result['data']['results']

            # Generar insights con LLM
            if self.llm:
                insight_prompt = f"""Para la empresa {company_name}, proporciona:

1. Qué deberías investigar en su página de LinkedIn antes de aplicar
2. 3 preguntas para preparar sobre la cultura empresarial
3. Cómo destacar en una candidatura para esta empresa
4. Señales de alerta (red flags) a tener en cuenta

Sé práctico y específico. Máximo 200 palabras."""

                try:
                    response = self.llm.invoke(insight_prompt)
                    results['data']['insights'] = response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    logger.warning(f"Error generando insights: {e}")

        except Exception as e:
            logger.error(f"Error obteniendo info de empresa: {e}")
            results['success'] = False
            results['error'] = str(e)

        return results

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'company_name': {
                        'type': 'string',
                        'description': 'Nombre de la empresa a investigar'
                    }
                },
                'required': ['company_name']
            }
        }


class ProfileSuggestionsTool(BaseTool):
    """Sugiere mejoras para el perfil de LinkedIn."""

    name = "suggest_profile_improvements"
    description = """Analiza el perfil del usuario y sugiere mejoras para LinkedIn.
    Incluye optimización de titular, resumen, skills y palabras clave.
    Útil para mejorar la visibilidad y atraer reclutadores."""

    def __init__(self, llm=None, user_profile=None):
        self.llm = llm
        self.user_profile = user_profile
        super().__init__()

    def run(self, target_role: str = "", current_headline: str = "") -> dict:
        """Genera sugerencias para mejorar perfil."""

        if not self.llm:
            return {
                'success': False,
                'error': 'LLM no configurado para generar sugerencias'
            }

        profile_context = ""
        if self.user_profile:
            profile_context = f"""
            Perfil actual:
            - Habilidades: {', '.join(self.user_profile.get('skills', [])[:10])}
            - Experiencia: {len(self.user_profile.get('experience', []))} posiciones
            - Resumen: {self.user_profile.get('professional_summary', 'No definido')[:200]}
            """

        prompt = f"""Actúa como experto en LinkedIn y personal branding.

{profile_context}

Rol objetivo: {target_role or 'No especificado'}
Titular actual: {current_headline or 'No proporcionado'}

Proporciona:

1. **Titulares optimizados** (3 opciones, máximo 120 caracteres cada uno)
   - Incluye palabras clave relevantes para el rol objetivo

2. **Estructura del "Acerca de"** (qué incluir en cada párrafo)
   - Gancho inicial
   - Propuesta de valor
   - Logros destacados
   - Call to action

3. **Palabras clave SEO** (10 términos para aparecer en búsquedas)

4. **Skills recomendadas** (10 habilidades para añadir)

5. **Contenido a publicar** (3 tipos de posts para aumentar visibilidad)

6. **Errores a evitar** (5 errores comunes en LinkedIn)

Sé específico y práctico."""

        try:
            response = self.llm.invoke(prompt)
            suggestions = response.content if hasattr(response, 'content') else str(response)

            return {
                'success': True,
                'data': {
                    'suggestions': suggestions,
                    'target_role': target_role,
                    'has_profile': bool(self.user_profile)
                }
            }

        except Exception as e:
            logger.error(f"Error generando sugerencias: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'target_role': {
                        'type': 'string',
                        'description': 'Rol objetivo que busca el usuario'
                    },
                    'current_headline': {
                        'type': 'string',
                        'description': 'Titular actual de LinkedIn (si lo tiene)'
                    }
                },
                'required': []
            }
        }
