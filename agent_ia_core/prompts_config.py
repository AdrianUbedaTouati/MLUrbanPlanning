# -*- coding: utf-8 -*-
"""
Configuración centralizada de prompts para la integración con Agent_IA.
Todos los prompts y contextos que se pasan a la IA están definidos aquí.
"""

# ================================================
# PROMPTS PARA CHAT
# ================================================

# Contexto inicial que se pasa al chat (una sola vez al inicio)
SYSTEM_CONTEXT_TEMPLATE = """Eres un asistente especializado en licitaciones públicas españolas y europeas.

Información de la empresa del usuario:
{company_context}

Tu objetivo es ayudar al usuario a encontrar y analizar licitaciones relevantes para su empresa.
Proporciona respuestas precisas, basadas en los documentos disponibles en la base de datos.
Si no tienes información suficiente, indícalo claramente.
"""

# ================================================
# PROMPTS PARA EXTRACCIÓN DE INFORMACIÓN DE EMPRESA
# ================================================

COMPANY_INFO_EXTRACTION_PROMPT = """Analiza el siguiente texto sobre una empresa y extrae la información estructurada.

Texto de la empresa:
{company_text}

Extrae la siguiente información:
- Nombre de la empresa
- Sectores o áreas de actividad
- Número aproximado de empleados
- Tecnologías, herramientas o servicios que ofrecen
- Ubicación geográfica (ciudades, regiones, países)
- Códigos CPV relevantes (inferir basándose en los servicios/productos)
- Regiones NUTS (inferir basándose en la ubicación)
- Presupuesto típico de proyectos (rango mínimo y máximo en euros)
- Certificaciones o acreditaciones
- Experiencia previa relevante

Instrucciones:
- Si no se menciona explícitamente algún dato, déjalo vacío o inferir basándote en el contexto
- Los códigos CPV deben ser códigos de 4 dígitos estándar del Common Procurement Vocabulary
- Las regiones NUTS deben seguir el formato estándar (ej: ES30, ES51, etc.)
- Sé preciso y extrae solo información que esté presente o claramente inferible

Devuelve la información en formato estructurado.
"""

# ================================================
# CONTEXTO DE EMPRESA PARA CHAT
# ================================================

def format_company_context(company_profile) -> str:
    """
    Formatea el perfil de empresa para incluirlo en el contexto del chat.
    Esta información se pasa UNA SOLA VEZ al inicio de cada sesión de chat.

    Args:
        company_profile: Instancia del modelo CompanyProfile

    Returns:
        str: Contexto formateado de la empresa
    """
    if not company_profile:
        return "No hay información de empresa disponible."

    context_parts = []

    # Nombre y descripción
    if company_profile.company_name:
        context_parts.append(f"Empresa: {company_profile.company_name}")

    if company_profile.company_description_text:
        context_parts.append(f"Descripción: {company_profile.company_description_text}")

    # Sectores
    if company_profile.sectors:
        sectors_list = ", ".join(company_profile.sectors)
        context_parts.append(f"Sectores: {sectors_list}")

    # Tamaño de la empresa
    if company_profile.employees:
        context_parts.append(f"Empleados: {company_profile.employees}")

    # Ubicación
    if company_profile.preferred_nuts_regions:
        nuts_list = ", ".join(company_profile.preferred_nuts_regions)
        context_parts.append(f"Regiones de interés (NUTS): {nuts_list}")

    # Códigos CPV preferidos
    if company_profile.preferred_cpv_codes:
        cpv_list = ", ".join(company_profile.preferred_cpv_codes)
        context_parts.append(f"Códigos CPV de interés: {cpv_list}")

    # Presupuesto
    if company_profile.budget_range:
        budget_min = company_profile.budget_range.get('min', 0)
        budget_max = company_profile.budget_range.get('max', 0)
        if budget_min or budget_max:
            context_parts.append(f"Rango de presupuesto: {budget_min:,}€ - {budget_max:,}€")

    return "\n".join(context_parts) if context_parts else "No hay información detallada de empresa."


# ================================================
# CAMPOS REQUERIDOS DEL PERFIL DE EMPRESA
# ================================================

