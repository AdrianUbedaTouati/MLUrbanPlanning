# 🏗️ Arquitectura del Sistema TenderAI v3.7.1

**Sistema de Function Calling Multi-Proveedor con Review Loop Automático**

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Estructura de agent_ia_core](#estructura-de-agent_ia_core)
4. [Componentes Principales](#componentes-principales)
5. [Sistema de Tools](#sistema-de-tools)
6. [Sistema de Review y Mejora](#sistema-de-review-y-mejora)
7. [Flujo de Datos Completo](#flujo-de-datos-completo)
8. [Proveedores LLM](#proveedores-llm)
9. [Base de Datos](#base-de-datos)

---

## 🎯 Visión General

TenderAI es una plataforma Django que utiliza **Function Calling** para permitir que los LLMs interactúen dinámicamente con datos de licitaciones públicas mediante **16 tools especializadas** y un **sistema de auto-mejora** con doble LLM.

### Características Clave v3.7

- ✅ **3 proveedores LLM**: Ollama (local), OpenAI, Google Gemini
- ✅ **16 tools especializadas**: Búsqueda, análisis, web, navegación interactiva
- ✅ **Review Loop automático**: Segunda iteración SIEMPRE ejecutada
- ✅ **Navegador interactivo**: Playwright para sitios JavaScript
- ✅ **Web Search**: Google Custom Search API
- ✅ **Grading y Verification**: Filtrado inteligente de documentos
- ✅ **ChromaDB**: Búsqueda vectorial semántica
- ✅ **Iteración inteligente**: Hasta 15 pasos para consultas complejas

---

## 🏛️ Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                         │
│                     Bootstrap 5 + JavaScript                      │
└────────────────────────────┬──────────────────────────────────────┘
                            │ HTTP/AJAX
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO APPLICATION                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      chat/views.py                         │  │
│  │              (ChatMessageCreateView)                       │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │                  chat/services.py                          │  │
│  │                 (ChatAgentService)                         │  │
│  │                                                            │  │
│  │  - Detecta proveedor del usuario                          │  │
│  │  - Crea FunctionCallingAgent                              │  │
│  │  - Ejecuta Review Loop (SIEMPRE)                          │  │
│  │  - Maneja historial conversacional                        │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │               chat/response_reviewer.py                    │  │
│  │                 (ResponseReviewer)                         │  │
│  │                                                            │  │
│  │  - Revisa formato (30%)                                   │  │
│  │  - Revisa contenido (40%)                                 │  │
│  │  - Revisa análisis (30%)                                  │  │
│  │  - Proporciona feedback específico                        │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬│─────────────────────────────────────┘
                            ││
            ┌───────────────┘└───────────────┐
            ↓                                 ↓
┌─────────────────────────┐     ┌─────────────────────────┐
│   AGENT_IA_CORE         │     │   DJANGO ORM            │
│                         │     │                         │
│  FunctionCallingAgent   │────→│  Tender Model           │
│  ToolRegistry (16)      │     │  CompanyProfile         │
│  SchemaConverter        │     │  ChatMessage            │
│  ResponseReviewer LLM   │     │  User                   │
└───────────┬─────────────┘     └─────────────────────────┘
            │
            ├──→ Ollama (localhost:11434)
            ├──→ OpenAI API
            ├──→ Google Gemini API
            ├──→ Google Custom Search API
            └──→ Playwright (Chromium)
```

---

## 📦 Estructura de agent_ia_core (v3.7.1)

El motor de IA ha sido reorganizado en modulos especializados:

```
agent_ia_core/
├── agent_function_calling.py   # Motor principal del agente
├── config.py                   # Configuracion centralizada
├── prompts_config.py           # CPV codes, NUTS codes, templates
│
├── parser/                     # Parsing y chunking de XMLs
│   ├── xml_parser.py           # EFormsXMLParser - parser de eForms
│   ├── chunking.py             # EFormsChunker - chunking semantico
│   └── tools_xml.py            # XmlLookupTool - XPath queries
│
├── prompts/                    # System prompts
│   └── prompts.py              # SYSTEM_PROMPT, RAG_PROMPT, etc.
│
├── indexing/                   # RAG y vectorizacion
│   ├── retriever.py            # HybridRetriever - busqueda vectorial
│   ├── index_build.py          # IndexBuilder - construccion de indices
│   └── ingest.py               # EFormsIngestor - ingesta de datos
│
├── download/                   # Descarga de licitaciones
│   ├── descarga_xml.py         # Descarga desde TED API
│   └── token_tracker.py        # TokenTracker - costos y uso
│
├── engines/                    # Motores especializados
│   └── recommendation_engine.py # Motor de recomendaciones
│
├── tools/                      # 16 Tools del agente
│   ├── registry.py             # ToolRegistry
│   ├── base.py                 # BaseTool
│   ├── search_tools.py         # find_by_*, search_tenders
│   ├── tender_tools.py         # get_tender_*, compare_*
│   ├── context_tools.py        # get_company_info, get_tenders_summary
│   ├── web_search_tool.py      # Google Custom Search
│   ├── browse_tool.py          # browse_webpage
│   ├── browse_interactive_tool.py # Playwright navigation
│   ├── grading_tool.py         # grade_documents
│   └── verification_tool.py    # verify_fields
│
└── schema/                     # Schemas eForms UBL
```

---

## 🧩 Componentes Principales

### 1. FunctionCallingAgent

**Ubicación**: `agent_ia_core/agent_function_calling.py`

**Responsabilidades**:
- Coordinar la ejecución de tools (16 disponibles)
- Gestionar iteraciones (máximo 15)
- Comunicarse con diferentes proveedores LLM
- Mantener historial conversacional

**Métodos clave**:
```python
class FunctionCallingAgent:
    def __init__(self, llm_provider, llm_model, llm_api_key, retriever, db_session, user):
        # Inicializa LLM según proveedor
        self.llm = self._create_llm()
        self.tool_registry = ToolRegistry(retriever, db_session, user)
        self.max_iterations = 15

    def query(self, question, conversation_history):
        # Loop de function calling (máx 15 iteraciones)
        # 1. LLM decide tools
        # 2. Ejecutar tools
        # 3. LLM procesa resultados
        # 4. Repetir o retornar respuesta
```

### 2. ToolRegistry

**Ubicación**: `agent_ia_core/tools/registry.py`

**Responsabilidades**:
- Registrar las 16 tools disponibles
- Convertir schemas al formato del proveedor
- Ejecutar tool calls en paralelo
- Inyectar LLM a tools que lo necesitan

**Tools registradas**:
```python
# Tools de contexto (2)
- get_company_info: Información de empresa del usuario
- get_tenders_summary: Resumen de licitaciones guardadas

# Tools de búsqueda (5)
- search_tenders: Búsqueda vectorial ChromaDB
- find_by_budget: Filtrado por presupuesto
- find_by_deadline: Filtrado por fecha
- find_by_cpv: Filtrado por sector
- find_by_location: Filtrado geográfico

# Tools de información (2)
- get_tender_details: Detalles completos
- get_tender_xml: XML original

# Tools de análisis (2)
- get_statistics: Estadísticas agregadas
- compare_tenders: Comparación lado a lado

# Tools opcionales (5)
- grade_documents: Filtrado inteligente (opcional)
- verify_fields: Verificación con XML (opcional)
- web_search: Google Custom Search (opcional)
- browse_webpage: Extracción web estática (opcional)
- browse_interactive: Navegador Playwright (opcional)
```

### 3. ResponseReviewer

**Ubicación**: `chat/response_reviewer.py`

**Responsabilidades**:
- Revisar respuesta inicial del agente principal
- Evaluar formato, contenido y análisis
- Proporcionar feedback específico y constructivo
- Generar score de calidad (0-100)

**Criterios de evaluación**:
```python
FORMATO (30 puntos):
- ¿Usa Markdown correctamente?
- ¿Headers ## para múltiples licitaciones?
- ¿Estructura clara y legible?

CONTENIDO (40 puntos):
- ¿Responde completamente la pregunta?
- ¿Incluye todos los datos relevantes?
- ¿Falta información importante?

ANÁLISIS (30 puntos):
- ¿Justifica recomendaciones con datos?
- ¿Usa documentos correctamente?
- ¿Es útil y profesional?
```

**Proceso**:
1. Recibe respuesta inicial + metadata
2. Llama al LLM revisor con prompt específico
3. Parsea resultado (status, score, issues, suggestions, feedback)
4. Retorna análisis estructurado

### 4. ChatAgentService (con Review Loop)

**Ubicación**: `chat/services.py`

**Responsabilidad**: Orquestar el flujo completo con mejora automática

**Flujo actualizado**:
```python
class ChatAgentService:
    def process_message(self, message, conversation_history):
        # 1. Ejecutar query inicial
        result = agent.query(message, conversation_history)
        response_content = result['answer']

        # 2. REVIEW LOOP (SIEMPRE ejecutado)
        reviewer = ResponseReviewer(agent.llm)
        review_result = reviewer.review_response(
            user_question=message,
            conversation_history=conversation_history,
            initial_response=response_content,
            metadata=result
        )

        # 3. Segunda iteración de mejora (SIEMPRE)
        improvement_prompt = f"""Tu respuesta fue revisada.

        Respuesta original: {response_content}

        Problemas: {review_result['issues']}
        Sugerencias: {review_result['suggestions']}
        Feedback: {review_result['feedback']}

        Genera una respuesta MEJORADA con acceso completo a tools."""

        improved_result = agent.query(
            improvement_prompt,
            conversation_history + [
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': response_content}
            ]
        )

        # 4. Merge resultados de ambas iteraciones
        final_response = improved_result['answer']
        final_documents = result['documents'] + improved_result['documents']

        return final_response, final_documents, review_metadata
```

### 5. Retriever (ChromaDB)

**Ubicación**: `agent_ia_core/retriever.py`

**Responsabilidad**: Búsqueda vectorial semántica

```python
class HybridRetriever:
    def __init__(self, provider, api_key, embedding_model, k):
        self.embeddings = self._create_embeddings(provider, api_key, embedding_model)
        self.vectorstore = Chroma(
            collection_name="eforms_chunks",
            embedding_function=self.embeddings,
            persist_directory="data/index/chroma"
        )

    def retrieve(self, query, filters=None, k=None):
        results = self.vectorstore.similarity_search_with_score(
            query, k=k, filter=filters
        )
        return self._format_results(results)
```

---

## 🛠️ Sistema de Tools

### Categorización Completa (16 Tools)

#### 🏢 Tools de Contexto (2)
**Descripción**: Información específica del usuario

1. **get_company_info**: Perfil de empresa del usuario
2. **get_tenders_summary**: Resumen de licitaciones guardadas

**Activación**: Automática si hay usuario autenticado

#### 🔍 Tools de Búsqueda (5)
**Descripción**: Búsqueda y filtrado de licitaciones

3. **search_tenders**: Búsqueda vectorial semántica (ChromaDB)
4. **find_by_budget**: Filtrado por rango de presupuesto (SQL)
5. **find_by_deadline**: Filtrado por fecha límite (SQL)
6. **find_by_cpv**: Filtrado por sector CPV (ChromaDB)
7. **find_by_location**: Filtrado geográfico NUTS (ChromaDB)

**Activación**: Siempre disponibles

#### 📄 Tools de Información (2)
**Descripción**: Detalles completos de licitaciones

8. **get_tender_details**: Información completa desde DB
9. **get_tender_xml**: XML original completo

**Activación**: Siempre disponibles

#### 📊 Tools de Análisis (2)
**Descripción**: Estadísticas y comparaciones

10. **get_statistics**: Estadísticas agregadas
11. **compare_tenders**: Comparación lado a lado (2-5 licitaciones)

**Activación**: Siempre disponibles

#### 🎯 Tools de Calidad (2 - Opcionales)
**Descripción**: Mejora de resultados

12. **grade_documents**: Filtrado inteligente de documentos irrelevantes
13. **verify_fields**: Verificación de campos críticos con XML

**Activación**: `use_grading=True`, `use_verification=True` en User model

#### 🌐 Tools de Web (3 - Opcionales)
**Descripción**: Búsqueda e interacción web

14. **web_search**: Google Custom Search API
15. **browse_webpage**: Extracción HTML estática (requests + BeautifulSoup)
16. **browse_interactive**: Navegador con Playwright (JavaScript, clicks, formularios)

**Activación**:
- `use_web_search=True` + Google API credentials
- `browse_interactive` requiere Playwright instalado

---

## 🔄 Sistema de Review y Mejora

### Flujo Completo del Review Loop

```
1. ITERACIÓN INICIAL
   Usuario: "Dame las mejores licitaciones de software"
   ↓
   Agent ejecuta tools → Genera respuesta inicial
   ↓

2. REVIEW (SIEMPRE ejecutado)
   ResponseReviewer analiza:
   - Formato: ¿Usa ## para cada licitación?
   - Contenido: ¿Incluye presupuestos, plazos?
   - Análisis: ¿Justifica por qué son las "mejores"?
   ↓
   Resultado: {
     status: "NEEDS_IMPROVEMENT" / "APPROVED",
     score: 75,
     issues: ["Falta justificación de por qué son mejores"],
     suggestions: ["Agregar análisis de fit con perfil usuario"],
     feedback: "Explica por qué cada licitación es adecuada"
   }
   ↓

3. SEGUNDA ITERACIÓN (SIEMPRE ejecutada)
   Prompt mejorado:
   "Tu respuesta inicial: [...]
    Problemas: [...]
    Sugerencias: [...]

    Genera respuesta MEJORADA con acceso a tools"
   ↓
   Agent ejecuta tools nuevamente si necesita → Genera respuesta mejorada
   ↓

4. MERGE Y RETORNO
   - Response final: respuesta mejorada
   - Documents: docs iteración 1 + docs iteración 2
   - Tools used: union de ambas iteraciones
   - Metadata: incluye info de review
```

### Metadata de Review

```python
{
    'review': {
        'review_performed': True,
        'review_status': 'NEEDS_IMPROVEMENT',
        'review_score': 75,
        'review_issues': ['Falta X', 'Falta Y'],
        'review_suggestions': ['Agregar Z'],
        'improvement_applied': True
    }
}
```

---

## 🔄 Flujo de Datos Completo

### Usuario hace pregunta: "Busca licitaciones de IT > 50k con review"

```
1. FRONTEND
   JavaScript → POST /chat/<session_id>/message/

2. DJANGO VIEWS
   ChatMessageCreateView
   → Guarda mensaje usuario
   → Llama ChatAgentService.process_message()

3. CHATAGENTSERVICE - ITERACIÓN 1
   → Crea FunctionCallingAgent
   → Ejecuta agent.query()

4. FUNCTIONCALLINGAGENT - ITERACIÓN 1
   Paso 1: LLM decide tools
   → "Voy a usar find_by_cpv('IT') y find_by_budget(min=50000)"

   Paso 2: ToolRegistry ejecuta
   → find_by_cpv → 10 licitaciones IT
   → find_by_budget → 8 licitaciones >50k

   Paso 3: LLM genera respuesta inicial
   → "Encontré 3 licitaciones que cumplen ambos criterios..."

   Retorna: {answer, documents, tools_used, iterations}

5. CHATAGENTSERVICE - REVIEW
   → Crea ResponseReviewer(llm)
   → reviewer.review_response()

6. RESPONSEREVIEWER
   → Llama LLM con prompt de revisión
   → Analiza formato, contenido, análisis
   → Retorna: {status, score, issues, suggestions, feedback}

7. CHATAGENTSERVICE - ITERACIÓN 2 (SIEMPRE)
   → Construye improvement_prompt
   → Ejecuta agent.query(improvement_prompt)

8. FUNCTIONCALLINGAGENT - ITERACIÓN 2
   Paso 1: LLM lee feedback
   → "Necesito agregar análisis de por qué son las mejores"
   → "Voy a usar get_company_info() para contexto"

   Paso 2: Ejecuta get_company_info
   → Perfil de empresa del usuario

   Paso 3: LLM genera respuesta mejorada
   → "Basándome en tu perfil de empresa...
      estas son las mejores porque:
      1. Licitación X - match 95% con tu experiencia..."

   Retorna: {answer mejorado, documents nuevos, tools_used}

9. CHATAGENTSERVICE - MERGE
   → Response final = respuesta mejorada
   → Documents = docs iter1 + docs iter2
   → Tools used = union
   → Metadata incluye review tracking

10. DJANGO VIEWS
    → Guarda ChatMessage con respuesta final
    → Retorna JSON al frontend

11. FRONTEND
    → Renderiza respuesta mejorada
    → Muestra metadata (review score, tools usadas)
```

---

## 🤖 Proveedores LLM

### Ollama (Local)

**Comunicación**:
```python
import ollama

response = ollama.chat(
    model='qwen2.5:7b',
    messages=messages,
    tools=tool_registry.get_ollama_tools()
)
```

**Ventajas**:
- 🆓 Gratis
- 🔒 100% local (privacidad)
- ⚡ Sin latencia de red

**Desventajas**:
- 💻 Requiere recursos (16GB+ RAM)
- 🎯 Calidad depende del modelo

### OpenAI (Cloud)

**Comunicación**:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model='gpt-4o-mini', api_key=api_key)
llm_with_tools = llm.bind_tools(tool_registry.get_openai_tools())
response = llm_with_tools.invoke(messages)
```

**Ventajas**:
- 🎯 Alta calidad
- ⚡ Rápido
- 📊 Excelente en consultas complejas

**Desventajas**:
- 💰 Costo por token
- ☁️ Datos en cloud

### Google Gemini (Cloud)

**Comunicación**:
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=api_key)
llm_with_tools = llm.bind_tools(tool_registry.get_gemini_tools())
response = llm_with_tools.invoke(messages)
```

**Ventajas**:
- 💰 Más económico que OpenAI
- ⚡ Muy rápido
- 🎯 Buena calidad

**Desventajas**:
- 💰 Costo por token
- ☁️ Datos en cloud

---

## 💾 Base de Datos

### Modelos Django

#### User (authentication/models.py)
```python
class User(AbstractUser):
    # Basic
    email = EmailField(unique=True)

    # LLM Config
    llm_provider = CharField(max_length=50)  # 'ollama', 'openai', 'google'
    llm_api_key = TextField(blank=True)
    ollama_model = CharField(max_length=100)
    openai_model = CharField(max_length=100)  # Nuevo campo

    # Features
    use_function_calling = BooleanField(default=True)
    use_grading = BooleanField(default=False)
    use_verification = BooleanField(default=False)
    use_web_search = BooleanField(default=False)

    # Google Custom Search (para web_search)
    google_search_api_key = TextField(blank=True)
    google_search_engine_id = CharField(max_length=100, blank=True)

    # Browse settings
    browse_max_chars = IntegerField(default=10000)
    browse_chunk_size = IntegerField(default=1250)
```

#### Tender (tenders/models.py)
```python
class Tender(Model):
    ojs_notice_id = CharField(max_length=255, unique=True)
    title = TextField()
    description = TextField(blank=True)
    buyer_name = CharField(max_length=500)
    budget_amount = DecimalField(max_digits=15, decimal_places=2, null=True)
    currency = CharField(max_length=3, null=True)
    tender_deadline_date = DateField(null=True)
    cpv_codes = JSONField(default=list)
    nuts_regions = JSONField(default=list)
    source_path = CharField(max_length=500, blank=True)
```

#### ChatMessage (chat/models.py)
```python
class ChatMessage(Model):
    session = ForeignKey(ChatSession, on_delete=CASCADE)
    role = CharField(max_length=20)  # 'user', 'assistant'
    content = TextField()
    timestamp = DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict)  # Incluye review tracking
```

### ChromaDB

**Colección**: `eforms_chunks`
**Documentos**: 235+ chunks

**Metadata por documento**:
```python
{
    'ojs_notice_id': '00668461-2025',
    'section': 'object_description',
    'title': 'Desarrollo de software',
    'buyer_name': 'Ministerio',
    'cpv_codes': ['72000000'],
    'nuts_regions': ['ES300'],
    'budget_amount': 961200.0,
    'budget_eur': '961200.0',  # String para filtros
    'tender_deadline_date': '2025-09-15'
}
```

---

## 📊 Métricas de Rendimiento

### Latencia con Review Loop

| Operación | Ollama | OpenAI | Gemini |
|-----------|--------|--------|--------|
| **Iteración 1** | 500-1000ms | 800-1500ms | 600-1200ms |
| **Review** | 200-400ms | 300-600ms | 200-500ms |
| **Iteración 2** | 500-1000ms | 800-1500ms | 600-1200ms |
| **Total** | 1.2-2.4s | 1.9-3.6s | 1.4-2.9s |

### Consumo de Recursos

| Proveedor | RAM | CPU | Disco | Red |
|-----------|-----|-----|-------|-----|
| **Ollama** | 8-16GB | Alto | 5-10GB | No |
| **OpenAI** | < 500MB | Bajo | Mínimo | Sí |
| **Gemini** | < 500MB | Bajo | Mínimo | Sí |

---

## 🔗 Referencias

- **Código fuente**: `agent_ia_core/`, `chat/`
- **Tools**: [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)
- **Flujo completo**: [FLUJO_EJECUCION_CHAT.md](FLUJO_EJECUCION_CHAT.md)
- **Configuración**: [CONFIGURACION_AGENTE.md](CONFIGURACION_AGENTE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

**Versión**: 3.7.0
**Última actualización**: 2025-01-19
**Features destacadas**: Review Loop automático, Playwright Interactive Browser, 16 tools

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
