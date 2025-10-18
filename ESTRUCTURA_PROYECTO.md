# Estructura del Proyecto TenderAI Platform

## Resumen Ejecutivo

**TenderAI Platform** es una plataforma web Django que permite analizar licitaciones públicas usando IA. Soporta múltiples proveedores de LLM (Gemini, OpenAI, NVIDIA, Ollama) con un sistema de recomendaciones inteligente, chat conversacional con RAG, y gestión completa de licitaciones.

**Stack Tecnológico Principal:**
- Django 5.2.7 (Backend web framework)
- LangChain 0.3.x + LangGraph 0.2.x (Orquestación IA)
- ChromaDB (Base de datos vectorial)
- Bootstrap 5.3 (Frontend UI)
- Ollama/Gemini/OpenAI/NVIDIA (Proveedores LLM)

---

## 1. ARQUITECTURA GENERAL

### Diagrama de Capas
```
┌─────────────────────────────────────────────────────┐
│  PRESENTACIÓN (Templates + Static)                  │
│  - Bootstrap 5 UI, JavaScript dinámico              │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  APLICACIONES DJANGO (Apps)                         │
│  - authentication  - core  - company                │
│  - tenders        - chat                            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  SERVICIOS DE NEGOCIO                               │
│  - TenderRecommendationService                      │
│  - ChatAgentService                                 │
│  - TenderIndexingService                            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  MOTOR IA (agent_ia_core)                           │
│  - agent_graph.py (LangGraph RAG Agent)             │
│  - index_build.py (Indexación XML → ChromaDB)       │
│  - llm_factory.py (Multi-provider abstraction)      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│  ALMACENAMIENTO                                      │
│  - SQLite (db.sqlite3) - Datos estructurados        │
│  - ChromaDB (data/index/chroma) - Embeddings        │
│  - Filesystem (data/xml) - XMLs originales          │
└─────────────────────────────────────────────────────┘
```

---

## 2. ESTRUCTURA DE DIRECTORIOS

```
TenderAI_Platform/
│
├── TenderAI/                      # Configuración principal Django
│   ├── settings.py                # Configuración: INSTALLED_APPS, DATABASES, MIDDLEWARE
│   ├── urls.py                    # URLs raíz: incluye apps
│   └── wsgi.py / asgi.py          # Servidor WSGI/ASGI
│
├── authentication/                # App: Autenticación y usuarios
│   ├── models.py                  # User (extendido): llm_provider, ollama_model, etc.
│   ├── views.py                   # Login, registro, logout, password reset
│   ├── forms.py                   # LoginForm, RegisterForm
│   └── templates/authentication/  # login.html, register.html, password_reset.html
│
├── core/                          # App: Funcionalidades core (perfil, home)
│   ├── views.py                   # HomeView, ProfileView, EditProfileView, ollama_models_api
│   ├── forms.py                   # UserProfileForm (con llm_provider, ollama_model)
│   ├── ollama_checker.py          # OllamaHealthChecker: verificar instalación Ollama
│   ├── urls.py                    # /profile/, /profile/edit/, /ollama/check/, /ollama/models/
│   └── templates/core/            # home.html, profile.html, edit_profile.html, ollama_check.html
│
├── company/                       # App: Perfiles de empresa
│   ├── models.py                  # CompanyProfile: 20+ campos (CNAE, CPVs, NUTS, facturación, etc.)
│   ├── views.py                   # CompanyProfileView, autocomplete CPV/NUTS
│   ├── forms.py                   # CompanyProfileForm
│   └── templates/company/         # company_profile.html
│
├── tenders/                       # App: Gestión de licitaciones
│   ├── models.py                  # Tender: ojs_notice_id, buyer_name, title, description
│   │                              # TenderXML: xml_content, processed
│   │                              # SavedTender: user, tender, status (interesado/aplicado/ganado/perdido)
│   │
│   ├── views.py                   # CLAVES:
│   │                              # - TenderListView: listado con filtros (CPV, NUTS, fecha)
│   │                              # - TenderDetailView: detalle de licitación
│   │                              # - GenerateRecommendationsView: motor recomendaciones IA
│   │                              # - VectorizationDashboardView: panel de vectorización
│   │                              # - IndexAllTendersView: SSE streaming para indexación
│   │
│   ├── services/                  # SERVICIOS CLAVE:
│   │   ├── recommendation_service.py  # TenderRecommendationService
│   │   │                              # - generate_recommendations(): análisis multicriteria IA
│   │   │                              # - 5 dimensiones: relevancia, capacidad, competitividad, viabilidad, estratégica
│   │   │
│   │   └── vectorization_service.py   # TenderIndexingService
│   │                                  # - index_all_tenders(): indexa XMLs → ChromaDB
│   │                                  # - Crea embeddings con provider seleccionado
│   │                                  # - Soporta callbacks SSE para progreso en tiempo real
│   │
│   ├── admin.py                   # Admin interface para Tender, TenderXML, SavedTender
│   └── templates/tenders/         # tender_list.html, tender_detail.html
│                                  # recommendations.html, vectorization_dashboard.html
│
├── chat/                          # App: Chat conversacional con IA
│   ├── models.py                  # ChatSession, ChatMessage
│   ├── views.py                   # ChatListView, ChatDetailView, SendMessageView
│   ├── services.py                # ChatAgentService:
│   │                              # - process_message(): integra con agent_graph
│   │                              # - Soporte para Gemini, OpenAI, NVIDIA, Ollama
│   │
│   └── templates/chat/            # chat_list.html, chat_detail.html
│       └── static/chat/css/       # chat.css (diseño moderno estilo ChatGPT)
│
├── agent_ia_core/                 # MOTOR DE INTELIGENCIA ARTIFICIAL
│   ├── agent_graph.py             # EFormsRAGAgent (LangGraph):
│   │                              # - Workflow: question_router → retriever → grader → generator
│   │                              # - RAG con verificación y re-ranking
│   │                              # - Soporta 4 proveedores LLM
│   │
│   ├── llm_factory.py             # LLMProviderFactory:
│   │                              # - get_llm(): ChatGoogleGenerativeAI, ChatOpenAI, ChatNVIDIA, ChatOllama
│   │                              # - get_embeddings(): GoogleGenerativeAIEmbeddings, OpenAIEmbeddings, etc.
│   │
│   ├── index_build.py             # XMLIndexBuilder:
│   │                              # - parse_xml(): parsea eForms XML
│   │                              # - chunk_notice(): divide en chunks semánticos
│   │                              # - build_index(): crea ChromaDB vectorstore
│   │
│   ├── config.py                  # Configuración paths:
│   │                              # - BASE_DIR, DATA_DIR, INDEX_DIR
│   │                              # - CHROMA_PERSIST_DIRECTORY
│   │
│   └── prompts.py                 # Prompts de sistema para el agente RAG
│
├── data/                          # Datos del proyecto
│   ├── xml/                       # XMLs de licitaciones (eForms standard)
│   └── index/chroma/              # ChromaDB vectorstore (embeddings persistentes)
│
├── static/                        # Archivos estáticos
│   ├── core/css/style.css         # Estilos globales
│   ├── chat/css/chat.css          # Estilos del chat (moderno, gradientes)
│   └── tenders/css/               # Estilos específicos de licitaciones
│
├── templates/                     # Templates base
│   └── base.html                  # Template base con Bootstrap 5
│
├── db.sqlite3                     # Base de datos SQLite (en git)
├── .env                           # Variables de entorno (en git - proyecto personal)
├── requirements.txt               # Dependencias Python
├── manage.py                      # Django management script
│
└── DOCUMENTACIÓN:
    ├── ESTRUCTURA_PROYECTO.md     # Este archivo
    ├── ARCHITECTURE.md            # Arquitectura detallada con diagramas
    ├── GUIA_INSTALACION_OLLAMA.md # Guía instalación Ollama
    └── README.md                  # Documentación general

```