# Campos mínimos que debería tener el perfil de empresa para usar Agent_IA efectivamente
REQUIRED_COMPANY_FIELDS = [
    'company_description_text',  # Descripción libre (siempre se incluye en el contexto)
]

# Campos opcionales pero recomendados
RECOMMENDED_COMPANY_FIELDS = [
    'sectors',                   # Para filtrar licitaciones relevantes
    'preferred_cpv_codes',       # Para búsquedas precisas por CPV
    'preferred_nuts_regions',    # Para filtrar por ubicación geográfica
]

# ================================================
# CONFIGURACIÓN DE EXTRACCIÓN CON IA
# ================================================

# Temperatura para la extracción (0 = determinista)
EXTRACTION_TEMPERATURE = 0.0

# Modelo de LLM para extracción
EXTRACTION_MODEL = "gemini-2.0-flash-exp"

# ================================================
# MAPEO DE CÓDIGOS CPV COMUNES
# ================================================

# Mapeo de palabras clave a códigos CPV (para ayudar en la inferencia)
CPV_CODE_KEYWORDS = {
    "software": ["7226", "7240", "7267"],
    "desarrollo": ["7226", "7240"],
    "consultoría": ["7210", "7220"],
    "tecnología": ["3020", "3021", "3022"],
    "construcción": ["4500", "4510", "4520"],
    "arquitectura": ["7122", "7123"],
    "ingeniería": ["7122", "7130"],
    "limpieza": ["9013", "9031"],
    "seguridad": ["7934", "9311"],
    "alimentación": ["1530", "1531"],
    "formación": ["8060", "8041"],
    "sanidad": ["8512", "8513"],
}

# ================================================
# MAPEO DE REGIONES NUTS ESPAÑOLAS (COMPLETO)
# ================================================

