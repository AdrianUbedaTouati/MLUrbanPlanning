# -*- coding: utf-8 -*-
"""
Servicio para descargar licitaciones desde la API de TED y guardarlas en la BD.
Adaptado de Agent_IA/src/descarga_xml.py
"""

import requests
from pathlib import Path
from datetime import date, timedelta
import re
import time
from typing import Optional, Dict, Any, List
from django.conf import settings
from .models import Tender
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import sys

# Import logging system
agent_ia_path = os.path.join(settings.BASE_DIR, 'agent_ia_core')
if agent_ia_path not in sys.path:
    sys.path.insert(0, agent_ia_path)
from apps.core.logging_config import ObtenerLogger

# Import EFormsXMLParser for robust XML parsing
try:
    from agent_ia_core.parser.xml_parser import EFormsXMLParser
    EFORMS_PARSER_AVAILABLE = True
except ImportError:
    EFORMS_PARSER_AVAILABLE = False
    print("WARNING: EFormsXMLParser not available, using legacy parser")

# URLs y configuración
SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

# Configuración por defecto
DEFAULT_CPV = "classification-cpv=72*"  # Servicios de TI (todos los códigos 72*)
DEFAULT_PLACE = "place-of-performance=ESP"
DEFAULT_NOTICE_TYPE = "notice-type=cn-standard"
DEFAULT_DAYS_BACK = 30
DEFAULT_WINDOW_DAYS = 7
DEFAULT_MAX_DOWNLOAD = 50
TIMEOUT = 60
DOWNLOAD_DELAY = 1.2  # segundos entre requests

# Directorio para guardar XMLs (importar desde agent_ia_core.config)
try:
    from agent_ia_core.config import XML_DIR
except ImportError:
    # Fallback si no se puede importar
    XML_DIR = Path(__file__).parent.parent / "data" / "xml"
MAX_RETRIES = 3  # Número máximo de reintentos
BACKOFF_FACTOR = 2  # Factor de backoff exponencial

# Regex para números de publicación
PUBNUM_RE = re.compile(r"\b\d{6,8}-\d{4}\b")

# Mapeo de códigos eForms a valores del modelo Tender
PROCEDURE_TYPE_MAP = {
    'open': 'open',
    'restricted': 'restricted',
    'neg-w-call': 'negotiated',
    'neg-wo-call': 'negotiated',
    'comp-dial': 'competitive_dialogue',
    'innovation': 'competitive_dialogue',
    'oth-single': 'open',  # Fallback
    'oth-mult': 'open',  # Fallback
}

CONTRACT_TYPE_MAP = {
    'services': 'services',
    'supplies': 'supplies',
    'works': 'works',
}

# Diccionario global para flags de cancelación por usuario
_cancel_flags = {}


def set_cancel_flag(user_id: int):
    """Establece el flag de cancelación para un usuario"""
    _cancel_flags[user_id] = True


def clear_cancel_flag(user_id: int):
    """Limpia el flag de cancelación para un usuario"""
    _cancel_flags[user_id] = False


def should_cancel(user_id: int) -> bool:
    """Verifica si se debe cancelar la descarga para un usuario"""
    return _cancel_flags.get(user_id, False)


def create_session_with_retries() -> requests.Session:
    """
    Crea una sesión de requests con reintentos automáticos configurados.
    Maneja errores de conexión, timeouts y errores DNS.
    """
    session = requests.Session()

    # Configurar estrategia de reintentos
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Headers comunes
    session.headers.update({
        'User-Agent': 'TenderAI-Platform/1.0 (Python requests)',
        'Accept': 'application/json',
    })

    return session


def http_post(url: str, session: Optional[requests.Session] = None, **kwargs) -> requests.Response:
    """POST con delay para respetar rate limits y manejo de errores"""
    time.sleep(DOWNLOAD_DELAY)

    if session is None:
        session = create_session_with_retries()

    try:
        response = session.post(url, **kwargs)
        return response
    except requests.exceptions.RequestException as e:
        # Mejorar el mensaje de error
        error_msg = str(e)
        if "Failed to resolve" in error_msg or "getaddrinfo failed" in error_msg:
            raise ConnectionError(
                f"No se pudo resolver el nombre de dominio. "
                f"Verifica tu conexión a Internet y configuración de DNS. "
                f"Error original: {error_msg}"
            )
        elif "Connection refused" in error_msg:
            raise ConnectionError(
                f"Conexión rechazada por el servidor. "
                f"Verifica tu firewall o configuración de proxy. "
                f"Error original: {error_msg}"
            )
        else:
            raise ConnectionError(f"Error de conexión: {error_msg}")