---

## 3. FLUJOS CLAVE DEL SISTEMA

### 3.1 Flujo de Autenticación
```
Usuario → /auth/login/ → LoginView → authentication/views.py
         ↓
    Validación credentials
         ↓
    Django Auth (authenticate)
         ↓
    Redirección a /home/
```

**Archivos involucrados:**
- `authentication/views.py`: LoginView, LogoutView, RegisterView
- `authentication/models.py`: User (modelo extendido)
- `authentication/templates/authentication/login.html`

---

### 3.2 Flujo de Configuración de Perfil
```
Usuario → /profile/edit/ → EditProfileView → core/views.py
         ↓
    UserProfileForm (core/forms.py)
         ↓
    Selecciona llm_provider: 'ollama'
         ↓
    JavaScript fetch /ollama/models/ → ollama_models_api (core/views.py)
         ↓
    OllamaHealthChecker.get_installed_models() (core/ollama_checker.py)
         ↓
    Devuelve JSON con modelos instalados
         ↓
    Popula selects dinámicos: ollama_model, ollama_embedding_model
         ↓
    Usuario selecciona: qwen2.5:72b (chat), nomic-embed-text (embeddings)
         ↓
    Form submit → Guarda en User model (authentication/models.py)
```

**Archivos involucrados:**
- `core/views.py`: EditProfileView, ollama_models_api
- `core/forms.py`: UserProfileForm
- `core/ollama_checker.py`: OllamaHealthChecker
- `core/templates/core/edit_profile.html`: AJAX para cargar modelos
- `authentication/models.py`: User.ollama_model, User.ollama_embedding_model

---

### 3.3 Flujo de Indexación (Vectorización)
```
Usuario → /licitaciones/vectorizacion/ → VectorizationDashboardView
         ↓
    Click "Indexar Todas"
         ↓
    AJAX GET /licitaciones/vectorizacion/indexar/ → IndexAllTendersView
         ↓
    TenderIndexingService(user) (tenders/vectorization_service.py)
         ↓
    index_all_tenders() en thread separado
         ↓
    [FASE 1] Crear ChromaDB client + colección
         ↓
    [FASE 2] Iterar Tender.objects.filter(xml_content__isnull=False)
         ↓
    [FASE 3] Para cada tender:
         ├─ Parsear XML → XMLIndexBuilder.parse_xml() (agent_ia_core/index_build.py)
         ├─ Chunking semántico → chunk_notice()
         ├─ Generar embeddings → LLMProviderFactory.get_embeddings()
         │   ├─ Si provider='ollama': OllamaEmbeddings(model=user.ollama_embedding_model)
         │   └─ Si provider='gemini': GoogleGenerativeAIEmbeddings()
         └─ Añadir a ChromaDB → collection.add(ids, embeddings, documents, metadatas)
         ↓
    [FASE 4] SSE progress_callback → envía eventos a frontend
         ├─ 'start': Indexación iniciada
         ├─ 'progress': tender_id indexado (X/total)
         ├─ 'info': Mensajes informativos
         └─ 'complete': Indexación completada (total_chunks, tokens, cost)
         ↓
    Frontend actualiza UI en tiempo real (tenders/templates/tenders/vectorization_dashboard.html)
```