# Mapeo completo de nombres de comunidades/provincias/ciudades a códigos NUTS
# Formato: nombre_normalizado -> (código_NUTS, nombre_oficial)
SPAIN_NUTS_MAPPING = {
    # Comunidades Autónomas (NUTS 1 y 2)
    "españa": ("ES", "España"),
    "noroeste": ("ES1", "Noroeste"),
    "noreste": ("ES2", "Noreste"),
    "comunidad de madrid": ("ES3", "Comunidad de Madrid"),
    "madrid": ("ES30", "Madrid"),
    "centro": ("ES4", "Centro (ES)"),
    "este": ("ES5", "Este"),
    "sur": ("ES6", "Sur"),
    "canarias": ("ES7", "Canarias"),

    # Galicia
    "galicia": ("ES11", "Galicia"),
    "coruña": ("ES111", "A Coruña"),
    "a coruña": ("ES111", "A Coruña"),
    "lugo": ("ES112", "Lugo"),
    "ourense": ("ES113", "Ourense"),
    "pontevedra": ("ES114", "Pontevedra"),

    # Asturias
    "asturias": ("ES12", "Principado de Asturias"),
    "oviedo": ("ES120", "Asturias"),
    "gijón": ("ES120", "Asturias"),

    # Cantabria
    "cantabria": ("ES13", "Cantabria"),
    "santander": ("ES130", "Cantabria"),

    # País Vasco
    "país vasco": ("ES21", "País Vasco / Euskadi"),
    "euskadi": ("ES21", "País Vasco / Euskadi"),
    "álava": ("ES211", "Álava / Araba"),
    "araba": ("ES211", "Álava / Araba"),
    "vitoria": ("ES211", "Álava / Araba"),
    "guipúzcoa": ("ES212", "Gipuzkoa"),
    "gipuzkoa": ("ES212", "Gipuzkoa"),
    "san sebastián": ("ES212", "Gipuzkoa"),
    "donostia": ("ES212", "Gipuzkoa"),
    "vizcaya": ("ES213", "Bizkaia"),
    "bizkaia": ("ES213", "Bizkaia"),
    "bilbao": ("ES213", "Bizkaia"),

    # Navarra
    "navarra": ("ES22", "Comunidad Foral de Navarra"),
    "nafarroa": ("ES22", "Comunidad Foral de Navarra"),
    "pamplona": ("ES220", "Navarra"),
    "iruña": ("ES220", "Navarra"),

    # La Rioja
    "la rioja": ("ES23", "La Rioja"),
    "rioja": ("ES23", "La Rioja"),
    "logroño": ("ES230", "La Rioja"),

    # Aragón
    "aragón": ("ES24", "Aragón"),
    "huesca": ("ES241", "Huesca"),
    "teruel": ("ES242", "Teruel"),
    "zaragoza": ("ES243", "Zaragoza"),

    # Cataluña
    "cataluña": ("ES51", "Cataluña"),
    "catalunya": ("ES51", "Cataluña"),
    "barcelona": ("ES511", "Barcelona"),
    "girona": ("ES512", "Girona"),
    "lleida": ("ES513", "Lleida"),
    "tarragona": ("ES514", "Tarragona"),

    # Comunidad Valenciana
    "comunidad valenciana": ("ES52", "Comunidad Valenciana"),
    "valencia": ("ES523", "Valencia / València"),
    "valència": ("ES523", "Valencia / València"),
    "alicante": ("ES521", "Alicante / Alacant"),
    "alacant": ("ES521", "Alicante / Alacant"),
    "castellón": ("ES522", "Castellón / Castelló"),
    "castelló": ("ES522", "Castellón / Castelló"),

    # Baleares
    "baleares": ("ES53", "Islas Baleares"),
    "illes balears": ("ES53", "Islas Baleares"),
    "mallorca": ("ES531", "Illes Balears"),
    "menorca": ("ES532", "Illes Balears"),
    "ibiza": ("ES533", "Illes Balears"),
    "eivissa": ("ES533", "Illes Balears"),
    "formentera": ("ES533", "Illes Balears"),
    "palma": ("ES531", "Illes Balears"),

    # Andalucía
    "andalucía": ("ES61", "Andalucía"),
    "almería": ("ES611", "Almería"),
    "cádiz": ("ES612", "Cádiz"),
    "córdoba": ("ES613", "Córdoba"),
    "granada": ("ES614", "Granada"),
    "huelva": ("ES615", "Huelva"),
    "jaén": ("ES616", "Jaén"),
    "málaga": ("ES617", "Málaga"),
    "sevilla": ("ES618", "Sevilla"),

    # Murcia
    "murcia": ("ES62", "Región de Murcia"),
    "cartagena": ("ES620", "Murcia"),
    "lorca": ("ES620", "Murcia"),

    # Castilla y León
    "castilla y león": ("ES41", "Castilla y León"),
    "ávila": ("ES411", "Ávila"),
    "burgos": ("ES412", "Burgos"),
    "león": ("ES413", "León"),
    "palencia": ("ES414", "Palencia"),
    "salamanca": ("ES415", "Salamanca"),
    "segovia": ("ES416", "Segovia"),
    "soria": ("ES417", "Soria"),
    "valladolid": ("ES418", "Valladolid"),
    "zamora": ("ES419", "Zamora"),

    # Castilla-La Mancha
    "castilla-la mancha": ("ES42", "Castilla-La Mancha"),
    "castilla la mancha": ("ES42", "Castilla-La Mancha"),
    "albacete": ("ES421", "Albacete"),
    "ciudad real": ("ES422", "Ciudad Real"),
    "cuenca": ("ES423", "Cuenca"),
    "guadalajara": ("ES424", "Guadalajara"),
    "toledo": ("ES425", "Toledo"),

    # Extremadura
    "extremadura": ("ES43", "Extremadura"),
    "badajoz": ("ES431", "Badajoz"),
    "cáceres": ("ES432", "Cáceres"),
    "mérida": ("ES431", "Badajoz"),

    # Canarias
    "las palmas": ("ES70", "Canarias"),
    "santa cruz de tenerife": ("ES70", "Canarias"),
    "tenerife": ("ES70", "Canarias"),
    "gran canaria": ("ES70", "Canarias"),
    "lanzarote": ("ES70", "Canarias"),
    "fuerteventura": ("ES70", "Canarias"),
    "la palma": ("ES70", "Canarias"),
    "la gomera": ("ES70", "Canarias"),
    "el hierro": ("ES70", "Canarias"),

    # Ceuta y Melilla
    "ceuta": ("ES63", "Ceuta"),
    "melilla": ("ES64", "Melilla"),
}