def http_get(url: str, session: Optional[requests.Session] = None, **kwargs) -> requests.Response:
    """GET con delay para respetar rate limits y manejo de errores"""
    time.sleep(DOWNLOAD_DELAY)

    if session is None:
        session = create_session_with_retries()

    try:
        response = session.get(url, **kwargs)
        return response
    except requests.exceptions.RequestException as e:
        # Mejorar el mensaje de error
        error_msg = str(e)
        if "Failed to resolve" in error_msg or "getaddrinfo failed" in error_msg:
            raise ConnectionError(
                f"No se pudo resolver el nombre de dominio. "
                f"Verifica tu conexión a Internet y configuración de DNS. "
                f"Error original: {error_msg}"
            )
        elif "Connection refused" in error_msg:
            raise ConnectionError(
                f"Conexión rechazada por el servidor. "
                f"Verifica tu firewall o configuración de proxy. "
                f"Error original: {error_msg}"
            )
        else:
            raise ConnectionError(f"Error de conexión: {error_msg}")


def date_range_clause(start_d: date, end_d: date) -> str:
    """Sintaxis Expert: publication-date=(YYYYMMDD <> YYYYMMDD)"""
    return f"publication-date=({start_d:%Y%m%d} <> {end_d:%Y%m%d})"


def expert_query_with_range(start_d: date, end_d: date, cpv_expr: str, place: str, notice_type: str) -> str:
    """Construir query en sintaxis Expert"""
    parts = [notice_type, cpv_expr, place, date_range_clause(start_d, end_d)]
    return " and ".join(parts)


def extract_publication_numbers(obj: Any) -> List[str]:
    """
    Recorre el JSON y extrae cualquier string con pinta de número de publicación
    (eForms 8 dígitos o TEDXML 6).
    """
    found: List[str] = []

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            for m in PUBNUM_RE.findall(x):
                found.append(m)

    walk(obj)

    # Únicos conservando orden
    seen, uniq = set(), []
    for nd in found:
        if nd not in seen:
            seen.add(nd)
            uniq.append(nd)
    return uniq


def save_xml_to_file(xml_content: bytes, pub_number: str) -> Optional[Path]:
    """
    Guarda el contenido XML en un archivo en data/xml/

    Args:
        xml_content: Contenido XML en bytes
        pub_number: Número de publicación (ej: '123456-2024')

    Returns:
        Path del archivo guardado o None si hubo error
    """
    try:
        # Crear directorio si no existe
        XML_DIR.mkdir(parents=True, exist_ok=True)

        # Nombre del archivo: pub_number.xml
        filename = f"{pub_number}.xml"
        filepath = XML_DIR / filename

        # Guardar XML
        with open(filepath, 'wb') as f:
            if isinstance(xml_content, bytes):
                f.write(xml_content)
            else:
                f.write(xml_content.encode('utf-8'))

        return filepath

    except Exception as e:
        print(f"Error guardando XML a archivo {pub_number}: {e}")
        return None