**Archivos involucrados:**
- `tenders/views.py`: VectorizationDashboardView, IndexAllTendersView
- `tenders/vectorization_service.py`: TenderIndexingService.index_all_tenders()
- `agent_ia_core/index_build.py`: XMLIndexBuilder (parse_xml, chunk_notice)
- `agent_ia_core/llm_factory.py`: LLMProviderFactory.get_embeddings()
- `tenders/templates/tenders/vectorization_dashboard.html`: EventSource SSE listener

**ChromaDB Schema:**
```python
collection.add(
    ids=['tender_123_chunk_0'],
    embeddings=[[0.123, 0.456, ...]],  # Vector 768-dim para nomic-embed-text
    documents=['Texto del chunk de la licitación'],
    metadatas=[{
        'ojs_notice_id': '123456-2024',
        'section': 'procedure',
        'chunk_index': '0',
        'source_path': 'data/xml/123456-2024.xml',
        'buyer_name': 'Ayuntamiento de Madrid',
        'cpv_codes': '72000000,72200000',
        'nuts_regions': 'ES30',
        'publication_date': '2024-01-15'
    }]
)
```

---

### 3.4 Flujo de Chat con RAG
```
Usuario → /chat/11/ → ChatDetailView (chat/views.py)
         ↓
    Escribe mensaje: "¿Qué licitaciones hay de desarrollo de software?"
         ↓
    AJAX POST /chat/11/send/ → SendMessageView
         ↓
    ChatAgentService(user) (chat/services.py)
         ↓
    process_message(message, conversation_history)
         ↓
    _get_agent() → agent_graph.EFormsRAGAgent (agent_ia_core/agent_graph.py)
         ├─ LLM: ChatOllama(model=user.ollama_model) o ChatGoogleGenerativeAI
         ├─ Embeddings: OllamaEmbeddings(model=user.ollama_embedding_model)
         └─ VectorStore: Chroma(persist_directory='data/index/chroma')
         ↓
    agent.process_query(message)
         ↓
    [WORKFLOW LANGGRAPH]:
         ├─ question_router: ¿Requiere búsqueda vectorial?
         ├─ retriever: Busca en ChromaDB (similarity_search, k=6)
         ├─ grader: Filtra documentos relevantes
         ├─ generator: LLM genera respuesta con contexto
         └─ verification (opcional): Verifica respuesta
         ↓
    Devuelve {'content': 'Respuesta del agente IA'}
         ↓
    Guarda mensaje en ChatMessage (chat/models.py)
         ↓
    JSON response a frontend → actualiza UI
```

**Archivos involucrados:**
- `chat/views.py`: ChatDetailView, SendMessageView
- `chat/services.py`: ChatAgentService.process_message()
- `agent_ia_core/agent_graph.py`: EFormsRAGAgent (LangGraph workflow completo)
- `agent_ia_core/llm_factory.py`: LLMProviderFactory.get_llm(), get_embeddings()
- `agent_ia_core/prompts.py`: System prompts para el agente
- `chat/templates/chat/chat_detail.html`: JavaScript para chat en tiempo real

**LangGraph Workflow:**
```python
class EFormsRAGAgent:
    def _build_graph(self):
        workflow = StateGraph(GraphState)
        workflow.add_node("question_router", self._question_router)
        workflow.add_node("retriever", self._retriever)
        workflow.add_node("grader", self._grader)
        workflow.add_node("generator", self._generator)
        workflow.add_node("verification", self._verification)

        workflow.set_entry_point("question_router")
        workflow.add_conditional_edges("question_router", ...)
        workflow.add_edge("retriever", "grader")
        workflow.add_conditional_edges("grader", ...)
        workflow.add_edge("generator", END)
```

---

### 3.5 Flujo de Recomendaciones IA
```
Usuario → /licitaciones/ → TenderListView
         ↓
    Click "Generar Recomendaciones IA"
         ↓
    POST /licitaciones/recomendaciones/ → GenerateRecommendationsView
         ↓
    TenderRecommendationService(user) (tenders/services/recommendation_service.py)
         ↓
    generate_recommendations()
         ↓
    [FASE 1] Obtener perfil de empresa (company/models.py: CompanyProfile)
         ├─ CPV codes preferidos
         ├─ NUTS regions
         ├─ Facturación anual
         ├─ Número de empleados
         └─ Certificaciones
         ↓
    [FASE 2] Obtener licitaciones activas (Tender.objects.filter(deadline__gte=today))
         ↓
    [FASE 3] Para cada tender, calcular 5 dimensiones:
         ├─ RELEVANCIA SECTORIAL: Match CPV codes (30 puntos)
         ├─ CAPACIDAD TÉCNICA: Empleados, facturación, certificaciones (25 puntos)
         ├─ COMPETITIVIDAD GEOGRÁFICA: Proximidad NUTS (20 puntos)
         ├─ VIABILIDAD ECONÓMICA: Budget vs facturación (15 puntos)
         └─ VALOR ESTRATÉGICO: Análisis IA del contenido (10 puntos)
         ↓
    [FASE 4] LLM analiza descripción de tender vs perfil empresa
         ├─ Prompt: "Analiza compatibilidad entre empresa y licitación"
         └─ ChatOllama/ChatGoogleGenerativeAI genera justificación
         ↓
    [FASE 5] Calcula score total (0-100)
         ↓
    [FASE 6] Ordena por score DESC
         ↓
    Devuelve top recommendations con:
         ├─ tender: Tender object
         ├─ score: 85.5
         ├─ match_reasons: ["CPV match 90%", "Presupuesto adecuado", ...]
         └─ ai_analysis: "Esta licitación es muy relevante porque..."
         ↓
    Renderiza recommendations.html con tabla ordenada
```

