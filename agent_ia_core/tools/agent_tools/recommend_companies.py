# -*- coding: utf-8 -*-
"""
Tool para recomendar empresas ideales al usuario con contactos de reclutadores.
"""

import logging
from typing import Any, Dict, List
from ..core.base import BaseTool

logger = logging.getLogger(__name__)


class CompanyRecommendationTool(BaseTool):
    """
    Recomienda empresas ideales para el usuario basándose en su perfil.
    Incluye contactos de reclutadores, emails y estrategias de acceso.
    """

    name = "recommend_companies"
    description = """Recomienda empresas ideales para el usuario basándose en su perfil profesional.
    **USA ESTA TOOL cuando el usuario pida:** recomendaciones de empresas, dónde trabajar,
    empresas que encajen con su perfil, contactos de reclutadores, o cómo conseguir trabajo en una empresa.

    Devuelve:
    - Empresas recomendadas con justificación de por qué encajan
    - Contactos de reclutadores (LinkedIn, email si disponible)
    - Estrategia específica para conseguir trabajo en cada empresa
    - Ofertas actuales de cada empresa"""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None, user_profile=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        self.user_profile = user_profile
        super().__init__()

    def run(self, sector: str = "", location: str = "",
            company_size: str = "", specific_companies: str = "") -> dict:
        """
        Recomienda empresas y encuentra contactos de reclutadores.

        Args:
            sector: Sector de interés (ej: "Tecnología", "Finanzas")
            location: Ubicación preferida (ej: "Madrid", "Barcelona")
            company_size: Tamaño preferido: "startup", "pyme", "grande"
            specific_companies: Empresas específicas a investigar (separadas por coma)
        """

        results = {
            'success': True,
            'data': {
                'recommendations': [],
                'total_companies': 0,
                'search_context': {
                    'sector': sector,
                    'location': location,
                    'company_size': company_size
                }
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        try:
            # Determinar empresas a investigar
            companies_to_search = []

            if specific_companies:
                # Usuario especificó empresas concretas
                companies_to_search = [c.strip() for c in specific_companies.split(',')]
            else:
                # Buscar empresas por sector/ubicación
                companies_to_search = self._find_relevant_companies(sector, location, company_size)

            if not companies_to_search:
                results['data']['message'] = f"No se encontraron empresas para {sector or 'el sector especificado'} en {location or 'España'}"
                return results

            # Para cada empresa, obtener info completa
            for company_name in companies_to_search[:5]:  # Máximo 5 empresas
                company_data = self._get_company_recommendation(
                    company_name=company_name,
                    sector=sector,
                    location=location
                )
                if company_data:
                    results['data']['recommendations'].append(company_data)

            results['data']['total_companies'] = len(results['data']['recommendations'])

            if not results['data']['recommendations']:
                results['data']['message'] = "No se pudo obtener información detallada de las empresas."
            else:
                results['data']['message'] = f"Se encontraron {len(results['data']['recommendations'])} empresas recomendadas con contactos."

        except Exception as e:
            logger.error(f"Error en recommend_companies: {e}")
            results['success'] = False
            results['error'] = str(e)

        return results

    def _find_relevant_companies(self, sector: str, location: str, company_size: str) -> List[str]:
        """Encuentra empresas relevantes por sector y ubicación."""

        companies = []

        # Construir query de búsqueda
        size_term = ""
        if company_size == "startup":
            size_term = "startups"
        elif company_size == "grande":
            size_term = "grandes empresas multinacionales"

        queries = [
            f"mejores empresas {sector} {location} trabajar {size_term}".strip(),
            f"empresas {sector} {location} contratando empleo {size_term}".strip(),
        ]

        for query in queries:
            search_result = self.web_search_tool.run(query=query, limit=5)
            if search_result.get('success') and search_result.get('data', {}).get('results'):
                # Extraer nombres de empresas de los resultados
                for item in search_result['data']['results']:
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')

                    # Intentar extraer nombres de empresas del LLM
                    if self.llm:
                        extract_prompt = f"""Del siguiente texto, extrae SOLO los nombres de empresas mencionadas.
                        Devuelve una lista separada por comas, sin explicaciones.
                        Si no hay empresas claras, devuelve "NONE".

                        Título: {title}
                        Descripción: {snippet}

                        Empresas:"""

                        try:
                            response = self.llm.invoke(extract_prompt)
                            extracted = response.content if hasattr(response, 'content') else str(response)
                            if extracted and "NONE" not in extracted.upper():
                                for company in extracted.split(','):
                                    company = company.strip()
                                    if company and len(company) > 2 and company not in companies:
                                        companies.append(company)
                        except Exception as e:
                            logger.warning(f"Error extrayendo empresas: {e}")

        return companies[:10]  # Máximo 10 empresas candidatas

    def _get_company_recommendation(self, company_name: str, sector: str, location: str) -> Dict[str, Any]:
        """Obtiene información completa de una empresa con contactos."""

        company_data = {
            'company_name': company_name,
            'why_fits': '',
            'recruiters': [],
            'job_openings': [],
            'company_info': {},
            'strategy': '',
            'direct_links': {}
        }

        try:
            # 1. Buscar información general de la empresa
            company_query = f'"{company_name}" empresa about careers trabaja con nosotros'
            company_result = self.web_search_tool.run(query=company_query, limit=3)
            if company_result.get('success') and company_result.get('data', {}).get('results'):
                company_data['company_info']['search_results'] = company_result['data']['results']

            # 2. Buscar ofertas de empleo actuales
            jobs_query = f'site:linkedin.com/jobs OR site:infojobs.net "{company_name}" empleo'
            jobs_result = self.web_search_tool.run(query=jobs_query, limit=5)
            if jobs_result.get('success') and jobs_result.get('data', {}).get('results'):
                for job in jobs_result['data']['results']:
                    company_data['job_openings'].append({
                        'title': job.get('title', ''),
                        'url': job.get('url', ''),
                        'snippet': job.get('snippet', '')
                    })

            # 3. Buscar reclutadores en LinkedIn
            recruiter_queries = [
                f'site:linkedin.com/in "{company_name}" recruiter talent acquisition {location}',
                f'site:linkedin.com/in "{company_name}" "recursos humanos" HR {location}',
            ]

            seen_urls = set()
            for query in recruiter_queries:
                recruiter_result = self.web_search_tool.run(query=query, limit=5)
                if recruiter_result.get('success') and recruiter_result.get('data', {}).get('results'):
                    for item in recruiter_result['data']['results']:
                        url = item.get('url', '')
                        if 'linkedin.com/in/' in url and url not in seen_urls:
                            seen_urls.add(url)

                            recruiter_info = {
                                'name': item.get('title', '').replace(' | LinkedIn', '').replace(' - LinkedIn', ''),
                                'profile_url': url,
                                'description': item.get('snippet', ''),
                                'email': None  # Intentar extraer después
                            }

                            # Intentar extraer email del snippet
                            snippet = item.get('snippet', '')
                            import re
                            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', snippet)
                            if email_match:
                                recruiter_info['email'] = email_match.group()

                            company_data['recruiters'].append(recruiter_info)

            # 4. Buscar emails de contacto de la empresa
            email_query = f'"{company_name}" careers empleo contacto email @'
            email_result = self.web_search_tool.run(query=email_query, limit=3)
            if email_result.get('success') and email_result.get('data', {}).get('results'):
                import re
                for item in email_result['data']['results']:
                    snippet = item.get('snippet', '')
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', snippet)
                    if emails:
                        company_data['company_info']['contact_emails'] = list(set(emails))[:3]

            # 5. Links directos útiles
            company_data['direct_links'] = {
                'linkedin_company': f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}/jobs/",
                'linkedin_recruiters': f"https://www.linkedin.com/search/results/people/?keywords={company_name.replace(' ', '%20')}%20recruiter",
                'glassdoor': f"https://www.glassdoor.es/Opiniones/{company_name.replace(' ', '-')}-Opiniones",
            }

            # 6. Generar análisis con LLM
            if self.llm:
                # Contexto del perfil del usuario
                profile_context = ""
                if self.user_profile:
                    profile_context = f"""
                    Perfil del candidato:
                    - Habilidades: {', '.join(self.user_profile.get('skills', [])[:10])}
                    - Experiencia: {self.user_profile.get('experience', 'No especificada')}
                    - Ubicación preferida: {', '.join(self.user_profile.get('preferred_locations', [location]))}
                    - Sectores de interés: {', '.join(self.user_profile.get('preferred_sectors', [sector]))}
                    """

                analysis_prompt = f"""Analiza esta empresa para el candidato:

{profile_context}

Empresa: {company_name}
Sector: {sector or 'No especificado'}
Ubicación: {location or 'España'}
Ofertas encontradas: {len(company_data['job_openings'])}
Reclutadores encontrados: {len(company_data['recruiters'])}

Proporciona en formato estructurado:

1. **POR QUÉ ENCAJA** (3-5 razones específicas basadas en el perfil)

2. **ESTRATEGIA DE ACCESO** (pasos concretos para conseguir trabajo ahí):
   - Cómo contactar a los reclutadores
   - Qué mencionar en el mensaje
   - Mejor momento para aplicar
   - Cómo destacar sobre otros candidatos

3. **MENSAJE DE CONTACTO** (plantilla personalizada de máximo 300 caracteres para LinkedIn)

Sé específico y práctico."""

                try:
                    response = self.llm.invoke(analysis_prompt)
                    analysis = response.content if hasattr(response, 'content') else str(response)

                    # Parsear respuesta
                    if "POR QUÉ ENCAJA" in analysis:
                        parts = analysis.split("**ESTRATEGIA")
                        company_data['why_fits'] = parts[0].replace("**POR QUÉ ENCAJA**", "").strip()
                        if len(parts) > 1:
                            strategy_parts = parts[1].split("**MENSAJE")
                            company_data['strategy'] = strategy_parts[0].replace("DE ACCESO**", "").strip()
                            if len(strategy_parts) > 1:
                                company_data['contact_template'] = strategy_parts[1].replace("DE CONTACTO**", "").strip()
                    else:
                        company_data['why_fits'] = analysis

                except Exception as e:
                    logger.warning(f"Error generando análisis para {company_name}: {e}")
                    company_data['why_fits'] = f"Empresa del sector {sector} en {location}"

        except Exception as e:
            logger.error(f"Error obteniendo datos de {company_name}: {e}")
            return None

        return company_data

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'sector': {
                        'type': 'string',
                        'description': 'Sector de interés (ej: "Tecnología", "Finanzas", "Marketing")'
                    },
                    'location': {
                        'type': 'string',
                        'description': 'Ciudad o provincia preferida (ej: "Madrid", "Barcelona", "Alicante")'
                    },
                    'company_size': {
                        'type': 'string',
                        'description': 'Tamaño preferido de empresa: "startup", "pyme", "grande"'
                    },
                    'specific_companies': {
                        'type': 'string',
                        'description': 'Empresas específicas a investigar, separadas por coma (ej: "Google, Microsoft, Indra")'
                    }
                },
                'required': []
            }
        }