# Lista de todas las regiones NUTS para autocompletado (código -> nombre_completo)
NUTS_CODES_LIST = [
    ("ES", "España"),
    ("ES1", "Noroeste"),
    ("ES11", "Galicia"),
    ("ES111", "A Coruña"),
    ("ES112", "Lugo"),
    ("ES113", "Ourense"),
    ("ES114", "Pontevedra"),
    ("ES12", "Principado de Asturias"),
    ("ES120", "Asturias"),
    ("ES13", "Cantabria"),
    ("ES130", "Cantabria"),
    ("ES2", "Noreste"),
    ("ES21", "País Vasco / Euskadi"),
    ("ES211", "Álava / Araba"),
    ("ES212", "Gipuzkoa"),
    ("ES213", "Bizkaia"),
    ("ES22", "Comunidad Foral de Navarra"),
    ("ES220", "Navarra"),
    ("ES23", "La Rioja"),
    ("ES230", "La Rioja"),
    ("ES24", "Aragón"),
    ("ES241", "Huesca"),
    ("ES242", "Teruel"),
    ("ES243", "Zaragoza"),
    ("ES3", "Comunidad de Madrid"),
    ("ES30", "Madrid"),
    ("ES300", "Madrid"),
    ("ES4", "Centro (ES)"),
    ("ES41", "Castilla y León"),
    ("ES411", "Ávila"),
    ("ES412", "Burgos"),
    ("ES413", "León"),
    ("ES414", "Palencia"),
    ("ES415", "Salamanca"),
    ("ES416", "Segovia"),
    ("ES417", "Soria"),
    ("ES418", "Valladolid"),
    ("ES419", "Zamora"),
    ("ES42", "Castilla-La Mancha"),
    ("ES421", "Albacete"),
    ("ES422", "Ciudad Real"),
    ("ES423", "Cuenca"),
    ("ES424", "Guadalajara"),
    ("ES425", "Toledo"),
    ("ES43", "Extremadura"),
    ("ES431", "Badajoz"),
    ("ES432", "Cáceres"),
    ("ES5", "Este"),
    ("ES51", "Cataluña"),
    ("ES511", "Barcelona"),
    ("ES512", "Girona"),
    ("ES513", "Lleida"),
    ("ES514", "Tarragona"),
    ("ES52", "Comunidad Valenciana"),
    ("ES521", "Alicante / Alacant"),
    ("ES522", "Castellón / Castelló"),
    ("ES523", "Valencia / València"),
    ("ES53", "Illes Balears"),
    ("ES531", "Illes Balears"),
    ("ES532", "Illes Balears"),
    ("ES533", "Illes Balears"),
    ("ES6", "Sur"),
    ("ES61", "Andalucía"),
    ("ES611", "Almería"),
    ("ES612", "Cádiz"),
    ("ES613", "Córdoba"),
    ("ES614", "Granada"),
    ("ES615", "Huelva"),
    ("ES616", "Jaén"),
    ("ES617", "Málaga"),
    ("ES618", "Sevilla"),
    ("ES62", "Región de Murcia"),
    ("ES620", "Murcia"),
    ("ES63", "Ceuta"),
    ("ES630", "Ceuta"),
    ("ES64", "Melilla"),
    ("ES640", "Melilla"),
    ("ES7", "Canarias"),
    ("ES70", "Canarias"),
    ("ES703", "El Hierro"),
    ("ES704", "Fuerteventura"),
    ("ES705", "Gran Canaria"),
    ("ES706", "La Gomera"),
    ("ES707", "La Palma"),
    ("ES708", "Lanzarote"),
    ("ES709", "Tenerife"),
]

# ================================================
# MAPEO DE CÓDIGOS CPV COMUNES (EXPANDIDO)
# ================================================