**Archivos involucrados:**
- `tenders/views.py`: GenerateRecommendationsView
- `tenders/services/recommendation_service.py`: TenderRecommendationService
- `company/models.py`: CompanyProfile
- `tenders/models.py`: Tender
- `agent_ia_core/llm_factory.py`: LLMProviderFactory.get_llm()
- `tenders/templates/tenders/recommendations.html`

**Algoritmo de Scoring:**
```python
def _calculate_score(self, tender, company_profile):
    scores = {
        'relevancia_sectorial': self._score_cpv_match(tender, company_profile),  # 0-30
        'capacidad_tecnica': self._score_technical_capacity(tender, company_profile),  # 0-25
        'competitividad_geografica': self._score_geographic_fit(tender, company_profile),  # 0-20
        'viabilidad_economica': self._score_budget_fit(tender, company_profile),  # 0-15
        'valor_estrategico': self._score_strategic_value(tender, company_profile)  # 0-10 (IA)
    }
    return sum(scores.values())  # 0-100
```

---

## 4. MODELOS DE DATOS (ORM Django)

### 4.1 authentication/models.py
```python
class User(AbstractUser):
    # Campos heredados: username, email, password, first_name, last_name

    # LLM Configuration
    llm_provider = models.CharField(
        max_length=20,
        choices=[('gemini', 'Google Gemini'), ('openai', 'OpenAI'),
                 ('nvidia', 'NVIDIA NIM'), ('ollama', 'Ollama')],
        default='gemini'
    )
    llm_api_key = models.CharField(max_length=255, blank=True)  # Para cloud providers

    # Ollama specific
    ollama_model = models.CharField(max_length=100, default='qwen2.5:72b')
    ollama_embedding_model = models.CharField(max_length=100, default='nomic-embed-text')
```

### 4.2 company/models.py
```python
class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Identificación
    company_name = models.CharField(max_length=255)
    cif = models.CharField(max_length=20)

    # Sector y actividad
    cnae_codes = models.TextField()  # Códigos CNAE separados por comas
    cpv_codes = models.TextField()   # Códigos CPV preferidos

    # Capacidad técnica
    num_employees = models.IntegerField()
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    certifications = models.TextField()  # ISO 9001, ISO 27001, etc.

    # Ubicación
    nuts_regions = models.TextField()  # NUTS codes: ES30, ES51, etc.
    address = models.TextField()

    # Experiencia
    years_in_business = models.IntegerField()
    previous_contracts = models.IntegerField(default=0)

    # Preferencias
    min_budget = models.DecimalField(max_digits=15, decimal_places=2)
    max_budget = models.DecimalField(max_digits=15, decimal_places=2)
```

### 4.3 tenders/models.py
```python
class Tender(models.Model):
    # Identificación
    ojs_notice_id = models.CharField(max_length=100, unique=True)  # ID oficial TED

    # Información básica
    title = models.CharField(max_length=500)
    description = models.TextField()
    buyer_name = models.CharField(max_length=255)

    # Clasificación
    cpv_codes = models.TextField()    # Códigos CPV de la licitación
    nuts_regions = models.TextField()  # Regiones NUTS

    # Plazos y presupuesto
    publication_date = models.DateField()
    deadline = models.DateField()
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True)

    # XML original
    xml_content = models.TextField(blank=True)
    source_path = models.CharField(max_length=500)

    # Metadata
    processed = models.BooleanField(default=False)
    indexed = models.BooleanField(default=False)  # Indexado en ChromaDB
    created_at = models.DateTimeField(auto_now_add=True)

class SavedTender(models.Model):
    """Licitaciones guardadas por el usuario con estado de seguimiento"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ('interesado', 'Interesado'),
            ('aplicado', 'Aplicado'),
            ('ganado', 'Ganado'),
            ('perdido', 'Perdido')
        ]
    )
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
```

### 4.4 chat/models.py
```python
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default='Nueva Conversación')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Metadata RAG
    sources_used = models.JSONField(null=True, blank=True)  # IDs de chunks usados
```

---

## 5. SERVICIOS CLAVE

### 5.1 TenderIndexingService (tenders/vectorization_service.py)

**Responsabilidad:** Indexar XMLs de licitaciones en ChromaDB.

