# MLUrbanPlanning - AI Job Search Platform

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.1.6-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/LangChain-0.3+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" />
  <img src="https://img.shields.io/badge/Version-3.8.0-blue?style=for-the-badge" />
</p>

<p align="center">
  <b>Plataforma inteligente de busqueda de empleo potenciada por agentes IA con Function Calling</b>
</p>

<p align="center">
  <a href="https://vocesalviento.com">vocesalviento.com</a>
</p>

---

## Descripcion General

MLUrbanPlanning es una plataforma web que ayuda a candidatos a encontrar ofertas de empleo mediante **agentes de IA** que analizan el CV del usuario, buscan ofertas en la web y generan recomendaciones personalizadas. El sistema utiliza **Function Calling** con hasta 15 iteraciones automaticas para resolver consultas complejas.

### Funcionalidades principales

- **Analisis de CV con IA** - Extraccion automatica de skills, experiencia, educacion e idiomas desde PDF o texto
- **Busqueda inteligente de empleo** - Agente que busca ofertas en la web y las filtra segun el perfil del candidato
- **Chat interactivo con Function Calling** - Conversacion natural con el agente que ejecuta herramientas automaticamente
- **Multi-proveedor LLM** - Soporte para Google Gemini, OpenAI, NVIDIA y Ollama (100% local y privado)
- **Fit Analysis** - Puntuacion de compatibilidad entre el perfil del candidato y las ofertas encontradas
- **Navegacion web interactiva** - Playwright para navegar portales de empleo complejos

---

## URL Publica

La aplicacion esta desplegada y accesible en:

**https://vocesalviento.com**

---

## Usuario de Prueba

La plataforma tiene un usuario pre-configurado con APIs y perfil completo listo para probar:

| Campo | Valor |
|-------|-------|
| **Usuario** | `pepe2012` |
| **Email** | `annndriancito2012@gmail.com` |
| **Proveedor LLM** | OpenAI |
| **API Key LLM** | Configurada |
| **Google Search API** | Configurada |
| **Perfil CV** | Completo con skills, experiencia y preferencias |

> El usuario ya tiene configuradas las API keys de OpenAI y Google Search, ademas de un perfil de candidato con CV analizado y preferencias de busqueda definidas.

---

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| **Backend** | Django 5.1.6, Python 3.12 |
| **IA / Agentes** | LangChain 0.3+, Function Calling Agent |
| **LLMs** | Google Gemini 2.5 Flash, OpenAI GPT-4o, NVIDIA NIM, Ollama |
| **Frontend** | Bootstrap 5, JavaScript (AJAX) |
| **Base de datos** | SQLite (desarrollo) / PostgreSQL (produccion) |
| **Web Scraping** | Playwright (navegacion interactiva) |
| **Servidor** | Nginx + HTTPS (Let's Encrypt) |

---

## Arquitectura del Agente

El sistema utiliza un **Function Calling Agent** que decide autonomamente que herramientas ejecutar:

```
Usuario: "Busca ofertas de data science en Madrid"

  -> Agente analiza la consulta
  -> Ejecuta: get_user_profile() -> obtiene CV y preferencias
  -> Ejecuta: search_jobs(query="data science", location="Madrid")
  -> Analiza ~60 ofertas, selecciona top 15
  -> Genera fit_analysis con puntuacion de compatibilidad
  -> Respuesta final con ofertas rankeadas
```

### Herramientas disponibles

| Categoria | Herramientas | Descripcion |
|-----------|-------------|-------------|
| **Perfil** | `get_user_profile`, `get_full_cv` | Contexto del candidato |
| **Busqueda** | `search_jobs`, `web_search` | Busqueda de ofertas y web |
| **Analisis** | `analyze_cv`, `recommend_companies` | Analisis de CV y recomendaciones |
| **Navegacion** | `browse_webpage`, `browse_interactive` | Extraccion web y Playwright |

---

## Estructura del Proyecto

```
MLUrbanPlanning/
├── config/                     # Settings y URLs de Django
├── apps/
│   ├── authentication/         # Usuarios, login, API keys
│   ├── company/                # Perfil candidato, CV, preferencias
│   ├── chat/                   # Sesiones de chat y mensajes
│   └── core/                   # Dashboard, home, perfil
├── agent_ia_core/              # Motor de IA
│   ├── agent_function_calling.py   # Agente principal
│   ├── config.py                   # Configuracion
│   ├── tools/
│   │   ├── agent_tools/            # Herramientas del agente
│   │   └── core/                   # Registry y base classes
│   └── schema/                     # Validacion de datos
├── templates/                  # Templates HTML
├── static/                     # CSS, JS (diseno Apple-inspired)
├── data/                       # Base de datos y registros
├── media/                      # CVs subidos por usuarios
└── manage.py
```

---

## Instalacion Local

```bash
# Clonar repositorio
git clone https://github.com/AdrianUbedaTouati/MLUrbanPlanning.git
cd MLUrbanPlanning

# Entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Dependencias
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env   # Editar con tus API keys

# Migraciones y servidor
python manage.py migrate
python manage.py runserver
```

Accede a `http://127.0.0.1:8000`

---

## Configuracion de LLM

Cada usuario configura su proveedor de IA desde **Mi Perfil > Editar Perfil**:

| Proveedor | Modelo por defecto | API Key | Coste |
|-----------|-------------------|---------|-------|
| **Ollama** | qwen2.5:7b | No necesita | Gratis (local) |
| **Google Gemini** | gemini-2.5-flash | Si | Pago |
| **OpenAI** | gpt-4o-mini | Si | Pago |
| **NVIDIA** | llama-3.1-8b | Si | Pago |

---

## Capturas

La interfaz sigue un diseno minimalista inspirado en Apple con:

- Chat interactivo con AJAX (sin recargas)
- Typing indicator animado mientras la IA responde
- Metadata visible: tokens usados, herramientas ejecutadas
- Responsive design para movil y desktop
- Soporte para dark mode

---

## Autor

**Adrian Ubeda Touati**

- GitHub: [@AdrianUbedaTouati](https://github.com/AdrianUbedaTouati)

---

## Licencia

Proyecto academico - Todos los derechos reservados.