# Mapeo expandido de palabras clave a códigos CPV (4 dígitos)
CPV_CODE_KEYWORDS_EXPANDED = {
    # Software y TI
    "software": ["7226", "7240", "7267", "4822"],
    "desarrollo software": ["7226", "7240"],
    "aplicaciones": ["7226", "4822"],
    "sitio web": ["7226", "7240"],
    "página web": ["7226", "7240"],
    "desarrollo web": ["7226"],
    "app": ["7226", "4822"],
    "aplicación móvil": ["7226", "4822"],
    "sistemas información": ["7224", "7226"],
    "base de datos": ["7224", "7226"],
    "infraestructura ti": ["3020", "7222"],
    "servidores": ["3020", "3021"],
    "redes": ["3214", "7225"],
    "ciberseguridad": ["7223", "7934"],
    "seguridad informática": ["7223", "7934"],

    # Consultoría
    "consultoría": ["7210", "7220", "7114"],
    "asesoría": ["7210", "7220"],
    "consultoría ti": ["7220", "7226"],
    "consultoría gestión": ["7114", "7921"],
    "auditoría": ["7921", "7922"],

    # Tecnología y electrónica
    "tecnología": ["3020", "3021", "3022", "3211"],
    "equipos informáticos": ["3020", "3021"],
    "ordenadores": ["3020", "3021"],
    "portátiles": ["3021"],
    "tablets": ["3022"],
    "impresoras": ["3010", "3013"],
    "escáneres": ["3012"],
    "equipos electrónicos": ["3200", "3210"],

    # Construcción y obras
    "construcción": ["4500", "4510", "4520"],
    "obras": ["4500", "4510"],
    "edificación": ["4520", "4521"],
    "rehabilitación": ["4523", "4524"],
    "mantenimiento edificios": ["5000", "7011"],
    "instalaciones": ["4530", "4531"],
    "fontanería": ["4532"],
    "electricidad": ["4531"],

    # Arquitectura e ingeniería
    "arquitectura": ["7122", "7123"],
    "ingeniería": ["7122", "7130", "7131"],
    "ingeniería civil": ["7131"],
    "diseño arquitectónico": ["7123"],
    "topografía": ["7151"],

    # Limpieza
    "limpieza": ["9013", "9031", "9091"],
    "limpieza edificios": ["9013", "9031"],
    "gestión residuos": ["9000", "9013"],

    # Seguridad
    "seguridad": ["7934", "9311", "9312"],
    "vigilancia": ["7934", "9311"],
    "seguridad privada": ["7934"],
    "protección": ["9311", "9312"],

    # Alimentación y catering
    "alimentación": ["1530", "1531", "1533"],
    "catering": ["5523", "5524"],
    "comedor": ["5523", "5524"],
    "restauración": ["5523", "5524"],

    # Formación y educación
    "formación": ["8060", "8041", "8042"],
    "educación": ["8000", "8041"],
    "cursos": ["8060", "8041"],
    "capacitación": ["8060"],
    "docencia": ["8000", "8041"],

    # Sanidad
    "sanidad": ["8512", "8513", "8514"],
    "salud": ["8512", "8513"],
    "médico": ["8512", "8514"],
    "hospital": ["8512", "8514"],
    "material sanitario": ["3310", "3311"],

    # Transporte
    "transporte": ["6000", "6010", "6042"],
    "logística": ["6342", "6344"],
    "mensajería": ["6411", "6412"],
    "vehículos": ["3400", "3410"],

    # Energía
    "energía": ["0910", "4530", "7113"],
    "electricidad": ["4531", "0913"],
    "renovables": ["0910", "4531"],
    "eficiencia energética": ["7113", "4531"],

    # Medio ambiente
    "medio ambiente": ["9071", "9090"],
    "sostenibilidad": ["9071", "9090"],
    "gestión ambiental": ["9071", "7720"],
}