**Métodos principales:**
```python
class TenderIndexingService:
    def __init__(self, user=None):
        self.user = user
        self.provider = user.llm_provider if user else 'gemini'
        self.ollama_embedding_model = user.ollama_embedding_model if user else 'nomic-embed-text'

    def index_all_tenders(self, progress_callback=None, cancel_flag_checker=None):
        """
        Indexa todos los tenders con XML en ChromaDB.

        Args:
            progress_callback: Callable para reportar progreso (SSE)
            cancel_flag_checker: Callable para verificar cancelación

        Returns:
            {
                'success': True,
                'indexed': 34,
                'total_chunks': 218,
                'total_tokens': 18128,
                'total_cost_eur': 0.0
            }
        """
        # 1. Crear ChromaDB client y colección
        # 2. Obtener embeddings según provider
        # 3. Iterar tenders con XML
        # 4. Para cada tender: parse → chunk → embed → add to ChromaDB
        # 5. Reportar progreso vía callback
        # 6. Retornar estadísticas
```

**Integración con XMLIndexBuilder:**
```python
# En index_all_tenders()
from agent_ia_core.index_build import XMLIndexBuilder

builder = XMLIndexBuilder()
parsed_data = builder.parse_xml(tender.xml_content)  # Parse XML
chunks = builder.chunk_notice(parsed_data)           # Chunking semántico

for chunk in chunks:
    embedding = embeddings.embed_query(chunk.text)
    collection.add(
        ids=[chunk.chunk_id],
        embeddings=[embedding],
        documents=[chunk.text],
        metadatas=[{...}]
    )
```

---

### 5.2 ChatAgentService (chat/services.py)

**Responsabilidad:** Gestionar conversaciones de chat con RAG.

**Métodos principales:**
```python
class ChatAgentService:
    def __init__(self, user):
        self.user = user
        self.provider = user.llm_provider
        self.ollama_model = user.ollama_model
        self._agent = None  # EFormsRAGAgent (lazy initialization)

    def process_message(self, message: str, conversation_history: List[Dict] = None):
        """
        Procesa un mensaje del usuario y devuelve respuesta del agente.

        Args:
            message: Texto del mensaje
            conversation_history: [{'role': 'user', 'content': '...'}, ...]

        Returns:
            {'content': 'Respuesta del agente IA', 'sources': [...]}
        """
        # 1. Validar API key (excepto Ollama)
        # 2. Obtener/crear agente RAG
        # 3. agent.process_query(message)
        # 4. Retornar respuesta

    def _get_agent(self):
        """Lazy initialization del agente RAG"""
        if not self._agent:
            from agent_ia_core.agent_graph import EFormsRAGAgent

            if self.provider == 'ollama':
                self._agent = EFormsRAGAgent(
                    api_key=None,
                    llm_provider='ollama',
                    llm_model=self.ollama_model,
                    ollama_embedding_model=self.user.ollama_embedding_model,
                    temperature=0.3,
                    k_retrieve=6
                )
            else:
                self._agent = EFormsRAGAgent(
                    api_key=self.user.llm_api_key,
                    llm_provider=self.provider,
                    temperature=0.3
                )
        return self._agent
```

---

### 5.3 TenderRecommendationService (tenders/services/recommendation_service.py)

**Responsabilidad:** Generar recomendaciones inteligentes de licitaciones.

**Algoritmo multicriteria:**
```python
class TenderRecommendationService:
    def generate_recommendations(self, user, limit=10):
        company = CompanyProfile.objects.get(user=user)
        tenders = Tender.objects.filter(deadline__gte=date.today())

        recommendations = []
        for tender in tenders:
            score = self._calculate_score(tender, company)
            match_reasons = self._get_match_reasons(tender, company)
            ai_analysis = self._get_ai_analysis(tender, company)

            recommendations.append({
                'tender': tender,
                'score': score,
                'match_reasons': match_reasons,
                'ai_analysis': ai_analysis
            })

        return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:limit]

    def _calculate_score(self, tender, company):
        """Calcula score 0-100 en 5 dimensiones"""
        return (
            self._score_cpv_match(tender, company) +           # 0-30
            self._score_technical_capacity(tender, company) +  # 0-25
            self._score_geographic_fit(tender, company) +      # 0-20
            self._score_budget_fit(tender, company) +          # 0-15
            self._score_strategic_value(tender, company)       # 0-10 (IA)
        )
```

---

## 6. MOTOR IA (agent_ia_core/)

### 6.1 EFormsRAGAgent (agent_ia_core/agent_graph.py)

**Responsabilidad:** Agente conversacional con RAG usando LangGraph.

