# 🏗️ Arquitectura del Sistema TenderAI v3.0

**Sistema de Function Calling Multi-Proveedor para Análisis de Licitaciones**

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Datos](#flujo-de-datos)
5. [Proveedores LLM](#proveedores-llm)
6. [Sistema de Tools](#sistema-de-tools)
7. [Base de Datos](#base-de-datos)

---

## 🎯 Visión General

TenderAI es una plataforma Django que utiliza **Function Calling** para permitir que los LLMs interactúen dinámicamente con datos de licitaciones públicas mediante **9 tools especializadas**.

### Características Clave

- ✅ **3 proveedores LLM**: Ollama (local), OpenAI, Google Gemini
- ✅ **9 tools especializadas**: Búsqueda, filtrado, análisis, comparación
- ✅ **Decisión automática**: LLM decide qué tools usar y cuándo
- ✅ **Iteración inteligente**: Hasta 5 pasos para consultas complejas
- ✅ **ChromaDB**: Búsqueda vectorial semántica
- ✅ **Django ORM**: Consultas SQL eficientes

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
│  │  - Maneja historial de conversación                       │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────┬│─────────────────────────────────────┘
                            ││
            ┌───────────────┘└───────────────┐
            ↓                                 ↓
┌─────────────────────────┐     ┌─────────────────────────┐
│   AGENT_IA_CORE         │     │   DJANGO ORM            │
│                         │     │                         │
│  FunctionCallingAgent   │────→│  Tender Model           │
│  ToolRegistry           │     │  CompanyProfile         │
│  9 Tools                │     │  ChatMessage            │
│  SchemaConverter        │     │  User                   │
└───────────┬─────────────┘     └─────────────────────────┘
            │
            ├──→ Ollama (localhost:11434)
            ├──→ OpenAI API
            └──→ Google Gemini API
```

---

## 🧩 Componentes Principales

### 1. FunctionCallingAgent

**Ubicación**: `agent_ia_core/agent_function_calling.py`

**Responsabilidades**:
- Coordinar la ejecución de tools
- Gestionar iteraciones (máximo 5)
- Comunicarse con diferentes proveedores LLM
- Mantener historial de conversación

**Métodos clave**:
```python
class FunctionCallingAgent:
    def __init__(self, llm_provider, llm_model, llm_api_key, retriever):
        # Inicializa LLM según proveedor
        self.llm = self._create_llm()
        self.tool_registry = ToolRegistry(retriever, db_session)

    def query(self, question, conversation_history):
        # Loop de function calling (máx 5 iteraciones)
        # 1. LLM decide tools
        # 2. Ejecutar tools
        # 3. LLM procesa resultados
        # 4. Repetir o retornar respuesta

    def _call_ollama_with_tools(self, messages):
        # Llamada nativa a Ollama con tools

    def _call_openai_with_tools(self, messages):
        # Llamada a OpenAI via LangChain

    def _call_gemini_with_tools(self, messages):
        # Llamada a Gemini via LangChain
```

### 2. ToolRegistry

**Ubicación**: `agent_ia_core/tools/registry.py`

**Responsabilidades**:
- Registrar las 9 tools disponibles
- Convertir schemas al formato del proveedor
- Ejecutar tool calls

**Métodos clave**:
```python
class ToolRegistry:
    def __init__(self, retriever, db_session):
        self.tools = {}
        self._register_all_tools()

    def get_ollama_tools(self):
        # Schemas en formato Ollama

    def get_openai_tools(self):
        # Schemas en formato OpenAI

    def get_gemini_tools(self):
        # Schemas en formato Gemini

    def execute_tool_calls(self, tool_calls):
        # Ejecuta múltiples tools en paralelo
```

### 3. Tools (9 especializadas)

**Ubicación**: `agent_ia_core/tools/`

**Búsqueda** (`search_tools.py`):
1. **SearchTendersTool**: Búsqueda vectorial con ChromaDB
2. **FindByBudgetTool**: Filtrado por presupuesto (Django ORM)
3. **FindByDeadlineTool**: Filtrado por fecha límite
4. **FindByCPVTool**: Filtrado por sector (ChromaDB)
5. **FindByLocationTool**: Filtrado geográfico (ChromaDB)

**Información** (`tender_tools.py`):
6. **GetTenderDetailsTool**: Detalles completos (Django ORM)
7. **GetTenderXMLTool**: Obtener XML completo (FileSystem)

**Análisis** (`search_tools.py` y `tender_tools.py`):
8. **GetStatisticsTool**: Estadísticas agregadas (Django Aggregate)
9. **CompareTendersTool**: Comparación lado a lado

**Cada tool implementa**:
```python
class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        # Lógica de ejecución

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        # Schema en formato JSON Schema
```

### 4. SchemaConverter

**Ubicación**: `agent_ia_core/tools/schema_converters.py`

**Responsabilidad**: Convertir schemas entre formatos de proveedores

**Conversiones soportadas**:
- **Ollama**: Formato OpenAI compatible
- **OpenAI**: Formato estándar OpenAI Function Calling
- **Gemini**: Tipos en MAYÚSCULAS (STRING, INTEGER, etc.)

```python
class SchemaConverter:
    @staticmethod
    def to_openai_format(base_schema):
        # JSON Schema → OpenAI format

    @staticmethod
    def to_gemini_format(base_schema):
        # JSON Schema → Gemini format (tipos en MAYÚSCULAS)

    @staticmethod
    def to_ollama_format(base_schema):
        # JSON Schema → Ollama format
```

### 5. ChatAgentService

**Ubicación**: `chat/services.py`

**Responsabilidad**: Integración entre Django y agent_ia_core

```python
class ChatAgentService:
    def __init__(self, user, use_function_calling=None):
        self.user = user
        self.provider = user.llm_provider  # 'ollama', 'openai', 'google'
        self.use_function_calling = use_function_calling

    def _create_function_calling_agent(self):
        # Crear retriever
        retriever = create_retriever(provider=self.provider)

        # Determinar modelo según proveedor
        if self.provider == 'ollama':
            model = user.ollama_model
        elif self.provider == 'openai':
            model = 'gpt-4o-mini'
        elif self.provider == 'google':
            model = 'gemini-2.0-flash-exp'

        # Crear agente
        agent = FunctionCallingAgent(
            llm_provider=self.provider,
            llm_model=model,
            llm_api_key=api_key,
            retriever=retriever
        )
        return agent

    def query(self, question, conversation_history):
        agent = self._get_agent()
        return agent.query(question, conversation_history)
```

### 6. Retriever (ChromaDB)

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
        # Búsqueda por similitud con filtros opcionales
        results = self.vectorstore.similarity_search_with_score(
            query, k=k, filter=filters
        )
        return self._format_results(results)
```

---

## 🔄 Flujo de Datos

### Flujo Completo: Usuario hace pregunta

```
1. FRONTEND
   Usuario escribe: "Busca licitaciones de IT con presupuesto > 50k"
   → JavaScript envía AJAX POST a /chat/<session_id>/message/

2. DJANGO VIEWS
   ChatMessageCreateView recibe request
   → Guarda mensaje del usuario en DB
   → Llama a ChatAgentService.query()

3. CHATAGENTSERVICE
   → Lee proveedor del usuario (ollama/openai/google)
   → Crea o reutiliza FunctionCallingAgent
   → Convierte historial a formato estándar
   → Llama a agent.query(question, history)

4. FUNCTIONCALLINGAGENT
   ITERACIÓN 1:
   → Prepara mensajes para LLM
   → Obtiene tools en formato del proveedor (via ToolRegistry)
   → Llama a _call_ollama_with_tools() / _call_openai_with_tools() / etc.

   LLM RESPONDE:
   → "Voy a usar find_by_cpv('IT') y find_by_budget(min_budget=50000)"

   → ToolRegistry.execute_tool_calls([
       {function: {name: 'find_by_cpv', arguments: {cpv_code: '72'}}},
       {function: {name: 'find_by_budget', arguments: {min_budget: 50000}}}
     ])

5. TOOLREGISTRY
   → Obtiene tools: find_by_cpv, find_by_budget
   → Ejecuta ambas en paralelo

   find_by_cpv:
   → Usa HybridRetriever (ChromaDB)
   → Filtra por CPV = 72
   → Retorna 10 licitaciones

   find_by_budget:
   → Usa Django ORM: Tender.objects.filter(budget_amount__gte=50000)
   → Retorna 8 licitaciones

   → Retorna resultados a FunctionCallingAgent

6. FUNCTIONCALLINGAGENT
   ITERACIÓN 2:
   → Añade resultados al historial
   → Vuelve a llamar al LLM con los datos

   LLM GENERA RESPUESTA FINAL:
   → "Encontré 3 licitaciones de IT con presupuesto mayor a 50,000 EUR:
      1. Desarrollo ERP - 150,000 EUR
      2. Migración cloud - 85,000 EUR
      3. Consultoría IT - 65,000 EUR"

   → No hay tool_calls, es respuesta final
   → Retorna respuesta a ChatAgentService

7. CHATAGENTSERVICE
   → Recibe respuesta
   → Extrae documentos usados
   → Retorna a Django Views

8. DJANGO VIEWS
   → Guarda respuesta del asistente en DB
   → Retorna JSON a frontend

9. FRONTEND
   → JavaScript recibe JSON
   → Renderiza mensaje del asistente
   → Muestra metadata (tools usadas, iteraciones)
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

tool_calls = response['message'].get('tool_calls', [])
```

**Ventajas**:
- 🆓 Gratis
- 🔒 100% local (privacidad)
- ⚡ Rápido (sin latencia de red)

**Desventajas**:
- 💻 Requiere recursos (16GB+ RAM)
- 🎯 Calidad depende del modelo local

### OpenAI (Cloud)

**Comunicación**:
```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

llm = ChatOpenAI(model='gpt-4o-mini', api_key=api_key)
llm_with_tools = llm.bind_tools(tool_registry.get_openai_tools())
response = llm_with_tools.invoke(messages)

tool_calls = response.tool_calls
```

**Ventajas**:
- 🎯 Alta calidad
- ⚡ Rápido
- 📊 Mejores resultados en consultas complejas

**Desventajas**:
- 💰 Costo por token
- ☁️ Datos en cloud (privacidad)
- 🌐 Requiere internet

### Google Gemini (Cloud)

**Comunicación**:
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=api_key)
llm_with_tools = llm.bind_tools(tool_registry.get_gemini_tools())
response = llm_with_tools.invoke(messages)

tool_calls = response.tool_calls
```

**Ventajas**:
- 💰 Más económico que OpenAI
- ⚡ Muy rápido
- 🎯 Buena calidad

**Desventajas**:
- 💰 Costo por token (menor que OpenAI)
- ☁️ Datos en cloud
- 🌐 Requiere internet

---

## 🛠️ Sistema de Tools

### Categorías

#### 🔍 Búsqueda (5 tools)

**Usan ChromaDB** (vectorial):
- `search_tenders`: Búsqueda semántica general
- `find_by_cpv`: Filtrado por sector (CPV codes)
- `find_by_location`: Filtrado geográfico (NUTS codes)

**Usan Django ORM** (SQL):
- `find_by_budget`: Filtrado por presupuesto
- `find_by_deadline`: Filtrado por fecha límite

#### 📄 Información (2 tools)

**Usan Django ORM**:
- `get_tender_details`: Detalles completos de una licitación
- `get_tender_xml`: Obtener XML completo del filesystem

#### 📊 Análisis (2 tools)

**Usan Django ORM + Aggregates**:
- `get_statistics`: Estadísticas agregadas (Count, Avg, Sum, Min, Max)
- `compare_tenders`: Comparación lado a lado de 2-5 licitaciones

### Decisión del LLM

El LLM decide automáticamente qué tools usar según la query:

| Query | Tools Usadas | Razón |
|-------|-------------|-------|
| "Busca licitaciones de IT" | `search_tenders` + `find_by_cpv` | Búsqueda semántica + filtro por sector |
| "Licitaciones > 50k euros" | `find_by_budget` | Filtro directo por presupuesto |
| "Estadísticas generales" | `get_statistics` | Análisis agregado |
| "Compara X e Y" | `get_tender_details` (x2) + `compare_tenders` | Obtiene detalles y compara |

---

## 💾 Base de Datos

### Modelos Django

#### User (authentication/models.py)
```python
class User(AbstractUser):
    email = EmailField(unique=True)
    llm_provider = CharField(max_length=50)  # 'ollama', 'openai', 'google'
    llm_api_key = TextField(blank=True)
    ollama_model = CharField(max_length=100)
    use_function_calling = BooleanField(default=False)
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
    source_path = CharField(max_length=500, blank=True)  # Path al XML
    # ... más campos
```

#### ChatSession (chat/models.py)
```python
class ChatSession(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    title = CharField(max_length=200)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_archived = BooleanField(default=False)
```

#### ChatMessage (chat/models.py)
```python
class ChatMessage(Model):
    session = ForeignKey(ChatSession, on_delete=CASCADE)
    role = CharField(max_length=20)  # 'user', 'assistant'
    content = TextField()
    timestamp = DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict, blank=True)  # tools_used, iterations, etc.
```

### ChromaDB

**Colección**: `eforms_chunks`
**Documentos**: 235+ chunks de 37 licitaciones

**Metadata por documento**:
```python
{
    'ojs_notice_id': '123456-2024',
    'section': 'object_description',  # o 'cpv_codes', 'nuts_regions', etc.
    'title': 'Desarrollo de software',
    'buyer_name': 'Ministerio',
    'cpv_codes': ['72000000'],
    'nuts_regions': ['ES300'],
    'budget_amount': 150000.0,
    'tender_deadline_date': '2024-03-20'
}
```

**Filtros soportados**:
- `cpv_codes`: Lista de códigos CPV
- `nuts_regions`: Lista de códigos NUTS
- `budget_amount`: Rango de presupuesto
- `tender_deadline_date`: Rango de fechas

---

## 📊 Métricas de Rendimiento

### Latencia Promedio

| Operación | Ollama (local) | OpenAI (API) | Gemini (API) |
|-----------|----------------|--------------|--------------|
| **Tool simple** (search) | 150-300ms | 200-500ms | 150-400ms |
| **Tool compleja** (compare) | 300-600ms | 400-800ms | 300-700ms |
| **Iteración completa** | 500-1000ms | 800-1500ms | 600-1200ms |
| **Query multi-tool** | 1-2s | 1.5-3s | 1-2.5s |

### Consumo de Recursos

| Proveedor | RAM | CPU | Disco | Red |
|-----------|-----|-----|-------|-----|
| **Ollama** | 8-16GB | Alto | 5-10GB (modelo) | No |
| **OpenAI** | < 500MB | Bajo | Mínimo | Sí |
| **Gemini** | < 500MB | Bajo | Mínimo | Sí |

---

## 🔐 Seguridad

### API Keys
- Almacenadas por usuario en DB (encriptadas en producción)
- No compartidas entre usuarios
- Validadas antes de cada llamada

### Datos
- Ollama: 100% local, nada sale de la máquina
- OpenAI/Gemini: Solo query y contexto necesario, no datos sensibles

### Rate Limiting
- Por usuario (no implementado aún, roadmap)
- Por proveedor (límites de API)

---

## 🔗 Referencias

- **Código fuente**: `agent_ia_core/`
- **Tools**: [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)
- **Configuración**: [CONFIGURACION_AGENTE.md](CONFIGURACION_AGENTE.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