# Lista completa de códigos CPV comunes para autocompletado (código -> descripción)
CPV_CODES_LIST = [
    ("7226", "Servicios de software"),
    ("7240", "Desarrollo de software y aplicaciones"),
    ("7267", "Mantenimiento y reparación de software"),
    ("7224", "Servicios de gestión de sistemas"),
    ("7225", "Servicios de redes"),
    ("7223", "Servicios de seguridad informática"),
    ("7222", "Servicios de soporte de sistemas"),
    ("7210", "Servicios de consultoría en gestión"),
    ("7220", "Servicios de consultoría en tecnología"),
    ("7114", "Servicios jurídicos"),
    ("7921", "Servicios de auditoría"),
    ("4822", "Aplicaciones informáticas personalizadas"),
    ("3020", "Equipos informáticos"),
    ("3021", "Ordenadores personales"),
    ("3022", "Tabletas"),
    ("3010", "Máquinas de oficina"),
    ("3013", "Impresoras y trazadores"),
    ("3012", "Escáneres"),
    ("4500", "Obras de construcción completas o parciales"),
    ("4510", "Trabajos de preparación del terreno"),
    ("4520", "Trabajos de construcción de edificios"),
    ("4521", "Trabajos generales de construcción de edificios"),
    ("4523", "Trabajos de rehabilitación de edificios"),
    ("4530", "Trabajos de instalación en edificios"),
    ("4531", "Trabajos de instalación eléctrica"),
    ("4532", "Trabajos de fontanería"),
    ("5000", "Servicios de reparación y mantenimiento"),
    ("7011", "Servicios relacionados con terrenos"),
    ("7122", "Servicios de arquitectura"),
    ("7123", "Servicios de diseño arquitectónico"),
    ("7130", "Servicios de ingeniería"),
    ("7131", "Servicios de ingeniería civil"),
    ("7151", "Servicios de topografía"),
    ("9013", "Servicios de limpieza de edificios"),
    ("9031", "Servicios de limpieza y desinfección en espacios públicos"),
    ("9091", "Servicios de limpieza doméstica"),
    ("9000", "Servicios de gestión de residuos"),
    ("7934", "Servicios de seguridad"),
    ("9311", "Servicios de vigilancia"),
    ("9312", "Servicios de protección de personas"),
    ("1530", "Productos alimenticios"),
    ("1531", "Productos cárnicos"),
    ("1533", "Productos lácteos"),
    ("5523", "Servicios de catering"),
    ("5524", "Servicios de comedor escolar"),
    ("8060", "Servicios de formación"),
    ("8041", "Servicios de educación para adultos y otros"),
    ("8042", "Servicios de formación profesional"),
    ("8000", "Servicios de educación y formación"),
    ("8512", "Servicios médicos"),
    ("8513", "Servicios dentales"),
    ("8514", "Servicios de hospital"),
    ("3310", "Dispositivos médicos"),
    ("3311", "Equipos médicos"),
    ("6000", "Servicios de transporte terrestre"),
    ("6010", "Servicios de transporte por carretera"),
    ("6042", "Servicios de transporte de personas"),
    ("6342", "Servicios de logística"),
    ("6344", "Servicios de almacenamiento"),
    ("6411", "Servicios de correo"),
    ("6412", "Servicios de mensajería"),
    ("3400", "Vehículos de motor"),
    ("3410", "Vehículos de pasajeros"),
    ("0910", "Combustibles"),
    ("0913", "Electricidad"),
    ("4530", "Instalaciones de producción de energía"),
    ("7113", "Servicios de consultoría en eficiencia energética"),
    ("9071", "Servicios de limpieza y gestión de espacios naturales"),
    ("9090", "Servicios de gestión medioambiental"),
    ("7720", "Servicios de investigación medioambiental"),
]

# ================================================
# TIPOS DE ANUNCIOS EN AGENT_IA
# ================================================

# Tipos de anuncios que Agent_IA puede procesar (basado en eForms)
NOTICE_TYPES = [
    ("contract_notice", "Licitación / Anuncio de Contrato"),
    ("contract_award", "Adjudicación / Formalización"),
    ("prior_information", "Anuncio Previo"),
    ("modification", "Modificación de Contrato"),
    ("completion", "Anuncio de Finalización"),
]

# Mapeo para búsqueda
NOTICE_TYPE_CHOICES = {
    "licitacion": "contract_notice",
    "licitación": "contract_notice",
    "oferta": "contract_notice",
    "convocatoria": "contract_notice",
    "adjudicacion": "contract_award",
    "adjudicación": "contract_award",
    "formalización": "contract_award",
    "formalización": "contract_award",
    "ganador": "contract_award",
    "anuncio previo": "prior_information",
    "previo": "prior_information",
    "modificacion": "modification",
    "modificación": "modification",
    "cambio": "modification",
    "finalizacion": "completion",
    "finalización": "completion",
    "completado": "completion",
}