**Arquitectura LangGraph:**
```python
class EFormsRAGAgent:
    def __init__(self, api_key, llm_provider='gemini', llm_model=None,
                 ollama_embedding_model='nomic-embed-text', temperature=0.3,
                 k_retrieve=6, use_grading=False, use_verification=False):

        # 1. Configurar LLM
        self.llm = LLMProviderFactory.get_llm(
            provider=llm_provider,
            api_key=api_key,
            model_name=llm_model,
            temperature=temperature
        )

        # 2. Configurar Embeddings
        self.embeddings = LLMProviderFactory.get_embeddings(
            provider=llm_provider,
            api_key=api_key,
            model_name=ollama_embedding_model if llm_provider == 'ollama' else None
        )

        # 3. Cargar ChromaDB vectorstore
        self.vectorstore = Chroma(
            persist_directory=config.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings
        )

        # 4. Construir grafo LangGraph
        self.graph = self._build_graph()

    def _build_graph(self):
        """Construye workflow LangGraph"""
        workflow = StateGraph(GraphState)

        # Nodos
        workflow.add_node("question_router", self._question_router)
        workflow.add_node("retriever", self._retriever)
        workflow.add_node("grader", self._grader)
        workflow.add_node("generator", self._generator)
        workflow.add_node("verification", self._verification)

        # Flujo
        workflow.set_entry_point("question_router")
        workflow.add_conditional_edges(
            "question_router",
            lambda state: "retriever" if state["needs_retrieval"] else "generator"
        )
        workflow.add_edge("retriever", "grader")
        workflow.add_conditional_edges(
            "grader",
            lambda state: "generator" if state["relevant_docs"] else "fallback"
        )
        workflow.add_edge("generator", END)

        return workflow.compile()

    def process_query(self, query: str):
        """Procesa query del usuario a través del grafo"""
        result = self.graph.invoke({
            "question": query,
            "generation": "",
            "documents": [],
            "relevant_docs": [],
            "needs_retrieval": True
        })
        return result
```

**Nodos del Workflow:**

1. **question_router**: Determina si la pregunta requiere búsqueda vectorial
2. **retriever**: Busca documentos similares en ChromaDB (similarity_search)
3. **grader**: Filtra documentos relevantes usando LLM
4. **generator**: Genera respuesta final usando LLM + contexto
5. **verification**: Verifica calidad de la respuesta (opcional)

---

### 6.2 LLMProviderFactory (agent_ia_core/llm_factory.py)

**Responsabilidad:** Abstracción multi-provider para LLMs y Embeddings.

```python
class LLMProviderFactory:
    @staticmethod
    def get_llm(provider: str, api_key: str = None, model_name: str = None,
                temperature: float = 0.3):
        """
        Factory method para obtener LLM según provider.

        Proveedores soportados:
        - gemini: ChatGoogleGenerativeAI (gemini-2.0-flash-exp)
        - openai: ChatOpenAI (gpt-4-turbo)
        - nvidia: ChatNVIDIA (meta/llama-3.1-70b-instruct)
        - ollama: ChatOllama (qwen2.5:72b, llama3.3:70b, etc.)
        """
        if provider == 'ollama':
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model_name or 'qwen2.5:72b',
                temperature=temperature,
                base_url='http://localhost:11434'
            )

        elif provider == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model='gemini-2.0-flash-exp',
                google_api_key=api_key,
                temperature=temperature
            )

        # ... openai, nvidia ...

    @staticmethod
    def get_embeddings(provider: str, api_key: str = None, model_name: str = None):
        """
        Factory method para obtener Embeddings según provider.

        Modelos soportados:
        - ollama: OllamaEmbeddings (nomic-embed-text, mxbai-embed-large)
        - gemini: GoogleGenerativeAIEmbeddings (text-embedding-004)
        - openai: OpenAIEmbeddings (text-embedding-3-large)
        - nvidia: NVIDIAEmbeddings (nvidia/nv-embedqa-e5-v5)
        """
        if provider == 'ollama':
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(
                model=model_name or 'nomic-embed-text',
                base_url='http://localhost:11434'
            )

        elif provider == 'gemini':
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model='models/text-embedding-004',
                google_api_key=api_key
            )

        # ... openai, nvidia ...
```

---

### 6.3 XMLIndexBuilder (agent_ia_core/index_build.py)

**Responsabilidad:** Parsear XMLs eForms y crear chunks semánticos.

```python
class XMLIndexBuilder:
    def parse_xml(self, xml_content: str) -> Dict:
        """
        Parsea XML eForms estándar y extrae información estructurada.

        Returns:
            {
                'ojs_notice_id': '123456-2024',
                'title': 'Desarrollo de software...',
                'buyer_name': 'Ayuntamiento de Madrid',
                'description': '...',
                'cpv_codes': ['72000000', '72200000'],
                'nuts_regions': ['ES30'],
                'publication_date': '2024-01-15',
                'deadline': '2024-02-15',
                'sections': {
                    'procedure': '...',
                    'object': '...',
                    'tender': '...',
                    'award': '...'
                }
            }
        """
        # Parse XML con ElementTree
        # Extrae campos según estándar eForms
        # Normaliza datos

    def chunk_notice(self, parsed_data: Dict, chunk_size: int = 1000) -> List[Chunk]:
        """
        Divide la licitación en chunks semánticos para embeddings.

        Estrategia:
        - Chunk por sección (procedure, object, tender, award)
        - Máximo chunk_size caracteres
        - Preserva contexto con metadata

        Returns:
            [
                Chunk(
                    chunk_id='tender_123_chunk_0',
                    text='Texto del chunk...',
                    ojs_notice_id='123456-2024',
                    section='procedure',
                    chunk_index=0,
                    metadata={...}
                ),
                ...
            ]
        """
        chunks = []
        for section_name, section_text in parsed_data['sections'].items():
            # Dividir sección en chunks de chunk_size
            # Crear objetos Chunk con metadata
            chunks.append(Chunk(...))
        return chunks
```

---

## 7. CONFIGURACIÓN Y VARIABLES DE ENTORNO

