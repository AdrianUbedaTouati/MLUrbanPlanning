# TenderAI Platform - Arquitectura Técnica

## Stack Tecnológico

### Backend
- Django 5.2.6
- Python 3.10+
- SQLite (dev) / PostgreSQL (prod)

### IA/ML
- LangChain 0.3.14
- LangGraph 0.2.63
- Google Gemini 2.5 Flash
- ChromaDB

### Frontend
- Bootstrap 5.3
- JavaScript vanilla (AJAX, animaciones CSS)
- Diseño Apple-inspired (#007AFF, tipografía San Francisco)

## Arquitectura de Apps

```
TenderAI/                      # Configuración Django
├── settings.py                # Configuración principal
├── urls.py                    # URLs raíz
└── wsgi.py                    # WSGI entry point

authentication/                 # Sistema de usuarios
├── models.py                  # User (custom), PasswordResetToken
├── views.py                   # Login, Registro, Recuperación
├── forms.py                   # Validación de formularios
└── backends.py                # Backend de autenticación

core/                          # Vistas base
├── views.py                   # Home, Perfil de usuario
├── forms.py                   # EditProfileForm
└── templates/core/            # Base template, home

company/                       # Perfiles empresariales
├── models.py                  # CompanyProfile (con campo company_description_text)
├── views.py                   # ProfileView, ProfileDetailView, ExtractCompanyInfoView
├── services.py                # CompanyProfileAIService (extracción con IA)
└── templates/company/         # Formulario de perfil con autocompletado IA

tenders/                       # Gestión de licitaciones
├── models.py                  # Tender, SavedTender, TenderRecommendation
├── views.py                   # Dashboard, List, Detail, Saved, Recommended
├── services.py                # TenderRecommendationService, TenderIndexingService
└── templates/tenders/         # Templates para licitaciones

chat/                          # Chat con IA (Interfaz Apple-style)
├── models.py                  # ChatSession, ChatMessage
├── views.py                   # SessionList, SessionDetail, MessageCreate
├── services.py                # ChatAgentService
├── templates/chat/            # Templates de chat rediseñados
└── static/chat/               # CSS/JS minimalista estilo Apple
    ├── css/chat.css           # Diseño limpio (#007AFF)
    └── js/chat.js             # AJAX sin recargas

agent_ia_core/                 # Motor de IA
├── agent_graph.py             # LangGraph workflow
├── recommendation_engine.py   # Evaluación multicriteria
├── retriever.py               # Búsqueda vectorial
├── xml_parser.py              # Parser de XMLs TED
├── chunking.py                # Chunking de documentos
└── config.py                  # Configuración ChromaDB
```

## Modelos de Base de Datos

### User (authentication.models)
```python
- email (unique)
- llm_api_key
- login_attempts
- bio, avatar, phone
- address fields
```

### CompanyProfile (company.models)
```python
- user (OneToOne)
- company_description_text (TextField) # Texto libre para extracción IA
- company_name, description, size
- sectors, certifications (JSONField)
- cpv_codes, nuts_regions (JSONField)
- budget_range (JSONField)
- is_complete (boolean)
```

### Tender (tenders.models)
```python
- ojs_notice_id (unique)
- title, description, budget_amount
- cpv_codes, nuts_regions (JSONField)
- buyer_name, deadline
- contract_type, procedure_type
- contact info
```

### TenderRecommendation (tenders.models)
```python
- user, tender (ForeignKey)
- score_total, score_technical, score_budget
- score_geographic, score_experience, score_competition
- probability_success
- recommendation_level (alta/media/baja)
- match_reasons, warning_factors (JSONField)
```

### ChatSession (chat.models)
```python
- user (ForeignKey)
- title
- is_archived
```

### ChatMessage (chat.models)
```python
- session (ForeignKey)
- role (user/assistant/system)
- content
- metadata (JSONField)
  - route, documents_used, verified_fields, tokens_used
```

## Flujo de Datos

### 1. Flujo de Recomendaciones

```
User → Completa CompanyProfile
  ↓
GenerateRecommendationsView
  ↓
TenderRecommendationService.generate_recommendations()
  ├→ company_profile.to_agent_format()
  ├→ _tender_to_dict() para cada Tender
  └→ recommendation_engine.evaluar_licitacion()
      ├→ Score Técnico (CPV match, áreas técnicas)
      ├→ Score Presupuesto (rango, capacidad financiera)
      ├→ Score Geográfico (NUTS regions)
      ├→ Score Experiencia (sector público, proyectos)
      └→ Score Competencia (tamaño, complejidad)
  ↓
TenderRecommendation.objects.create()
  ↓
Dashboard muestra top recomendaciones
```

### 2. Flujo de Chat

```
User → Escribe mensaje
  ↓
ChatMessageCreateView
  ↓
ChatAgentService.process_message()
  ├→ Construye conversation_history
  ├→ Establece API key en os.environ
  └→ agent_graph.invoke()
      ├→ ROUTE: Clasifica pregunta (search/detail)
      ├→ RETRIEVE: Busca en ChromaDB
      ├→ GRADE: Evalúa relevancia
      ├→ VERIFY: Verifica con XML original
      └→ ANSWER: Genera respuesta
  ↓
ChatMessage.objects.create()
  ├→ role: 'assistant'
  ├→ content: respuesta
  └→ metadata: {route, documents_used, verified_fields, tokens_used}
  ↓
Vista muestra mensaje en chat
```

### 3. Flujo de Indexación

```
Admin → Crea/importa Tender
  ↓
TenderIndexingService.index_tender()
  ├→ _tender_to_dict()
  ├→ chunking.chunk_tender_document()
  └→ ChromaDB.add()
      ├→ Crea embeddings con Google Gemini
      ├→ Almacena en colección 'licitaciones'
      └→ Metadata: ojs_notice_id, title, cpv_codes, etc.
  ↓
tender.indexed_at = now()
```

### 4. Flujo de Autocompletado de Perfil con IA

```
User → Escribe texto libre sobre empresa
  ↓
"Extraer Información con IA" button (AJAX)
  ↓
ExtractCompanyInfoView.post()
  ↓
CompanyProfileAIService.extract_company_info()
  ├→ Define Pydantic schema (20+ campos)
  ├→ Create LangChain prompt
  ├→ LLM invocation (Google Gemini, temperature=0)
  └→ PydanticOutputParser
      ├→ Extrae: nombre, sectores, empleados, ingresos, etc.
      ├→ Infiere CPV codes desde servicios mencionados
      ├→ Detecta NUTS regions desde ubicaciones
      └→ Estructura budget_range, relevant_projects
  ↓
validate_extracted_data()
  ├→ Elimina duplicados en listas
  ├→ Valida rangos numéricos
  └→ Verifica budget_range (min < max)
  ↓
JSON response → JavaScript auto-fill
  ├→ Rellena campos del formulario
  ├→ Animación de highlight en campos modificados
  └→ Usuario revisa y ajusta manualmente
  ↓
User → "Guardar" button
  ↓
CompanyProfile.objects.update()
```

## Servicios de Integración

### ChatAgentService (chat/services.py)
```python
def __init__(self, user):
    self.api_key = user.llm_api_key

def process_message(message, conversation_history):
    # 1. Set API key temporalmente
    # 2. Create agent graph
    # 3. Invoke with message
    # 4. Extract response + metadata
    # 5. Restore original API key
    return {content, metadata}
```

### TenderRecommendationService (tenders/services.py)
```python
def generate_recommendations(tenders_queryset):
    # 1. Get company profile
    # 2. Convert to agent format
    # 3. For each tender:
    #    - Convert to dict
    #    - Evaluate with recommendation_engine
    # 4. Return list of recommendations
```

### CompanyProfileAIService (company/services.py)
```python
def __init__(self, user):
    self.api_key = user.llm_api_key

def extract_company_info(company_text):
    # 1. Define Pydantic schema (CompanyInfoExtraction)
    # 2. Create LangChain parser
    # 3. Create prompt with extraction instructions
    # 4. Invoke LLM (Google Gemini 2.0 Flash, temperature=0)
    # 5. Parse structured output
    # 6. Infer CPV codes and NUTS regions
    # 7. Structure budget_range dict
    # 8. Convert relevant_projects to List[Dict]
    return extracted_data

def validate_extracted_data(data):
    # 1. Remove duplicates from lists
    # 2. Ensure numeric fields are positive
    # 3. Validate budget_range (min < max)
    return validated_data
```

## Configuración

### Variables de Entorno (.env)
```
# Django
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=

# Database
DB_ENGINE=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# Email
EMAIL_BACKEND=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Authentication
LOGIN_ATTEMPTS_ENABLED=
MAX_LOGIN_ATTEMPTS=
LOGIN_COOLDOWN_MINUTES=

# Agent_IA
LLM_PROVIDER=google
DEFAULT_K_RETRIEVE=5
CHROMA_COLLECTION_NAME=licitaciones
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## Seguridad

### API Keys
- Almacenadas por usuario en DB
- No compartidas entre usuarios
- Establecidas temporalmente en os.environ
- Restauración automática después de cada operación

### Autenticación
- Rate limiting (5 intentos, 30 min cooldown)
- Contraseñas hasheadas (PBKDF2)
- CSRF protection
- Session security

### Validación
- Inputs sanitizados
- Forms con validación Django
- Email verification (opcional)

## Despliegue

### Desarrollo
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Producción
- Usar PostgreSQL
- DEBUG=False
- Configurar Gunicorn + Nginx
- SSL con Let's Encrypt
- Archivos estáticos servidos por Nginx
- ChromaDB persistente

## Performance

### Optimizaciones Implementadas
- Select_related/prefetch_related en queries
- Índices en campos frecuentes (ojs_notice_id, user, deadline)
- Paginación en listados (20 items)
- JSONField para flexibilidad sin joins

### Optimizaciones Futuras
- Caché con Redis
- CDN para estáticos
- Celery para tareas asíncronas (indexación, recomendaciones)
- Query optimization con Django Debug Toolbar

---

**Versión**: 1.0.0  
**Última actualización**: Octubre 2025
