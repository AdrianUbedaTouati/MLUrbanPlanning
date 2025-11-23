# -*- coding: utf-8 -*-
"""
Tools para búsqueda de ofertas de empleo usando web search.
"""

import json
import logging
from typing import Any
from ..core.base import BaseTool

logger = logging.getLogger(__name__)


class JobSearchTool(BaseTool):
    """Busca ofertas de empleo usando web search."""

    name = "search_jobs"
    description = """Busca ofertas de empleo en portales como InfoJobs, LinkedIn, Indeed y páginas de empresa usando web search.
    Analiza MUCHAS ofertas (~60) y devuelve las 15 más interesantes para el perfil del usuario.
    Incluye contacto del reclutador de cada oferta para contacto directo.
    Devuelve enlaces a ofertas reales verificadas con análisis de por qué son buenas opciones."""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None, user_profile=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        self.user_profile = user_profile
        super().__init__()

    def run(self, query: str, location: str = "", sector: str = "",
            job_type: str = "", contract_type: str = "") -> dict:
        """Busca ofertas de empleo, analiza muchas y devuelve las 10 mejores."""

        results = {
            'success': True,
            'data': {
                'query': query,
                'location': location,
                'sector': sector,
                'job_type': job_type,
                'jobs': [],
                'sources_searched': [],
                'total_analyzed': 0
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        try:
            # Auto-rellenar location desde user_profile si no se proporciona
            if not location and self.user_profile:
                location = self.user_profile.get('city', '')
                if location:
                    results['data']['location'] = location

            # Obtener modalidad de trabajo del usuario
            work_mode = ''
            if self.user_profile:
                work_mode = self.user_profile.get('work_mode', 'any')

            # Construir queries específicas para cada portal
            base_query = query
            if location:
                base_query += f" {location}"
            if sector:
                base_query += f" {sector}"
            if job_type:
                base_query += f" {job_type}"
            if contract_type:
                base_query += f" {contract_type}"

            # AÑADIR MODALIDAD A LA BÚSQUEDA (filtro estricto)
            work_mode_query = ""
            if work_mode == 'remote':
                work_mode_query = ' "100% remoto" OR "teletrabajo" OR "full remote"'
            elif work_mode == 'onsite':
                work_mode_query = ' "presencial"'
            elif work_mode == 'hybrid':
                work_mode_query = ' "híbrido" OR "flexible"'
            # Si es 'any' o vacío, no añadimos filtro

            all_jobs = []

            # 1. Buscar en InfoJobs (ofertas individuales)
            infojobs_query = f'site:infojobs.net/ofertas/trabajo "{base_query}"{work_mode_query}'
            infojobs_result = self.web_search_tool.run(query=infojobs_query, limit=10)
            if infojobs_result.get('success') and infojobs_result.get('data', {}).get('results'):
                for item in infojobs_result['data']['results']:
                    all_jobs.append({
                        'source': 'InfoJobs',
                        'title': item.get('title', ''),
                        'description': item.get('snippet', ''),
                        'url': item.get('url', ''),
                        'portal': 'infojobs.net'
                    })
                results['data']['sources_searched'].append('InfoJobs')

            # 2. Buscar en LinkedIn Jobs (ofertas individuales con /view/)
            linkedin_query = f'site:linkedin.com/jobs/view "{base_query}"{work_mode_query}'
            linkedin_result = self.web_search_tool.run(query=linkedin_query, limit=10)
            if linkedin_result.get('success') and linkedin_result.get('data', {}).get('results'):
                for item in linkedin_result['data']['results']:
                    all_jobs.append({
                        'source': 'LinkedIn',
                        'title': item.get('title', ''),
                        'description': item.get('snippet', ''),
                        'url': item.get('url', ''),
                        'portal': 'linkedin.com'
                    })
                results['data']['sources_searched'].append('LinkedIn')

            # 3. Buscar en Indeed (más resultados)
            indeed_query = f"site:indeed.es {base_query}{work_mode_query} empleo"
            indeed_result = self.web_search_tool.run(query=indeed_query, limit=10)
            if indeed_result.get('success') and indeed_result.get('data', {}).get('results'):
                for item in indeed_result['data']['results']:
                    all_jobs.append({
                        'source': 'Indeed',
                        'title': item.get('title', ''),
                        'description': item.get('snippet', ''),
                        'url': item.get('url', ''),
                        'portal': 'indeed.es'
                    })
                results['data']['sources_searched'].append('Indeed')

            # 4. Buscar en Tecnoempleo (específico para tech)
            if sector and 'tecnolog' in sector.lower() or 'programador' in query.lower() or 'developer' in query.lower():
                tecno_query = f"site:tecnoempleo.com {base_query}"
                tecno_result = self.web_search_tool.run(query=tecno_query, limit=10)
                if tecno_result.get('success') and tecno_result.get('data', {}).get('results'):
                    for item in tecno_result['data']['results']:
                        all_jobs.append({
                            'source': 'Tecnoempleo',
                            'title': item.get('title', ''),
                            'description': item.get('snippet', ''),
                            'url': item.get('url', ''),
                            'portal': 'tecnoempleo.com'
                        })
                    results['data']['sources_searched'].append('Tecnoempleo')

            # 5. Buscar en portales adicionales y páginas de empresa (~20 resultados extra)
            extra_jobs = self._search_extra_portals(base_query, location, sector)
            if extra_jobs:
                all_jobs.extend(extra_jobs)
                results['data']['sources_searched'].append('Portales Extra')

            results['data']['total_analyzed'] = len(all_jobs)

            if not all_jobs:
                results['data']['message'] = f"No se encontraron ofertas para '{query}' en {location or 'España'}. Prueba con otros términos."
                return results

            # 5. Deduplicar ofertas (misma empresa+título similar)
            deduplicated_jobs = self._deduplicate_jobs(all_jobs)
            results['data']['duplicates_removed'] = len(all_jobs) - len(deduplicated_jobs)
            logger.info(f"[JOB_SEARCH] Deduplicadas: {len(all_jobs)} → {len(deduplicated_jobs)} ofertas")

            # 5.5. Filtrar URLs de listados, mantener solo ofertas individuales
            individual_jobs = self._filter_individual_jobs(deduplicated_jobs)
            results['data']['listings_filtered'] = len(deduplicated_jobs) - len(individual_jobs)

            # 6. Usar LLM para filtrar y rankear las 15 mejores ofertas con scoring mejorado
            if self.llm and len(individual_jobs) > 15:
                top_jobs = self._rank_and_filter_jobs(individual_jobs, query, location, sector)
            else:
                # Sin LLM, devolver las primeras 15
                top_jobs = individual_jobs[:15]

            # 6. Verificar que las ofertas estén activas (si browse_tool está disponible)
            if self.browse_tool and top_jobs:
                verified_jobs = self._verify_active_jobs(top_jobs, all_jobs)
            else:
                verified_jobs = top_jobs

            # 7. Enriquecer ofertas con reclutadores y razonamientos profundos
            if self.web_search_tool and self.llm:
                enriched_jobs = self._enrich_jobs_with_recruiters(verified_jobs, query, location)
                results['data']['jobs'] = enriched_jobs
                results['data']['message'] = f"Analizadas {len(all_jobs)} ofertas, verificadas y enriquecidas con contactos de reclutadores."
            else:
                results['data']['jobs'] = verified_jobs
                results['data']['message'] = f"Analizadas {len(all_jobs)} ofertas, seleccionadas las 15 mejores de {', '.join(results['data']['sources_searched'])}."

        except Exception as e:
            logger.error(f"Error buscando empleos: {e}")
            results['success'] = False
            results['error'] = str(e)

        return results

    def _search_extra_portals(self, base_query: str, location: str, sector: str) -> list:
        """Busca en portales adicionales y páginas de empresa directamente."""

        extra_jobs = []

        # Portales adicionales españoles
        extra_searches = [
            # Portales de empleo adicionales
            (f"site:jobatus.es {base_query}", "Jobatus"),
            (f"site:trabajos.com {base_query}", "Trabajos.com"),
            (f"site:empleo.trovit.es {base_query}", "Trovit"),
            (f"site:talent.com/es {base_query}", "Talent.com"),
            (f"site:glassdoor.es {base_query} empleo", "Glassdoor"),

            # Búsqueda directa en páginas de empresa (careers/trabaja con nosotros)
            (f'"{base_query}" "trabaja con nosotros" OR "careers" OR "únete" {location}', "Páginas Empresa"),
            (f'"{base_query}" "oferta de empleo" -site:infojobs.net -site:linkedin.com -site:indeed.es {location}', "Web Directa"),

            # Portales especializados
            (f"site:domestika.org/empleo {base_query}", "Domestika") if 'diseñ' in base_query.lower() or 'creativ' in base_query.lower() else None,
            (f"site:getmanfred.com {base_query}", "Manfred") if any(t in base_query.lower() for t in ['developer', 'programador', 'software', 'tech']) else None,
            (f"site:welcometothejungle.com/es {base_query}", "Welcome Jungle"),
        ]

        for search_config in extra_searches:
            if search_config is None:
                continue

            search_query, source_name = search_config

            try:
                result = self.web_search_tool.run(query=search_query, limit=5)
                if result.get('success') and result.get('data', {}).get('results'):
                    for item in result['data']['results']:
                        url = item.get('url', '')
                        # Evitar duplicados de portales principales
                        if any(main in url for main in ['infojobs.net', 'linkedin.com/jobs', 'indeed.es', 'tecnoempleo.com']):
                            continue

                        extra_jobs.append({
                            'source': source_name,
                            'title': item.get('title', ''),
                            'description': item.get('snippet', ''),
                            'url': url,
                            'portal': self._extract_domain(url)
                        })

            except Exception as e:
                logger.warning(f"Error buscando en {source_name}: {e}")

        # Limitar a 20 resultados extra
        return extra_jobs[:20]

    def _extract_domain(self, url: str) -> str:
        """Extrae el dominio de una URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return 'web'

    def _deduplicate_jobs(self, jobs: list) -> list:
        """
        Elimina ofertas duplicadas basándose en empresa+título similar.
        Usa normalización de texto para detectar duplicados entre portales.
        """
        import re
        from difflib import SequenceMatcher

        def normalize(text: str) -> str:
            """Normaliza texto para comparación."""
            text = text.lower().strip()
            # Eliminar caracteres especiales y múltiples espacios
            text = re.sub(r'[^\w\s]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            # Eliminar palabras comunes que no aportan
            stopwords = ['en', 'de', 'para', 'con', 'the', 'and', 'or', 'in', 'at', 'to']
            words = [w for w in text.split() if w not in stopwords]
            return ' '.join(words)

        def extract_company(job: dict) -> str:
            """Extrae nombre de empresa del job."""
            title = job.get('title', '')
            # Patrones comunes: "Puesto at Empresa", "Puesto - Empresa", "Empresa | Puesto"
            patterns = [
                r'\bat\s+([A-Za-z0-9\s&]+?)(?:\s*[-|]|$)',
                r'[-|]\s*([A-Za-z0-9\s&]+?)$',
                r'^([A-Za-z0-9\s&]+?)\s*[-|]',
            ]
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    return normalize(match.group(1))
            return ""

        def similarity(a: str, b: str) -> float:
            """Calcula similaridad entre dos strings."""
            return SequenceMatcher(None, a, b).ratio()

        seen = []  # Lista de (normalized_title, company, original_job)
        unique_jobs = []

        for job in jobs:
            title_norm = normalize(job.get('title', ''))
            company = extract_company(job)

            is_duplicate = False
            for seen_title, seen_company, _ in seen:
                # Mismo título (>80% similar)
                title_sim = similarity(title_norm, seen_title)

                # Si títulos muy similares
                if title_sim > 0.8:
                    # Y misma empresa o empresa no detectada
                    if not company or not seen_company or similarity(company, seen_company) > 0.7:
                        is_duplicate = True
                        break

            if not is_duplicate:
                seen.append((title_norm, company, job))
                unique_jobs.append(job)

        return unique_jobs

    def _filter_individual_jobs(self, jobs: list) -> list:
        """
        Filtra URLs de listados de búsqueda y mantiene solo ofertas individuales.
        """
        import re

        # Patrones de URLs que son LISTADOS (no ofertas individuales)
        listing_patterns = [
            # InfoJobs listados
            r'infojobs\.net/trabajo(?:\?|$)',
            r'infojobs\.net/trabajo-de-',
            r'infojobs\.net/ofertas-empleo(?:\?|$)',
            r'infojobs\.net/empleo-de-',
            r'infojobs\.net/empleo-en-',
            # LinkedIn listados
            r'linkedin\.com/jobs/search',
            r'linkedin\.com/jobs\?',
            r'linkedin\.com/jobs$',
            # Indeed listados
            r'indeed\.es/jobs\?',
            r'indeed\.es/empleos\?',
            r'indeed\.es/q-',
            r'indeed\.es/trabajo\?',
            r'indeed\.es/l-',
            # Tecnoempleo listados
            r'tecnoempleo\.com/busqueda',
            r'tecnoempleo\.com/ofertas-',
            r'tecnoempleo\.com/empleo-',
            # Otros portales
            r'glassdoor\.es/Empleo/',
            r'glassdoor\.es/Trabajo/',
            r'trabajos\.com/trabajo/',
            r'trabajos\.com/empleos/',
            r'talent\.com/jobs/',
            r'talent\.com/es/jobs\?',
            r'trovit\.es/empleos/',
            r'jobatus\.es/trabajo/',
            r'getmanfred\.com/ofertas\?',
        ]

        # Patrones de URLs que son OFERTAS INDIVIDUALES
        individual_patterns = [
            # InfoJobs oferta individual (tiene ID numérico o path específico)
            r'infojobs\.net/[^/]+/oferta/',
            r'infojobs\.net/ofertas/trabajo/.+-\d+',
            r'infojobs\.net/oferta/.+',
            # LinkedIn oferta individual
            r'linkedin\.com/jobs/view/\d+',
            r'linkedin\.com/jobs/view/[a-zA-Z0-9-]+',
            # Indeed oferta individual
            r'indeed\.es/ver-empleo',
            r'indeed\.es/viewjob',
            r'indeed\.es/pagead/',
            r'indeed\.es/rc/clk',
            # Tecnoempleo oferta individual
            r'tecnoempleo\.com/[^/]+/[^/]+/rf-\w+',
            r'tecnoempleo\.com/oferta/',
            # Getmanfred oferta individual
            r'getmanfred\.com/offers/',
            # Glassdoor oferta individual
            r'glassdoor\.es/job-listing/',
            # Páginas de empresa (careers)
            r'/careers/',
            r'/trabaja-con-nosotros/',
            r'/empleo/',
            r'/jobs/',
            r'/job/',
            r'/vacante/',
        ]

        filtered_jobs = []

        for job in jobs:
            url = job.get('url', '')

            # Primero verificar si es un listado conocido
            is_listing = any(re.search(pattern, url) for pattern in listing_patterns)

            if is_listing:
                logger.debug(f"[JOB_SEARCH] Descartada URL de listado: {url[:60]}...")
                continue

            # Verificar si parece una oferta individual
            is_individual = any(re.search(pattern, url) for pattern in individual_patterns)

            # Si no coincide con patrones conocidos, aceptarla por defecto
            # (podría ser una página de empresa o portal menos conocido)
            if is_individual or not is_listing:
                filtered_jobs.append(job)
            else:
                logger.debug(f"[JOB_SEARCH] URL ambigua descartada: {url[:60]}...")

        logger.info(f"[JOB_SEARCH] Filtradas {len(jobs) - len(filtered_jobs)} URLs de listados, quedan {len(filtered_jobs)} ofertas")
        return filtered_jobs

    def _rank_and_filter_jobs(self, jobs: list, query: str, location: str, sector: str) -> list:
        """Usa el LLM para rankear y filtrar las mejores ofertas con scoring ponderado."""

        # Obtener modalidad de trabajo del usuario para el filtro
        work_mode = self.user_profile.get('work_mode', 'any') if self.user_profile else 'any'
        work_mode_text = {
            'any': 'Indiferente',
            'remote': 'Remoto',
            'onsite': 'Presencial',
            'hybrid': 'Híbrido'
        }.get(work_mode, 'Indiferente')

        # Crear lista de ofertas para análisis
        jobs_text = ""
        for i, job in enumerate(jobs):
            jobs_text += f"""
[{i+1}] {job['title']}
    Fuente: {job['source']}
    Descripción: {job['description'][:200]}
    URL: {job['url']}
"""

        ranking_prompt = f"""Analiza las siguientes {len(jobs)} ofertas de empleo y selecciona las 15 MEJORES usando el sistema de puntuación.

Búsqueda realizada: "{query}" en {location or 'España'}
Modalidad de trabajo preferida: {work_mode_text}

OFERTAS ENCONTRADAS:
{jobs_text}

SISTEMA DE PUNTUACIÓN (100 puntos máximo):

1. **MATCH DE TECNOLOGÍAS/HABILIDADES (35 puntos)**
   - 35 pts: Match perfecto con 3+ habilidades clave del candidato
   - 25 pts: Match bueno con 2 habilidades
   - 15 pts: Match parcial con 1 habilidad
   - 5 pts: Match indirecto o sector relacionado
   - 0 pts: Sin match aparente

2. **UBICACIÓN Y MODALIDAD (25 puntos) - FILTRO ESTRICTO**
   REGLAS OBLIGATORIAS:
   - Si el candidato especifica CIUDAD: la oferta DEBE ser de esa ciudad O 100% remota. DESCARTAR ofertas de otras ciudades.
   - Si modalidad = "Remoto": SOLO ofertas 100% remotas/teletrabajo. DESCARTAR presenciales e híbridas.
   - Si modalidad = "Presencial": SOLO ofertas presenciales en la ciudad indicada. DESCARTAR remotas.
   - Si modalidad = "Híbrido": ofertas híbridas o presenciales en la ciudad indicada.
   - Si modalidad = "Indiferente": no filtrar por modalidad, cualquier modalidad es válida.
   - Si NO hay ciudad especificada: cualquier ubicación en España es válida.

   PUNTUACIÓN (solo para ofertas que pasen el filtro):
   - 25 pts: Cumple perfectamente con ubicación Y modalidad
   - 15 pts: Cumple parcialmente (ej: híbrido cuando prefiere remoto)
   - 0 pts: No cumple - DESCARTAR de la selección

3. **SALARIO Y BENEFICIOS (20 puntos)**
   - 20 pts: Salario mencionado y competitivo para el puesto
   - 15 pts: Salario mencionado en rango medio
   - 10 pts: Beneficios mencionados (seguro, bonus, etc.)
   - 5 pts: Descripción sugiere buen paquete
   - 0 pts: Sin información salarial

4. **CALIDAD DE LA OFERTA (10 puntos)**
   - 10 pts: Descripción detallada, empresa conocida/reputada
   - 7 pts: Buena descripción, empresa establecida
   - 4 pts: Descripción básica pero clara
   - 0 pts: Descripción pobre o sospechosa

5. **TIPO DE CONTRATO (10 puntos)**
   - 10 pts: Indefinido mencionado
   - 7 pts: Contrato estable implícito
   - 4 pts: Temporal con posibilidad de conversión
   - 0 pts: Temporal, prácticas o no especificado

INSTRUCCIONES:
- Evalúa CADA oferta con este sistema de puntos
- Devuelve SOLO los números de las 15 mejores ofertas, ordenadas de MAYOR a MENOR puntuación
- Formato: número,número,número... (ej: 3,7,1,15,8,12,4,9,6,2,5,11,14,13,10)
- NO incluyas explicaciones, SOLO los números separados por comas

SELECCIÓN (15 números ordenados por puntuación):"""

        try:
            response = self.llm.invoke(ranking_prompt)
            selection_text = response.content if hasattr(response, 'content') else str(response)

            # Parsear la respuesta
            import re
            numbers = re.findall(r'\d+', selection_text)
            selected_indices = []

            for num in numbers:
                idx = int(num) - 1  # Convertir a índice 0-based
                if 0 <= idx < len(jobs) and idx not in selected_indices:
                    selected_indices.append(idx)
                if len(selected_indices) >= 15:
                    break

            # Construir lista de jobs seleccionados
            selected_jobs = []
            for idx in selected_indices:
                job = jobs[idx].copy()
                job['rank'] = len(selected_jobs) + 1
                selected_jobs.append(job)

            # Si no se obtuvieron suficientes, completar con los primeros
            if len(selected_jobs) < 15:
                for job in jobs:
                    if job not in [jobs[i] for i in selected_indices]:
                        job_copy = job.copy()
                        job_copy['rank'] = len(selected_jobs) + 1
                        selected_jobs.append(job_copy)
                        if len(selected_jobs) >= 15:
                            break

            return selected_jobs

        except Exception as e:
            logger.warning(f"Error rankeando ofertas con LLM: {e}")
            # Fallback: devolver las primeras 15
            return [dict(job, rank=i+1) for i, job in enumerate(jobs[:15])]

    def _verify_active_jobs(self, top_jobs: list, all_jobs: list) -> list:
        """Verifica que las ofertas estén activas y reemplaza las inactivas."""

        verified_jobs = []
        used_urls = set()
        backup_jobs = [j for j in all_jobs if j not in top_jobs]
        backup_index = 0

        for job in top_jobs:
            url = job.get('url', '')
            if not url or url in used_urls:
                continue

            # Verificar si la oferta está activa (ahora retorna dict)
            check_result = self._check_job_active(url)

            if check_result.get('is_active', True):
                # Enriquecer job con datos del análisis
                enriched_job = job.copy()
                if check_result.get('job_details'):
                    enriched_job['verified_details'] = check_result['job_details']
                if check_result.get('fit_analysis'):
                    enriched_job['fit_analysis'] = check_result['fit_analysis']
                enriched_job['verification'] = {
                    'status': 'active',
                    'confidence': check_result.get('confidence', 'media'),
                    'reason': check_result.get('reason', '')
                }

                verified_jobs.append(enriched_job)
                used_urls.add(url)
                logger.info(f"[JOB_SEARCH] ✓ Oferta activa: {url[:50]}... ({check_result.get('confidence', 'media')})")
            else:
                logger.info(f"[JOB_SEARCH] ✗ Oferta inactiva: {url[:50]}... Razón: {check_result.get('reason', 'desconocida')}")

                # Buscar reemplazo en ofertas de backup
                while backup_index < len(backup_jobs):
                    backup_job = backup_jobs[backup_index]
                    backup_url = backup_job.get('url', '')
                    backup_index += 1

                    if backup_url and backup_url not in used_urls:
                        backup_check = self._check_job_active(backup_url)
                        if backup_check.get('is_active', True):
                            enriched_backup = backup_job.copy()
                            enriched_backup['rank'] = len(verified_jobs) + 1
                            enriched_backup['replaced_inactive'] = True
                            if backup_check.get('job_details'):
                                enriched_backup['verified_details'] = backup_check['job_details']
                            if backup_check.get('fit_analysis'):
                                enriched_backup['fit_analysis'] = backup_check['fit_analysis']
                            enriched_backup['verification'] = {
                                'status': 'active',
                                'confidence': backup_check.get('confidence', 'media'),
                                'reason': backup_check.get('reason', '')
                            }

                            verified_jobs.append(enriched_backup)
                            used_urls.add(backup_url)
                            logger.info(f"[JOB_SEARCH] ↻ Reemplazada con: {backup_url[:50]}...")
                            break

            # Limitar a 15 ofertas verificadas
            if len(verified_jobs) >= 15:
                break

        return verified_jobs

    def _check_job_active(self, url: str) -> dict:
        """
        Verifica si una oferta sigue activa usando LLM para análisis inteligente.

        Returns:
            dict con:
                - is_active: bool
                - reason: str (razón de la decisión)
                - job_details: dict (detalles extraídos si está activa)
        """

        if not self.browse_tool:
            return {'is_active': True, 'reason': 'Sin browse_tool disponible', 'job_details': {}}

        try:
            # Obtener contenido de la página
            result = self.browse_tool.run(
                url=url,
                extract_type="text",
                max_chars=4000  # Más contenido para mejor análisis
            )

            if not result.get('success'):
                return {'is_active': False, 'reason': 'Error al acceder a la página', 'job_details': {}}

            content = result.get('data', {}).get('content', '')

            if len(content) < 100:
                return {'is_active': False, 'reason': 'Página sin contenido suficiente', 'job_details': {}}

            # Usar LLM para análisis inteligente
            if self.llm:
                return self._analyze_job_page_with_llm(url, content)
            else:
                # Fallback a verificación básica si no hay LLM
                return self._basic_job_check(content)

        except Exception as e:
            logger.warning(f"Error verificando oferta {url}: {e}")
            return {'is_active': True, 'reason': f'Error: {str(e)}', 'job_details': {}}

    def _analyze_job_page_with_llm(self, url: str, content: str) -> dict:
        """Analiza la página de la oferta con LLM para determinar si está activa."""

        # Obtener información del perfil del usuario para fit_analysis personalizado
        user_context = ""
        if self.user_profile:
            city = self.user_profile.get('city', '')
            work_mode = self.user_profile.get('work_mode', '')
            if city or work_mode:
                user_context = f"\nPERFIL DEL CANDIDATO:\n- Ciudad: {city or 'No especificada'}\n- Modalidad preferida: {work_mode or 'Indiferente'}\n"

        analysis_prompt = f"""Analiza esta página de oferta de empleo y responde en formato JSON estricto.

URL: {url}
{user_context}
CONTENIDO DE LA PÁGINA:
{content[:3500]}

INSTRUCCIONES:
Analiza el contenido y determina:
1. Si la oferta sigue ACTIVA y acepta candidaturas
2. Extrae los detalles clave de la oferta
3. Genera un análisis detallado de por qué esta oferta encaja con un candidato técnico

RESPONDE ÚNICAMENTE con este JSON (sin texto adicional):
{{
    "is_active": true/false,
    "confidence": "alta/media/baja",
    "reason": "explicación breve de por qué está activa o no",
    "job_details": {{
        "title": "título del puesto",
        "company": "nombre de la empresa",
        "location": "ubicación",
        "salary": "salario si se menciona o null",
        "contract_type": "tipo de contrato si se menciona o null",
        "requirements": ["requisito1", "requisito2"],
        "publish_date": "fecha de publicación si aparece o null"
    }},
    "fit_analysis": "Análisis DETALLADO y ESPECÍFICO de por qué esta oferta encaja. DEBE incluir: 1) Tecnologías/herramientas específicas mencionadas que coinciden, 2) Nivel de experiencia requerido vs experiencia típica, 3) Responsabilidades concretas del puesto, 4) Aspectos diferenciadores de esta oferta. Mínimo 3-4 oraciones con datos concretos de la oferta."
}}

CRITERIOS PARA DETERMINAR SI ESTÁ ACTIVA:
- INACTIVA si: menciona que ya no acepta solicitudes, está cerrada, expirada, finalizada, proceso completado
- INACTIVA si: la página muestra error 404, "no encontrado", o redirige a página de búsqueda
- INACTIVA si: dice explícitamente que la vacante ya no está disponible
- ACTIVA si: tiene botón de aplicar, formulario de candidatura, o instrucciones para aplicar
- ACTIVA si: muestra detalles completos del puesto sin mencionar cierre

IMPORTANTE para fit_analysis:
- NO uses frases genéricas como "tu formación te hace ideal"
- MENCIONA tecnologías específicas de la oferta (Python, React, AWS, etc.)
- INDICA requisitos concretos (años de experiencia, certificaciones)
- DESCRIBE responsabilidades reales del puesto
- SÉ ESPECÍFICO con datos de la oferta, no generalidades
- Si hay PERFIL DEL CANDIDATO, compara la ubicación/modalidad con lo que ofrece el puesto

Responde SOLO con el JSON, sin explicaciones adicionales."""

        try:
            response = self.llm.invoke(analysis_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Parsear JSON de la respuesta
            import json
            import re

            # Extraer JSON del texto (por si viene con texto adicional)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                analysis = json.loads(json_match.group())

                return {
                    'is_active': analysis.get('is_active', True),
                    'reason': analysis.get('reason', ''),
                    'confidence': analysis.get('confidence', 'media'),
                    'job_details': analysis.get('job_details', {}),
                    'fit_analysis': analysis.get('fit_analysis', '')
                }

        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON del análisis: {e}")
        except Exception as e:
            logger.warning(f"Error en análisis LLM: {e}")

        # Fallback si falla el análisis LLM
        return self._basic_job_check(content)

    def _basic_job_check(self, content: str) -> dict:
        """Verificación básica sin LLM (fallback)."""

        content_lower = content.lower()

        # Indicadores de que la oferta está INACTIVA
        inactive_indicators = [
            'esta oferta ya no está disponible',
            'oferta caducada', 'oferta expirada',
            'no longer accepting applications',
            'ya no acepta solicitudes',
            'this job is no longer available',
            'solicitudes cerradas', 'applications closed',
            'job not found', 'page not found', '404',
            'proceso cerrado', 'vacante cerrada',
            'oferta finalizada', 'ha finalizado',
            'error 404', 'página no encontrada',
            'contenido no disponible'
        ]

        for indicator in inactive_indicators:
            if indicator in content_lower:
                return {
                    'is_active': False,
                    'reason': f'Detectado indicador de inactividad: {indicator}',
                    'job_details': {}
                }

        # Indicadores de que es una PÁGINA DE LISTADO (no una oferta individual)
        listing_indicators = [
            'mostrando resultados',
            'ofertas encontradas',
            'empleos encontrados',
            'resultados de búsqueda',
            'filtrar por',
            'ordenar por fecha',
            'páginas de resultados',
            'ver más ofertas',
            'siguiente página'
        ]

        listing_count = sum(1 for indicator in listing_indicators if indicator in content_lower)
        if listing_count >= 2:
            return {
                'is_active': False,
                'reason': 'Página de listado de búsqueda, no una oferta individual',
                'job_details': {}
            }

        return {
            'is_active': True,
            'reason': 'No se detectaron indicadores de inactividad',
            'job_details': {}
        }

    def _enrich_jobs_with_recruiters(self, jobs: list, query: str, location: str) -> list:
        """Enriquece cada oferta con contacto del reclutador verificado."""

        enriched_jobs = []

        for job in jobs[:15]:  # Limitar a 15 para no hacer demasiadas búsquedas
            enriched_job = job.copy()

            try:
                # Extraer nombre de empresa - priorizar verified_details
                company_name = None

                # 1. Primero de verified_details (más fiable)
                if job.get('verified_details', {}).get('company'):
                    company_name = job['verified_details']['company']
                else:
                    # 2. Extraer del título/descripción
                    company_name = self._extract_company_name(job)

                if company_name:
                    # Buscar reclutador de esa empresa con verificación
                    recruiter_info = self._find_verified_recruiter(company_name, location)
                    if recruiter_info:
                        enriched_job['recruiter'] = recruiter_info
                        logger.info(f"[JOB_SEARCH] ✓ Reclutador encontrado para {company_name}: {recruiter_info.get('name')}")
                    else:
                        # Mensaje claro cuando no se encuentra reclutador verificado
                        enriched_job['recruiter'] = {
                            'verified': False,
                            'message': f'No se encontró reclutador verificado para {company_name}'
                        }
                        logger.info(f"[JOB_SEARCH] ✗ No se encontró reclutador verificado para {company_name}")

            except Exception as e:
                logger.warning(f"Error enriqueciendo oferta: {e}")

            enriched_jobs.append(enriched_job)

        return enriched_jobs

    def _extract_company_name(self, job: dict) -> str:
        """Extrae el nombre de la empresa del título o descripción de la oferta."""

        # 1. Primero verificar si ya tenemos verified_details
        if job.get('verified_details', {}).get('company'):
            return job['verified_details']['company']

        title = job.get('title', '')
        description = job.get('description', '')

        # Patrones comunes en títulos de ofertas
        import re

        # Patrón "at Company" - común en LinkedIn
        at_match = re.search(r'\bat\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\s*[-|]|$)', title)
        if at_match:
            return at_match.group(1).strip()

        # Patrón "- Company" o "| Company" al final
        end_match = re.search(r'[-|]\s*([A-Z][A-Za-z0-9\s&\-\.]+?)$', title)
        if end_match:
            return end_match.group(1).strip()

        # Patrón "Company -" o "Company |" al inicio
        dash_match = re.search(r'^([A-Z][A-Za-z0-9\s&\-\.]+?)\s*[-|]', title)
        if dash_match:
            return dash_match.group(1).strip()

        # Buscar en descripción con patrones más amplios
        company_patterns = [
            r'empresa[:\s]+([A-Za-z0-9\s&\-\.]+)',
            r'company[:\s]+([A-Za-z0-9\s&\-\.]+)',
            r'en\s+([A-Z][A-Za-z0-9\s&\-\.]+?)\s+buscamos',
            r'([A-Z][A-Za-z0-9\s&\-\.]+?)\s+está buscando',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Filtrar palabras genéricas
                if company.lower() not in ['la', 'una', 'nuestra', 'esta']:
                    return company

        return ""

    def _find_verified_recruiter(self, company_name: str, location: str) -> dict:
        """
        Busca un reclutador VERIFICADO de la empresa.
        Solo devuelve resultados si el snippet confirma que trabaja en esa empresa.
        """

        if not self.web_search_tool or not company_name:
            return None

        # Normalizar nombre de empresa para comparación
        company_lower = company_name.lower().strip()
        # Variantes comunes del nombre
        company_variants = [
            company_lower,
            company_lower.replace(' ', ''),
            company_lower.split()[0] if company_lower else ''  # Primera palabra
        ]

        try:
            # Búsquedas más específicas
            recruiter_queries = [
                f'site:linkedin.com/in "{company_name}" "Talent Acquisition" OR "Recruiter" OR "RRHH"',
                f'site:linkedin.com/in "{company_name}" "People" OR "HR" OR "Hiring"',
            ]

            for query in recruiter_queries:
                result = self.web_search_tool.run(query=query, limit=5)
                if result.get('success') and result.get('data', {}).get('results'):
                    for item in result['data']['results']:
                        url = item.get('url', '')
                        title = item.get('title', '')
                        snippet = item.get('snippet', '')

                        # Verificar que es un perfil de LinkedIn
                        if 'linkedin.com/in/' not in url:
                            continue

                        # VERIFICACIÓN: El snippet debe mencionar la empresa
                        snippet_lower = snippet.lower()
                        title_lower = title.lower()

                        # Buscar variantes del nombre de empresa en el snippet o título
                        company_confirmed = any(
                            variant in snippet_lower or variant in title_lower
                            for variant in company_variants if variant
                        )

                        if not company_confirmed:
                            continue

                        # Verificar que es un rol de reclutamiento
                        recruiting_keywords = [
                            'talent', 'recruiter', 'recruiting', 'rrhh', 'hr ',
                            'people', 'hiring', 'acquisition', 'recursos humanos',
                            'selección', 'headhunter'
                        ]

                        is_recruiter = any(kw in snippet_lower or kw in title_lower for kw in recruiting_keywords)

                        if not is_recruiter:
                            continue

                        # Extraer nombre limpio
                        name = title.replace(' | LinkedIn', '').replace(' - LinkedIn', '').strip()

                        # Extraer rol del snippet
                        role = snippet[:200] if snippet else ''

                        return {
                            'name': name,
                            'linkedin_url': url,
                            'role': role,
                            'company': company_name,
                            'verified': True
                        }

        except Exception as e:
            logger.warning(f"Error buscando reclutador verificado para {company_name}: {e}")

        return None

    def _find_job_recruiter(self, company_name: str, job_title: str, location: str) -> dict:
        """Método legacy - redirige a _find_verified_recruiter."""
        return self._find_verified_recruiter(company_name, location)

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Palabras clave de búsqueda (ej: "programador python", "diseñador UX")'
                    },
                    'location': {
                        'type': 'string',
                        'description': 'Ciudad o provincia (ej: "Alicante", "Madrid", "Barcelona")'
                    },
                    'sector': {
                        'type': 'string',
                        'description': 'Sector laboral (ej: "Informática", "Marketing", "Finanzas")'
                    },
                    'job_type': {
                        'type': 'string',
                        'description': 'Tipo de trabajo: "Remoto", "Presencial", "Híbrido"'
                    },
                    'contract_type': {
                        'type': 'string',
                        'description': 'Tipo de contrato: "Indefinido", "Temporal", "Freelance"'
                    }
                },
                'required': ['query']
            }
        }


class SearchJobsByRankingTool(BaseTool):
    """Busca ofertas para cada puesto del ranking del usuario."""

    name = "search_jobs_by_ranking"
    description = """Busca ofertas de empleo basándose en el ranking de puestos recomendados del usuario.
    Busca 10 ofertas por cada puesto del ranking y devuelve las 3 mejores para cada uno.
    **USA ESTA TOOL cuando el usuario pida:** búsqueda basada en su perfil, ofertas para sus puestos recomendados,
    o una búsqueda completa según su ranking."""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None, user_profile=None, user=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        self.user_profile = user_profile
        self.user = user
        super().__init__()

    def run(self, location: str = "", top_n: int = 3) -> dict:
        """Busca ofertas para cada puesto del ranking del usuario.

        Args:
            location: Ciudad o provincia para la búsqueda
            top_n: Número de mejores ofertas a devolver por puesto (default: 3)
        """

        results = {
            'success': True,
            'data': {
                'location': location,
                'top_n': top_n,
                'ranking_jobs': [],
                'total_analyzed': 0,
                'total_selected': 0
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        if not self.llm:
            return {
                'success': False,
                'error': 'LLM no disponible para análisis.'
            }

        try:
            # Obtener ranking de puestos del usuario
            ranking_positions = self._extract_ranking_positions()

            if not ranking_positions:
                return {
                    'success': False,
                    'error': 'No se encontró ranking de puestos. Asegúrate de tener un CV analizado.'
                }

            # Auto-rellenar location
            if not location and self.user_profile:
                location = self.user_profile.get('city', '')

            # Buscar ofertas para cada puesto del ranking
            for position in ranking_positions:
                position_results = self._search_for_position(position, location, top_n)
                if position_results:
                    results['data']['ranking_jobs'].append(position_results)
                    results['data']['total_analyzed'] += position_results.get('analyzed', 0)
                    results['data']['total_selected'] += len(position_results.get('jobs', []))

            if not results['data']['ranking_jobs']:
                results['data']['message'] = 'No se encontraron ofertas para los puestos del ranking.'
            else:
                results['data']['message'] = f"Búsqueda completada: {results['data']['total_selected']} ofertas seleccionadas de {results['data']['total_analyzed']} analizadas."

        except Exception as e:
            logger.error(f"Error en búsqueda por ranking: {e}")
            results['success'] = False
            results['error'] = str(e)

        return results

    def _extract_ranking_positions(self) -> list:
        """Extrae los puestos del ranking del perfil del usuario desde cv_summary."""

        try:
            from apps.company.models import UserProfile
            import re

            # Acceso directo al cv_summary del usuario
            if self.user:
                profile = UserProfile.objects.filter(user=self.user).first()
                if profile and profile.cv_summary:
                    cv_summary = profile.cv_summary

                    # Extraer puestos del ranking del cv_summary
                    # Buscar sección de ranking de puestos
                    ranking_section = re.search(
                        r'(?:ranking|puestos recomendados|posiciones recomendadas)[:\s]*(.+?)(?:\n\n|\Z)',
                        cv_summary,
                        re.IGNORECASE | re.DOTALL
                    )

                    if ranking_section:
                        # Extraer nombres de puestos (líneas con números o bullets)
                        positions_text = ranking_section.group(1)
                        positions = re.findall(
                            r'(?:\d+[\.\)]\s*|\-\s*|\*\s*)([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\n|$|:|\()',
                            positions_text
                        )
                        if positions:
                            return [p.strip() for p in positions if p.strip()]

                    # Fallback: usar LLM para extraer del cv_summary
                    if self.llm:
                        prompt = f"""Extrae los nombres de los puestos del ranking de puestos recomendados de este CV summary:

{cv_summary[:2000]}

Devuelve SOLO una lista JSON con los nombres de los puestos.
Formato: ["Puesto 1", "Puesto 2", "Puesto 3"]

Si no hay ranking, devuelve: []"""

                        response = self.llm.invoke(prompt)
                        response_text = response.content if hasattr(response, 'content') else str(response)

                        json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())

            # Fallback si no hay user: usar LLM con contexto de conversación
            if self.llm:
                prompt = """Basándote en el contexto de la conversación, extrae los nombres de los puestos
del ranking de puestos recomendados del usuario.

Devuelve SOLO una lista JSON con los nombres de TODOS los puestos del ranking.
Formato: ["Puesto 1", "Puesto 2", "Puesto 3", ...]

Si no hay ranking disponible, devuelve: []"""

                response = self.llm.invoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)

                json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())

            return []

        except Exception as e:
            logger.warning(f"Error extrayendo puestos del ranking: {e}")
            return []

    def _search_for_position(self, position: str, location: str, top_n: int = 3) -> dict:
        """Busca ofertas para un puesto específico y devuelve las top_n mejores."""

        try:
            all_jobs = []

            # Búsquedas mejoradas para obtener ofertas INDIVIDUALES (no listados)
            # Usar términos que filtren páginas de ofertas específicas
            searches = [
                # InfoJobs: buscar en URLs de ofertas específicas
                (f'site:infojobs.net/ofertas/trabajo "{position}" {location}', "InfoJobs", 4),
                # LinkedIn: URLs con /view/ son ofertas individuales
                (f'site:linkedin.com/jobs/view "{position}" {location}', "LinkedIn", 3),
                # Indeed: usar viewjob para ofertas específicas
                (f'site:indeed.es "{position}" {location} empleo', "Indeed", 3),
            ]

            for query, source, limit in searches:
                result = self.web_search_tool.run(query=query, limit=limit)
                if result.get('success') and result.get('data', {}).get('results'):
                    for item in result['data']['results']:
                        all_jobs.append({
                            'source': source,
                            'title': item.get('title', ''),
                            'description': item.get('snippet', ''),
                            'url': item.get('url', ''),
                            'portal': source.lower()
                        })

            if not all_jobs:
                return {
                    'position': position,
                    'jobs': [],
                    'analyzed': 0,
                    'message': f'No se encontraron ofertas para {position}'
                }

            # Filtrar URLs de listados usando el método de JobSearchTool
            job_search_tool = JobSearchTool(
                llm=self.llm,
                web_search_tool=self.web_search_tool,
                browse_tool=self.browse_tool,
                user_profile=self.user_profile
            )
            filtered_jobs = job_search_tool._filter_individual_jobs(all_jobs)

            if not filtered_jobs:
                return {
                    'position': position,
                    'jobs': [],
                    'analyzed': len(all_jobs),
                    'message': f'No se encontraron ofertas individuales para {position} (todas eran listados)'
                }

            # Seleccionar las top_n mejores usando LLM
            top_jobs = self._select_top_jobs(filtered_jobs, position, location, top_n)

            return {
                'position': position,
                'jobs': top_jobs,
                'analyzed': len(all_jobs),
                'selected': len(top_jobs)
            }

        except Exception as e:
            logger.warning(f"Error buscando ofertas para {position}: {e}")
            return {
                'position': position,
                'jobs': [],
                'analyzed': 0,
                'error': str(e)
            }

    def _select_top_jobs(self, jobs: list, position: str, location: str, top_n: int = 3) -> list:
        """Usa el LLM para seleccionar las top_n mejores ofertas."""

        if len(jobs) <= top_n:
            return jobs

        jobs_text = ""
        for i, job in enumerate(jobs):
            jobs_text += f"[{i+1}] {job['title']}\n    {job['description'][:150]}\n    URL: {job['url']}\n"

        prompt = f"""Selecciona las {top_n} MEJORES ofertas para el puesto "{position}" en {location or 'España'}.

OFERTAS:
{jobs_text}

CRITERIOS:
1. Relevancia con el puesto buscado
2. Calidad de la descripción
3. Empresa reconocida

Devuelve SOLO los {top_n} números de las mejores ofertas, separados por comas.
Ejemplo: 2,5,1

SELECCIÓN:"""

        try:
            response = self.llm.invoke(prompt)
            selection = response.content if hasattr(response, 'content') else str(response)

            import re
            numbers = re.findall(r'\d+', selection)
            selected = []

            for num in numbers:
                idx = int(num) - 1
                if 0 <= idx < len(jobs) and jobs[idx] not in selected:
                    selected.append(jobs[idx])
                if len(selected) >= top_n:
                    break

            # Completar si faltan
            if len(selected) < top_n:
                for job in jobs:
                    if job not in selected:
                        selected.append(job)
                        if len(selected) >= top_n:
                            break

            return selected

        except Exception as e:
            logger.warning(f"Error seleccionando ofertas: {e}")
            return jobs[:top_n]

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'location': {
                        'type': 'string',
                        'description': 'Ciudad o provincia para la búsqueda (opcional, usa la del perfil si no se especifica)'
                    },
                    'top_n': {
                        'type': 'integer',
                        'description': 'Número de mejores ofertas a devolver por cada puesto del ranking (default: 3)',
                        'default': 3
                    }
                },
                'required': []
            }
        }


class SearchRecentJobsTool(BaseTool):
    """Busca las ofertas de empleo más recientes usando web search."""

    name = "search_recent_jobs"
    description = """Busca las ofertas de empleo MÁS RECIENTES publicadas en las últimas 24-48 horas.
    **USA ESTA TOOL cuando el usuario pida:** ofertas recientes, últimas ofertas, ofertas nuevas,
    ofertas publicadas hoy, o después de haber visto las mejores ofertas generales.

    Filtra por fecha de publicación y prioriza las más nuevas.
    Devuelve las 15 ofertas más recientes con verificación y contacto de reclutadores."""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None, user_profile=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        self.user_profile = user_profile
        super().__init__()

    def run(self, query: str, location: str = "", sector: str = "") -> dict:
        """Busca ofertas de empleo recientes (últimas 24-48h)."""

        results = {
            'success': True,
            'data': {
                'query': query,
                'location': location,
                'sector': sector,
                'jobs': [],
                'sources_searched': [],
                'total_analyzed': 0,
                'filter': 'recent_24h'
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        try:
            base_query = query
            if location:
                base_query += f" {location}"
            if sector:
                base_query += f" {sector}"

            all_jobs = []

            # Búsquedas específicas para ofertas recientes
            recent_searches = [
                # InfoJobs con filtro de fecha
                (f"site:infojobs.net {base_query} empleo", "InfoJobs"),
                # LinkedIn Jobs recientes
                (f"site:linkedin.com/jobs {base_query} publicado hoy OR ayer", "LinkedIn"),
                # Indeed con filtro reciente
                (f"site:indeed.es {base_query} empleo publicado últimas 24 horas", "Indeed"),
                # Tecnoempleo
                (f"site:tecnoempleo.com {base_query}", "Tecnoempleo"),
                # Búsqueda general con términos de reciente
                (f'{base_query} empleo "publicado hoy" OR "hace 1 día" OR "recién publicado"', "General"),
                # Portales extra
                (f"site:jobatus.es {base_query}", "Jobatus"),
                (f"site:talent.com/es {base_query}", "Talent.com"),
            ]

            for search_query, source_name in recent_searches:
                try:
                    result = self.web_search_tool.run(query=search_query, limit=8)
                    if result.get('success') and result.get('data', {}).get('results'):
                        for item in result['data']['results']:
                            all_jobs.append({
                                'source': source_name,
                                'title': item.get('title', ''),
                                'description': item.get('snippet', ''),
                                'url': item.get('url', ''),
                                'portal': source_name.lower().replace(' ', '')
                            })
                        results['data']['sources_searched'].append(source_name)
                except Exception as e:
                    logger.warning(f"Error buscando en {source_name}: {e}")

            results['data']['total_analyzed'] = len(all_jobs)

            if not all_jobs:
                results['data']['message'] = f"No se encontraron ofertas recientes para '{query}'"
                return results

            # Deduplicar
            from difflib import SequenceMatcher
            import re

            def normalize(text):
                text = text.lower().strip()
                text = re.sub(r'[^\w\s]', ' ', text)
                return re.sub(r'\s+', ' ', text)

            unique_jobs = []
            seen_titles = []
            for job in all_jobs:
                title_norm = normalize(job.get('title', ''))
                is_dup = any(SequenceMatcher(None, title_norm, seen).ratio() > 0.8 for seen in seen_titles)
                if not is_dup:
                    seen_titles.append(title_norm)
                    unique_jobs.append(job)

            # Reutilizar métodos de JobSearchTool
            job_search_tool = JobSearchTool(
                llm=self.llm,
                web_search_tool=self.web_search_tool,
                browse_tool=self.browse_tool,
                user_profile=self.user_profile
            )

            # Filtrar URLs de listados
            individual_jobs = job_search_tool._filter_individual_jobs(unique_jobs)

            # Rankear por recencia usando LLM
            if self.llm and len(individual_jobs) > 15:
                top_jobs = self._rank_recent_jobs(individual_jobs, query, location)
            else:
                top_jobs = individual_jobs[:15]

            if self.browse_tool:
                verified_jobs = job_search_tool._verify_active_jobs(top_jobs, unique_jobs)
            else:
                verified_jobs = top_jobs

            if self.web_search_tool and self.llm:
                enriched_jobs = job_search_tool._enrich_jobs_with_recruiters(verified_jobs, query, location)
                results['data']['jobs'] = enriched_jobs
            else:
                results['data']['jobs'] = verified_jobs

            results['data']['message'] = f"Encontradas {len(results['data']['jobs'])} ofertas recientes de {len(all_jobs)} analizadas."

        except Exception as e:
            logger.error(f"Error buscando ofertas recientes: {e}")
            results['success'] = False
            results['error'] = str(e)

        return results

    def _rank_recent_jobs(self, jobs: list, query: str, location: str) -> list:
        """Rankea ofertas priorizando las más recientes."""

        jobs_text = ""
        for i, job in enumerate(jobs[:40]):
            jobs_text += f"[{i+1}] {job['title']} - {job['source']}\n    {job['description'][:150]}\n"

        ranking_prompt = f"""Selecciona las 15 ofertas MÁS RECIENTES y relevantes.

Búsqueda: "{query}" en {location or 'España'}

OFERTAS:
{jobs_text}

CRITERIOS (prioridad):
1. **RECENCIA (50%)**: Indicadores de publicación reciente ("hoy", "ayer", "hace X horas/días", "recién publicado")
2. **RELEVANCIA (30%)**: Match con la búsqueda realizada
3. **CALIDAD (20%)**: Descripción clara, empresa reconocida

Devuelve SOLO los 15 números de las ofertas más recientes y relevantes, ordenados.
Formato: número,número,número...

SELECCIÓN:"""

        try:
            response = self.llm.invoke(ranking_prompt)
            selection = response.content if hasattr(response, 'content') else str(response)

            import re
            numbers = re.findall(r'\d+', selection)
            selected = []

            for num in numbers:
                idx = int(num) - 1
                if 0 <= idx < len(jobs) and idx not in [s['idx'] for s in selected if 'idx' in s]:
                    job = jobs[idx].copy()
                    job['rank'] = len(selected) + 1
                    job['idx'] = idx
                    selected.append(job)
                if len(selected) >= 15:
                    break

            # Completar si faltan
            if len(selected) < 15:
                for i, job in enumerate(jobs):
                    if i not in [s.get('idx', -1) for s in selected]:
                        job_copy = job.copy()
                        job_copy['rank'] = len(selected) + 1
                        selected.append(job_copy)
                        if len(selected) >= 15:
                            break

            return selected

        except Exception as e:
            logger.warning(f"Error rankeando ofertas recientes: {e}")
            return jobs[:15]

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'Palabras clave de búsqueda (ej: "programador python", "diseñador UX")'
                    },
                    'location': {
                        'type': 'string',
                        'description': 'Ciudad o provincia (ej: "Alicante", "Madrid")'
                    },
                    'sector': {
                        'type': 'string',
                        'description': 'Sector laboral (ej: "Informática", "Marketing")'
                    }
                },
                'required': ['query']
            }
        }


class CompanySearchTool(BaseTool):
    """Busca información sobre empresas usando web search."""

    name = "search_companies"
    description = """Busca empresas por sector y ubicación usando web search.
    Encuentra información sobre empresas que están contratando, su cultura y ofertas disponibles.
    Útil para investigar empresas objetivo antes de aplicar."""

    def __init__(self, llm=None, web_search_tool=None, browse_tool=None):
        self.llm = llm
        self.web_search_tool = web_search_tool
        self.browse_tool = browse_tool
        super().__init__()

    def run(self, sector: str = "", location: str = "",
            company_name: str = "", size: str = "") -> dict:
        """Busca información sobre empresas."""

        results = {
            'success': True,
            'data': {
                'sector': sector,
                'location': location,
                'company_name': company_name,
                'companies': [],
                'insights': ''
            }
        }

        if not self.web_search_tool:
            return {
                'success': False,
                'error': 'Web search no disponible. Configura Google Search API en tu perfil.'
            }

        try:
            if company_name:
                # Buscar empresa específica
                queries = [
                    f"{company_name} empresa trabaja con nosotros careers",
                    f"{company_name} opiniones empleados glassdoor",
                    f"site:linkedin.com/company {company_name}"
                ]
            else:
                # Buscar empresas por sector/ubicación
                base = f"empresas {sector} {location} empleo trabaja con nosotros".strip()
                queries = [
                    base,
                    f"mejores empresas {sector} {location} trabajar",
                    f"startups {sector} {location}" if size == 'startup' else f"empresas grandes {sector} {location}"
                ]

            all_companies = []
            for query in queries[:2]:  # Limitar a 2 búsquedas
                search_result = self.web_search_tool.run(query=query, limit=5)
                if search_result.get('success') and search_result.get('data', {}).get('results'):
                    for item in search_result['data']['results']:
                        all_companies.append({
                            'title': item.get('title', ''),
                            'description': item.get('snippet', ''),
                            'url': item.get('url', ''),
                            'query_used': query
                        })

            results['data']['companies'] = all_companies
            results['data']['total_found'] = len(all_companies)

            # Generar insights con LLM si está disponible
            if self.llm and (sector or company_name):
                insight_prompt = f"""Basándote en una búsqueda de empresas:
                - Sector: {sector or 'No especificado'}
                - Ubicación: {location or 'España'}
                - Empresa específica: {company_name or 'No especificada'}

                Proporciona 3-5 consejos prácticos para:
                1. Cómo investigar estas empresas antes de aplicar
                2. Qué buscar en sus páginas de "Trabaja con nosotros"
                3. Cómo destacar en la candidatura

                Sé conciso y práctico."""

                try:
                    response = self.llm.invoke(insight_prompt)
                    results['data']['insights'] = response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    logger.warning(f"Error generando insights: {e}")

        except Exception as e:
            logger.error(f"Error buscando empresas: {e}")
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
                    'sector': {
                        'type': 'string',
                        'description': 'Sector de la empresa (ej: "Tecnología", "Consultoría", "Marketing")'
                    },
                    'location': {
                        'type': 'string',
                        'description': 'Ciudad o provincia donde buscar empresas'
                    },
                    'company_name': {
                        'type': 'string',
                        'description': 'Nombre específico de empresa a investigar'
                    },
                    'size': {
                        'type': 'string',
                        'description': 'Tamaño de empresa: "startup", "pyme", "grande"'
                    }
                },
                'required': []
            }
        }


class JobMatchTool(BaseTool):
    """Evalúa compatibilidad entre perfil y oferta."""

    name = "match_job_profile"
    description = """Evalúa la compatibilidad entre el perfil del usuario y una oferta de empleo.
    Proporciona un análisis de match, puntos fuertes, áreas de mejora y recomendaciones.
    Usar cuando el usuario quiere saber si encaja en una oferta específica."""

    def __init__(self, llm=None, user_profile=None):
        self.llm = llm
        self.user_profile = user_profile
        super().__init__()

    def run(self, job_description: str, job_requirements: str = "") -> dict:
        """Evalúa match entre perfil y oferta."""

        if not self.llm:
            return {
                'success': False,
                'error': 'LLM no configurado para análisis de compatibilidad'
            }

        profile_context = ""
        if self.user_profile:
            profile_context = f"""
            Perfil del candidato:
            - Habilidades: {', '.join(self.user_profile.get('skills', []))}
            - Experiencia: {len(self.user_profile.get('experience', []))} posiciones anteriores
            - Formación: {len(self.user_profile.get('education', []))} títulos
            - Idiomas: {', '.join([l.get('language', '') for l in self.user_profile.get('languages', [])])}
            - Ubicación preferida: {', '.join(self.user_profile.get('preferred_locations', []))}
            - Sectores de interés: {', '.join(self.user_profile.get('preferred_sectors', []))}
            """

        prompt = f"""Evalúa la compatibilidad entre el candidato y esta oferta de empleo.

{profile_context}

Oferta de empleo:
{job_description}

Requisitos adicionales:
{job_requirements or 'No especificados'}

Proporciona un análisis estructurado:

1. **Score de compatibilidad**: X/100
2. **Puntos fuertes** del candidato para esta oferta (3-5 puntos)
3. **Áreas de mejora** o gaps a trabajar (2-3 puntos)
4. **Recomendaciones** específicas para la candidatura
5. **Preguntas** que debería preparar para la entrevista (3-5)

Sé específico y práctico en tu análisis."""

        try:
            response = self.llm.invoke(prompt)
            analysis = response.content if hasattr(response, 'content') else str(response)

            return {
                'success': True,
                'data': {
                    'analysis': analysis,
                    'job_description_length': len(job_description),
                    'has_profile': bool(self.user_profile)
                }
            }

        except Exception as e:
            logger.error(f"Error evaluando match: {e}")
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
                    'job_description': {
                        'type': 'string',
                        'description': 'Descripción completa de la oferta de empleo'
                    },
                    'job_requirements': {
                        'type': 'string',
                        'description': 'Requisitos específicos del puesto'
                    }
                },
                'required': ['job_description']
            }
        }