### 7.1 .env (Variables de Entorno)

```bash
# Django
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# LLM API Keys (opcionales según provider)
GOOGLE_API_KEY=tu-api-key-gemini        # Para Gemini
OPENAI_API_KEY=tu-api-key-openai        # Para OpenAI
NVIDIA_API_KEY=tu-api-key-nvidia        # Para NVIDIA NIM

# Ollama (no requiere API key, local)
OLLAMA_BASE_URL=http://localhost:11434

# ChromaDB
CHROMA_PERSIST_DIRECTORY=data/index/chroma
CHROMA_COLLECTION_NAME=eforms_notices

# Paths
DATA_DIR=data
XML_DIR=data/xml
INDEX_DIR=data/index
```

### 7.2 settings.py (Configuración Django)

**INSTALLED_APPS:**
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'authentication',
    'core',
    'company',
    'tenders',
    'chat',
]
```

**AUTH_USER_MODEL:**
```python
AUTH_USER_MODEL = 'authentication.User'
```

**STATIC & MEDIA:**
```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

## 8. FRONTEND (Templates & JavaScript)

### 8.1 Template Base (templates/base.html)

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}TenderAI Platform{% endblock %}</title>

    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">

    <!-- Custom CSS -->
    <link href="{% static 'core/css/style.css' %}" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'core:home' %}">
                <i class="bi bi-briefcase-fill"></i> TenderAI
            </a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    {% if user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link" href="{% url 'tenders:list' %}">Licitaciones</a></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'chat:list' %}">Chat IA</a></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'core:profile' %}">Perfil</a></li>
                        <li class="nav-item"><a class="nav-link" href="{% url 'authentication:logout' %}">Salir</a></li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link" href="{% url 'authentication:login' %}">Login</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <!-- Content -->
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

### 8.2 Chat Interface (chat/templates/chat/chat_detail.html)

**JavaScript clave para chat en tiempo real:**

```javascript
// Enviar mensaje
async function sendMessage() {
    const message = document.getElementById('message-input').value;

    // Añadir mensaje del usuario a UI
    appendMessage('user', message);

    // POST a backend
    const response = await fetch(`/chat/{{ session.id }}/send/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ message: message })
    });

    const data = await response.json();

    // Añadir respuesta del asistente
    appendMessage('assistant', data.content);
}

function appendMessage(role, content) {
    const messagesContainer = document.getElementById('messages-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-bubble ${role}`;
    messageDiv.textContent = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
```

---

### 8.3 Vectorization Dashboard (tenders/templates/tenders/vectorization_dashboard.html)

**Server-Sent Events (SSE) para progreso en tiempo real:**

```javascript
function startIndexing() {
    const eventSource = new EventSource('/licitaciones/vectorizacion/indexar/');
    const logsContainer = document.getElementById('indexing-logs');

    eventSource.addEventListener('start', (e) => {
        const data = JSON.parse(e.data);
        addLog(`🚀 ${data.message}`, 'info');
    });

    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        addLog(`✓ ${data.message}`, 'success');
        updateProgressBar(data.indexed, data.total);
    });

    eventSource.addEventListener('info', (e) => {
        const data = JSON.parse(e.data);
        addLog(`ℹ ${data.message}`, 'info');
    });

    eventSource.addEventListener('error', (e) => {
        const data = JSON.parse(e.data);
        const errorContext = data.tender_id || 'indexación';
        const errorMsg = data.error || data.message || 'Error desconocido';
        addLog(`✗ Error en ${errorContext}: ${errorMsg}`, 'error');
    });

    eventSource.addEventListener('complete', (e) => {
        const data = JSON.parse(e.data);
        addLog(`✅ ${data.message}`, 'success');
        eventSource.close();
        setTimeout(() => location.reload(), 2000);
    });
}

function addLog(message, type) {
    const logsContainer = document.getElementById('indexing-logs');
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}
```

---

## 9. DEPENDENCIAS CRÍTICAS (requirements.txt)

```txt
# Django
Django==5.2.7
django-cors-headers==4.3.1
djangorestframework==3.14.0
python-decouple==3.8

# LangChain Core
langchain-core>=0.3.72,<1.0.0      # Compatible con langchain 0.3.x
langchain>=0.3.27,<0.4.0
langgraph>=0.2.63,<1.0.0

# LangChain Providers
langchain-ollama>=0.2.0,<1.0.0     # Ollama (local)
langchain-google-genai>=2.0.8      # Google Gemini
langchain-openai>=0.2.14           # OpenAI
langchain-nvidia-ai-endpoints>=0.3.12  # NVIDIA NIM

# Vector Database
chromadb>=0.5.23

# Utilities
tiktoken>=0.8.0                    # Token counting
lxml>=5.3.0                        # XML parsing
beautifulsoup4>=4.12.3             # HTML parsing (opcional)
```

**IMPORTANTE - Versiones compatibles:**
- `langchain-core` debe ser `<1.0.0` para compatibilidad con `langchain 0.3.x`
- `langchain-ollama` debe ser `0.2.x` (la versión 1.0.x requiere `langchain-core>=1.0.0`)

---

## 10. COMANDOS ÚTILES

### Django Management
```bash
# Iniciar servidor de desarrollo
python manage.py runserver 8001

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Shell interactivo
python manage.py shell
```

### Ollama (Local LLM)
```bash
# Verificar instalación
ollama --version

