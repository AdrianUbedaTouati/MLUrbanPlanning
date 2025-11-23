# -*- coding: utf-8 -*-
"""
Configuración centralizada del agente IA para JobSearchAI Platform.
Define modelos, parámetros y configuración general.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ================================================
# RUTAS DEL PROYECTO
# ================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# ================================================
# CONFIGURACIÓN DE PROVEEDOR DE LLM
# ================================================
# El proveedor real se obtiene del perfil del usuario
LLM_PROVIDER = "google"  # Valor por defecto

# ================================================
# CONFIGURACIÓN DE MODELOS - OPENAI
# ================================================
OPENAI_LLM_MODEL = "gpt-4o-mini"

# ================================================
# CONFIGURACIÓN DE MODELOS - GOOGLE GEMINI
# ================================================
GOOGLE_LLM_MODEL = "gemini-2.5-flash"

# ================================================
# CONFIGURACIÓN DE MODELOS - NVIDIA NIM
# ================================================
NVIDIA_LLM_MODEL = "meta/llama-3.1-8b-instruct"

# ================================================
# CONFIGURACIÓN ACTIVA POR DEFECTO
# ================================================
LLM_MODEL = GOOGLE_LLM_MODEL

# Temperatura para respuestas (0.0 = determinista, 1.0 = creativo)
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))

# Longitud de contexto para Ollama (tokens)
OLLAMA_CONTEXT_LENGTH = int(os.getenv('OLLAMA_CONTEXT_LENGTH', '2048'))

# Timeout para llamadas al LLM (segundos)
LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '120'))

# ================================================
# CONFIGURACIÓN DEL AGENTE
# ================================================
# Número máximo de iteraciones del agente (para evitar loops)
MAX_AGENT_ITERATIONS = int(os.getenv('MAX_AGENT_ITERATIONS', '15'))

# ================================================
# CONFIGURACIÓN DE BÚSQUEDA DE EMPLEO
# ================================================
# APIs de búsqueda de empleo
INFOJOBS_API_URL = "https://api.infojobs.net/api/7"
INDEED_API_URL = "https://api.indeed.com/v2"
LINKEDIN_API_URL = "https://api.linkedin.com/v2"

# Límite de resultados por búsqueda
MAX_JOB_RESULTS = 20

# Regiones de España (para autocompletado)
SPANISH_REGIONS = [
    "Alicante", "Barcelona", "Madrid", "Valencia", "Sevilla",
    "Málaga", "Bilbao", "Zaragoza", "Murcia", "Palma de Mallorca",
    "Las Palmas", "Valladolid", "Vigo", "Gijón", "Granada",
    "A Coruña", "Vitoria", "Elche", "Oviedo", "Santa Cruz de Tenerife"
]

# Sectores de empleo
JOB_SECTORS = [
    "Informática/IT", "Marketing", "Ventas", "Finanzas", "RRHH",
    "Ingeniería", "Sanidad", "Educación", "Construcción", "Hostelería",
    "Logística", "Administración", "Legal", "Diseño", "Comunicación"
]

# ================================================
# CONFIGURACIÓN DE LOGGING
# ================================================
LOG_LEVEL = "INFO"
LOG_FILE = str(LOGS_DIR / "job_search.log")

# ================================================
# IDIOMA Y LOCALIZACIÓN
# ================================================
DEFAULT_LANGUAGE = "es"
SUPPORTED_LANGUAGES = ["es", "en"]