def download_xml_content(pub_number: str, session: Optional[requests.Session] = None) -> bytes:
    """
    Descarga el XML de un aviso por número de publicación.
    Formato: https://ted.europa.eu/en/notice/{publication-number}/xml
    """
    url = f"https://ted.europa.eu/en/notice/{pub_number}/xml"

    # Headers específicos para descargar XML
    headers = {
        'Accept': 'application/xml, text/xml, */*',
        'User-Agent': 'TenderAI-Platform/1.0 (Python requests)',
    }

    r = http_get(url, session=session, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content


def parse_xml_to_tender(xml_content: bytes, pub_number: str) -> Optional[Dict[str, Any]]:
    """
    Parsea el XML usando EFormsXMLParser y mapea a estructura Tender.
    Extrae información completa incluyendo contactos.

    Args:
        xml_content: Contenido XML en bytes
        pub_number: Número de publicación (ej: '715887-2025')

    Returns:
        Dict con campos para Tender.objects.create() o None si falla
    """
    if not EFORMS_PARSER_AVAILABLE:
        # Fallback al parseo antiguo si EFormsXMLParser no está disponible
        return _parse_xml_to_tender_legacy(xml_content, pub_number)

    try:
        # Guardar temporalmente el XML para que EFormsXMLParser pueda leerlo
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as tmp_file:
            tmp_file.write(xml_content)
            tmp_path = Path(tmp_file.name)

        try:
            # Parsear con EFormsXMLParser
            parser = EFormsXMLParser()
            parsed = parser.parse_file(tmp_path)

            required = parsed.get('REQUIRED', {})
            optional = parsed.get('OPTIONAL', {})
            meta = parsed.get('META', {})

            # Construir tender_data mapeando campos
            tender_data = {}

            # === REQUIRED FIELDS ===
            tender_data['ojs_notice_id'] = required.get('ojs_notice_id', pub_number)
            tender_data['title'] = required.get('title', f'Licitación {pub_number}')
            tender_data['buyer_name'] = required.get('buyer_name', 'Organismo público (por determinar)')
            tender_data['publication_date'] = required.get('publication_date', date.today())

            # === OPTIONAL FIELDS ===
            # Description
            description = optional.get('description', '')
            tender_data['description'] = description if description else tender_data['title']
            tender_data['short_description'] = (description if description else tender_data['title'])[:500]

            # Budget
            tender_data['budget_amount'] = optional.get('budget_eur', None)
            tender_data['currency'] = optional.get('currency', 'EUR')

            # CPV codes (combinar main + additional, extraer primeros 4 dígitos)
            cpv_codes = []
            cpv_main = required.get('cpv_main', '')
            if cpv_main:
                cpv_codes.append(cpv_main[:4])

            cpv_additional = optional.get('cpv_additional', [])
            for cpv in cpv_additional:
                cpv_short = cpv[:4]
                if cpv_short not in cpv_codes:
                    cpv_codes.append(cpv_short)

            tender_data['cpv_codes'] = cpv_codes

            # NUTS regions
            tender_data['nuts_regions'] = optional.get('nuts_regions', [])

            # Contract type (mapear código eForms)
            contract_type_code = optional.get('contract_type', 'services')
            tender_data['contract_type'] = CONTRACT_TYPE_MAP.get(contract_type_code, 'services')

            # Procedure type (mapear código eForms)
            procedure_type_code = optional.get('procedure_type', 'open')
            tender_data['procedure_type'] = PROCEDURE_TYPE_MAP.get(procedure_type_code, 'open')

            # Buyer type (no extraído por EFormsXMLParser)
            tender_data['buyer_type'] = ''

            # Deadline dates
            tender_data['tender_deadline_date'] = optional.get('tender_deadline_date', None)
            tender_data['tender_deadline_time'] = optional.get('tender_deadline_time', None)

            # Award criteria
            tender_data['award_criteria'] = optional.get('award_criteria', [])

            # === CONTACT FIELDS (PRINCIPAL OBJETIVO) ===
            tender_data['contact_email'] = optional.get('contact_email', '')
            tender_data['contact_phone'] = optional.get('contact_phone', '')
            tender_data['contact_url'] = optional.get('contact_url', '')
            tender_data['contact_fax'] = optional.get('contact_fax', '')

            # === METADATA ===
            tender_data['xpaths_used'] = meta.get('xpaths', {})
            tender_data['parsed_summary'] = {
                'REQUIRED': required,
                'OPTIONAL': optional,
                'META': meta
            }

            return tender_data

        finally:
            # Limpiar archivo temporal
            try:
                tmp_path.unlink()
            except:
                pass

    except Exception as e:
        print(f"Error parseando XML {pub_number} con EFormsXMLParser: {e}")
        # Fallback al parseo antiguo
        return _parse_xml_to_tender_legacy(xml_content, pub_number)


def _parse_xml_to_tender_legacy(xml_content: bytes, pub_number: str) -> Optional[Dict[str, Any]]:
    """
    Parseo antiguo (fallback) cuando EFormsXMLParser falla o no está disponible.
    Parseo básico con extracción limitada de campos.
    """
    try:
        root = ET.fromstring(xml_content)

        # Namespaces comunes en TED XML
        ns = {
            'ted': 'http://publications.europa.eu/resource/schema/ted/R2.0.9/publication',
            'n2016': 'http://publications.europa.eu/resource/schema/ted/2016/nuts',
        }

        # Extraer datos básicos (ajustar según estructura real)
        tender_data = {
            'ojs_notice_id': pub_number,
            'title': '',
            'description': '',
            'short_description': '',
            'budget_amount': None,
            'currency': 'EUR',
            'cpv_codes': [],
            'nuts_regions': [],
            'contract_type': 'services',
            'buyer_name': '',
            'buyer_type': '',
            'publication_date': date.today(),
            'tender_deadline_date': None,
            'procedure_type': 'open',
        }

        # Intentar extraer título
        for title_elem in root.iter():
            if 'TITLE' in title_elem.tag.upper():
                if title_elem.text:
                    tender_data['title'] = title_elem.text[:500]
                    break

        # Intentar extraer códigos CPV
        for cpv_elem in root.iter():
            if 'CPV' in cpv_elem.tag.upper():
                cpv_code = cpv_elem.get('CODE', '')
                if cpv_code and cpv_code not in tender_data['cpv_codes']:
                    tender_data['cpv_codes'].append(cpv_code[:4])  # Primeros 4 dígitos

        # Intentar extraer regiones NUTS
        for nuts_elem in root.iter():
            if 'NUTS' in nuts_elem.tag.upper():
                nuts_code = nuts_elem.get('CODE', '')
                if nuts_code and nuts_code not in tender_data['nuts_regions']:
                    tender_data['nuts_regions'].append(nuts_code)

        # Si no tenemos título, usar el pub_number
        if not tender_data['title']:
            tender_data['title'] = f"Licitación {pub_number}"

        # Si no tenemos descripción, usar el título
        tender_data['short_description'] = tender_data['title'][:500]
        tender_data['description'] = tender_data['title']

        # Buyer name por defecto
        if not tender_data['buyer_name']:
            tender_data['buyer_name'] = 'Organismo público (por determinar)'

        return tender_data

    except Exception as e:
        print(f"Error parseando XML {pub_number}: {e}")
        return None


def search_tenders_by_date_windows(
    days_back: int = DEFAULT_DAYS_BACK,
    cpv_expr: str = DEFAULT_CPV,
    place: str = DEFAULT_PLACE,
    notice_type: str = DEFAULT_NOTICE_TYPE,
    window_days: int = DEFAULT_WINDOW_DAYS,
    max_results: int = DEFAULT_MAX_DOWNLOAD,
    progress_callback=None,
    session: Optional[requests.Session] = None,
    logger: Optional[ObtenerLogger] = None
) -> Dict[str, Any]:
    """
    Busca licitaciones en ventanas de fechas.
    Retorna: dict con pub_numbers, total_range, analyzed_range, remaining_range
    """
    # Crear sesión si no se proporciona
    if session is None:
        session = create_session_with_retries()

    all_nd: List[str] = []
    today = date.today()
    total_start = today - timedelta(days=days_back)
    total_end = today

    analyzed_start: Optional[date] = None
    analyzed_end: Optional[date] = None
    remaining_start: Optional[date] = None
    remaining_end: Optional[date] = None

    win_end = total_end
    while win_end > total_start:
        win_start = max(total_start, win_end - timedelta(days=window_days))
        q = expert_query_with_range(win_start, win_end, cpv_expr, place, notice_type)

        # Debug: mostrar query construida
        import sys
        print(f"\n[QUERY TED API]", file=sys.stderr)
        print(f"  Window: {win_start} -> {win_end}", file=sys.stderr)
        print(f"  Query: {q}", file=sys.stderr)

        if progress_callback:
            progress_callback({
                'type': 'window',
                'start': str(win_start),
                'end': str(win_end),
                'total': len(all_nd)
            })

        payload = {"query": q, "fields": ["ND"]}

        # Log API request
        if logger:
            logger.log_api_request(SEARCH_URL, payload)

        resp = http_post(SEARCH_URL, session=session, json=payload, timeout=TIMEOUT)

        if resp.status_code >= 400:
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise RuntimeError(f"Search API error {resp.status_code}: {err}")

        data = resp.json()
        nd_page = extract_publication_numbers(data)

        # Log API response
        if logger:
            logger.log_api_response(resp.status_code, len(nd_page))

        # Deduplicar
        added = 0
        for nd in nd_page:
            if nd not in all_nd:
                all_nd.append(nd)
                added += 1

        if added:
            analyzed_end = analyzed_end or win_end
            analyzed_start = win_start

        if progress_callback:
            progress_callback({
                'type': 'window_result',
                'added': added,
                'total': len(all_nd)
            })

        # Si ya tenemos suficientes, parar
        if len(all_nd) >= max_results * 3:
            remaining_start = total_start
            remaining_end = win_start - timedelta(days=1)
            break

        # Siguiente ventana
        win_end = win_start - timedelta(days=1)

    if remaining_start is None:
        remaining_start, remaining_end = None, None

    return {
        "pub_numbers": all_nd,
        "total_range": (total_start, total_end),
        "analyzed_range": (analyzed_start or total_end, analyzed_end or total_end),
        "remaining_range": (remaining_start, remaining_end),
    }


def download_and_save_tenders(
    days_back: int = DEFAULT_DAYS_BACK,
    max_download: int = DEFAULT_MAX_DOWNLOAD,
    cpv_codes: Optional[List[str]] = None,
    place: Optional[str] = None,
    notice_type: Optional[str] = None,
    progress_callback=None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Función principal: busca, descarga y guarda licitaciones en la BD.

    Args:
        days_back: Días hacia atrás para buscar
        max_download: Máximo de licitaciones a descargar
        cpv_codes: Lista de códigos CPV para filtrar (ej: ['72', '7226'])
        place: País/región (ej: 'ESP', 'FRA'). Si es None, usa DEFAULT_PLACE
        notice_type: Tipo de aviso (ej: 'cn-standard'). Si es None, usa DEFAULT_NOTICE_TYPE
        progress_callback: Función opcional para reportar progreso
        user_id: ID del usuario (para control de cancelación)

    Returns:
        Dict con estadísticas: total_found, downloaded, saved, errors
    """
    # Inicializar logger
    logger = ObtenerLogger()

    # Limpiar flag de cancelación al inicio
    if user_id is not None:
        clear_cancel_flag(user_id)

    # Crear sesión reutilizable con reintentos
    session = create_session_with_retries()

    # Construir expresión CPV
    if cpv_codes:
        if len(cpv_codes) == 1:
            # Un solo código: no necesita paréntesis
            cpv_expr = f"classification-cpv={cpv_codes[0]}*"
        else:
            # Múltiples códigos: envolver en paréntesis para correcta precedencia
            cpv_parts = " or ".join([f"classification-cpv={code}*" for code in cpv_codes])
            cpv_expr = f"({cpv_parts})"
    else:
        cpv_expr = DEFAULT_CPV

    # Usar valores proporcionados o defaults
    place_expr = f"place-of-performance={place}" if place else DEFAULT_PLACE
    notice_type_expr = f"notice-type={notice_type}" if notice_type else DEFAULT_NOTICE_TYPE

    # Construir query para el log
    search_query = f"{cpv_expr} and {place_expr} and {notice_type_expr} (last {days_back} days)"

    # Log inicio de descarga
    logger.log_start(search_query)

    # Debug: mostrar filtros aplicados
    import sys
    print(f"\n[FILTROS APLICADOS]", file=sys.stderr)
    print(f"  CPV Expression: {cpv_expr}", file=sys.stderr)
    print(f"  Place: {place_expr}", file=sys.stderr)
    print(f"  Notice Type: {notice_type_expr}", file=sys.stderr)
    print(f"  Days Back: {days_back}", file=sys.stderr)

    # 1. Buscar licitaciones
    if progress_callback:
        progress_callback({'type': 'start', 'message': '🚀 Conectando con TED API...'})

    try:
        search_res = search_tenders_by_date_windows(
            days_back=days_back,
            cpv_expr=cpv_expr,
            place=place_expr,
            notice_type=notice_type_expr,
            max_results=max_download,
            progress_callback=progress_callback,
            session=session,
            logger=logger
        )
    except ConnectionError as e:
        # Error de conexión detectado
        if progress_callback:
            progress_callback({
                'type': 'error',
                'message': str(e)
            })
        return {
            "total_found": 0,
            "downloaded": 0,
            "saved": 0,
            "errors": [str(e)],
            "date_range": (date.today(), date.today()),
        }
    except Exception as e:
        # Otro tipo de error
        error_msg = f"Error en la búsqueda: {str(e)}"
        if progress_callback:
            progress_callback({
                'type': 'error',
                'message': error_msg
            })
        return {
            "total_found": 0,
            "downloaded": 0,
            "saved": 0,
            "errors": [error_msg],
            "date_range": (date.today(), date.today()),
        }

    pub_numbers = search_res["pub_numbers"][:max_download]
    total_found = len(search_res["pub_numbers"])

    if progress_callback:
        progress_callback({
            'type': 'search_complete',
            'total_found': total_found,
            'to_download': len(pub_numbers)
        })

    # 2. Descargar y guardar
    downloaded = 0
    saved = 0
    errors = []

    for idx, pub_num in enumerate(pub_numbers, 1):
        # Verificar cancelación
        if user_id is not None and should_cancel(user_id):
            if progress_callback:
                progress_callback({
                    'type': 'cancelled',
                    'message': 'Descarga cancelada por el usuario',
                    'saved': saved,
                    'downloaded': downloaded
                })
            break

        try:
            if progress_callback:
                progress_callback({
                    'type': 'download',
                    'current': idx,
                    'total': len(pub_numbers),
                    'pub_number': pub_num
                })

            # Verificar si ya existe
            if Tender.objects.filter(ojs_notice_id=pub_num).exists():
                if progress_callback:
                    progress_callback({
                        'type': 'skip',
                        'pub_number': pub_num,
                        'reason': 'Ya existe en la base de datos'
                    })
                continue

            # Descargar XML
            xml_content = download_xml_content(pub_num, session=session)
            downloaded += 1

            # Parsear
            tender_data = parse_xml_to_tender(xml_content, pub_num)
            if not tender_data:
                errors.append(f"{pub_num}: Error parseando XML")
                # Log download failure
                logger.log_download(pub_num, success=False)
                if progress_callback:
                    progress_callback({
                        'type': 'error',
                        'pub_number': pub_num,
                        'message': 'Error parseando XML'
                    })
                continue

            # Guardar XML en archivo (data/xml/)
            xml_filepath = save_xml_to_file(xml_content, pub_num)

            # Guardar en BD con el XML completo
            tender_data['xml_content'] = xml_content.decode('utf-8') if isinstance(xml_content, bytes) else xml_content

            # Guardar ruta del archivo si se guardó exitosamente
            if xml_filepath:
                tender_data['source_path'] = str(xml_filepath)

            tender = Tender.objects.create(**tender_data)
            saved += 1

            # Log download success
            logger.log_download(pub_num, success=True, file_path=str(xml_filepath) if xml_filepath else None)

            if progress_callback:
                progress_callback({
                    'type': 'saved',
                    'pub_number': pub_num,
                    'title': tender.title[:80],
                    'current': idx,
                    'total': len(pub_numbers),
                    'saved_count': saved
                })

        except ConnectionError as e:
            error_msg = f"{pub_num}: {str(e)}"
            errors.append(error_msg)
            # Log download failure
            logger.log_download(pub_num, success=False)
            if progress_callback:
                progress_callback({
                    'type': 'error',
                    'pub_number': pub_num,
                    'message': str(e)
                })
        except Exception as e:
            error_msg = f"{pub_num}: {str(e)}"
            errors.append(error_msg)
            # Log download failure
            logger.log_download(pub_num, success=False)
            if progress_callback:
                progress_callback({
                    'type': 'error',
                    'pub_number': pub_num,
                    'message': str(e)
                })

    if progress_callback:
        progress_callback({
            'type': 'complete',
            'saved': saved,
            'downloaded': downloaded,
            'errors': len(errors)
        })

    # Log summary
    logger.log_summary(
        total=total_found,
        downloaded=downloaded,
        failed=len(errors)
    )

    return {
        "total_found": total_found,
        "downloaded": downloaded,
        "saved": saved,
        "errors": errors,
        "date_range": search_res["total_range"],
    }