# Listar modelos instalados
ollama list

# Descargar modelos recomendados
ollama pull qwen2.5:72b
ollama pull nomic-embed-text

# Ejecutar modelo manualmente
ollama run qwen2.5:72b "Hola, ¿cómo estás?"
```

### ChromaDB
```bash
# Verificar estado desde Python
python
>>> import chromadb
>>> client = chromadb.PersistentClient(path='data/index/chroma')
>>> collection = client.get_collection(name='eforms_notices')
>>> print(collection.count())  # Número de chunks indexados
```

---

## 11. PUNTOS DE ENTRADA CLAVE PARA IA

Si eres una IA leyendo este documento para entender el proyecto rápidamente:

### Para entender el flujo de datos completo:
1. Lee: `tenders/views.py` → `IndexAllTendersView` (SSE streaming)
2. Lee: `tenders/vectorization_service.py` → `index_all_tenders()`
3. Lee: `agent_ia_core/index_build.py` → `parse_xml()` + `chunk_notice()`
4. Lee: `agent_ia_core/llm_factory.py` → `get_embeddings()`

### Para entender el chat RAG:
1. Lee: `chat/views.py` → `SendMessageView`
2. Lee: `chat/services.py` → `ChatAgentService.process_message()`
3. Lee: `agent_ia_core/agent_graph.py` → `EFormsRAGAgent._build_graph()`
4. Lee: `agent_ia_core/prompts.py` → Prompts del sistema

### Para entender las recomendaciones:
1. Lee: `tenders/views.py` → `GenerateRecommendationsView`
2. Lee: `tenders/services/recommendation_service.py` → `TenderRecommendationService`
3. Lee: `company/models.py` → `CompanyProfile` (datos de entrada)

### Para entender la configuración multi-provider:
1. Lee: `authentication/models.py` → `User` (llm_provider, ollama_model)
2. Lee: `core/views.py` → `EditProfileView` + `ollama_models_api`
3. Lee: `core/ollama_checker.py` → `OllamaHealthChecker`
4. Lee: `agent_ia_core/llm_factory.py` → `LLMProviderFactory`

### Modelos de datos críticos:
- `authentication/models.py`: User
- `company/models.py`: CompanyProfile
- `tenders/models.py`: Tender, SavedTender
- `chat/models.py`: ChatSession, ChatMessage

### Templates UI clave:
- `tenders/templates/tenders/vectorization_dashboard.html` (SSE)
- `chat/templates/chat/chat_detail.html` (Chat en tiempo real)
- `core/templates/core/edit_profile.html` (Configuración provider)

---

## 12. FLUJO DE INSTALACIÓN COMPLETO

Para replicar el proyecto en otra máquina:

```bash
# 1. Clonar repositorio
git clone https://github.com/AdrianUbedaTouati/TED.git
cd TED

# 2. Crear virtualenv
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env con tus API keys (opcional según provider)

# 5. Migraciones Django
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Instalar Ollama (opcional, solo para provider local)
# Windows: Ejecutar instalar_ollama.bat como administrador
# O descargar de https://ollama.com/download

# 8. Descargar modelos Ollama
ollama pull qwen2.5:72b
ollama pull nomic-embed-text

# 9. Iniciar servidor
python manage.py runserver 8001

# 10. Acceder a http://localhost:8001
```

---

## 13. ARQUITECTURA DE SEGURIDAD

### Autenticación:
- Django `django.contrib.auth` con User extendido
- Login/Logout views estándar
- Password reset por email (configurar SMTP en settings.py)

### API Keys:
- Almacenadas en User model (`llm_api_key`)
- Nunca expuestas en frontend
- Validadas en backend antes de uso

### Permisos:
- `@login_required` en todas las views protegidas
- ChatSession/SavedTender filtrados por `user`
- CompanyProfile OneToOne con User

---

## 14. ROADMAP Y MEJORAS FUTURAS

### Próximas funcionalidades:
- [ ] Notificaciones email de nuevas licitaciones
- [ ] Export PDF de recomendaciones
- [ ] Filtros avanzados en listado licitaciones
- [ ] Dashboard analytics (métricas de uso)
- [ ] Sistema de alertas por CPV/NUTS
- [ ] Integración con TED API para actualización automática
- [ ] Soporte multi-idioma (i18n)
- [ ] Tests automatizados (pytest + Django TestCase)

### Optimizaciones técnicas:
- [ ] Caché Redis para recomendaciones
- [ ] Celery para indexación asíncrona
- [ ] PostgreSQL en producción (en lugar de SQLite)
- [ ] Nginx + Gunicorn deployment
- [ ] Docker Compose para desarrollo
- [ ] CI/CD con GitHub Actions

---

## 15. CONTACTO Y SOPORTE

**Proyecto:** TenderAI Platform
**Repositorio:** https://github.com/AdrianUbedaTouati/TED
**Autor:** Adrian Ubeda Touati
**Documentación adicional:**
- ARCHITECTURE.md - Arquitectura técnica detallada
- GUIA_INSTALACION_OLLAMA.md - Guía instalación Ollama
- README.md - Documentación general

---

**Última actualización:** 2025-10-18
**Versión:** 1.0.0 (Initial Release con integración Ollama completa)
