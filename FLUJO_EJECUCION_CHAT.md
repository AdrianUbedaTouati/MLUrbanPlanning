# 🔄 Flujo Completo de Ejecución del Chat - TenderAI

**Documento técnico:** Explica paso a paso TODO lo que sucede cuando el usuario envía un mensaje en el chat, incluyendo qué se envía al LLM en cada momento.

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Flujo Paso a Paso](#flujo-paso-a-paso)
3. [Mensajes Enviados al LLM](#mensajes-enviados-al-llm)
4. [Ejemplos Reales](#ejemplos-reales)
5. [Diagrama de Flujo](#diagrama-de-flujo)

---

## Visión General

```
Usuario escribe mensaje → Django View → Chat Service → Agent Graph → LLM (1-3 veces) → Respuesta
                                                           ↓
                                                      ChromaDB (si necesita docs)
```

**Llamadas al LLM:**
- **Mínimo:** 1 llamada (mensaje directo sin documentos)
- **Normal:** 2 llamadas (routing + respuesta)
- **Con grading:** 2-8 llamadas (routing + grading por documento + respuesta)

---

## Flujo Paso a Paso

### 🎯 PASO 1: Usuario Envía Mensaje

**Archivo:** `chat/views.py` → `ChatMessageCreateView.post()`

**Líneas:** 61-86

```python
# Usuario escribe: "cual es la licitacion con mas dinero"
user_message_content = request.POST.get('message', '').strip()

# Se crea el mensaje en BD
user_message = ChatMessage.objects.create(
    session=session,
    role='user',
    content=user_message_content  # "cual es la licitacion con mas dinero"
)
```

**Logs en consola:**
```
======================================================================
[CHAT REQUEST] Usuario: pepe2012 (OLLAMA)
[CHAT REQUEST] Sesión ID: 42 | Título: Consulta licitaciones
[CHAT REQUEST] Mensaje: cual es la licitacion con mas dinero
======================================================================
```

---

### 🎯 PASO 2: Preparar Historial Conversacional

**Archivo:** `chat/views.py` → líneas 98-120

```python
# Obtener mensajes anteriores de la sesión
previous_messages = session.messages.filter(
    created_at__lt=user_message.created_at
).order_by('created_at')

# Convertir a formato para el agente
conversation_history = []
for msg in previous_messages:
    conversation_history.append({
        'role': msg.role,  # 'user' o 'assistant'
        'content': msg.content
    })
```

**Ejemplo de historial:**
```python
[
    {'role': 'user', 'content': 'hola'},
    {'role': 'assistant', 'content': '¡Hola! ¿En qué puedo ayudarte?'},
    {'role': 'user', 'content': 'busca licitaciones de software'},
    {'role': 'assistant', 'content': 'He encontrado 6 licitaciones...'}
]
```

---

### 🎯 PASO 3: Crear ChatAgentService

**Archivo:** `chat/services.py` → `ChatAgentService.__init__()`

**Líneas:** 28-75

```python
chat_service = ChatAgentService(request.user)

# Lee configuración del usuario
self.provider = user.llm_provider  # "ollama"
self.model = user.ollama_model  # "qwen2.5:7b"
self.embedding_model = user.ollama_embedding_model  # "nomic-embed-text"
self.api_key = user.llm_api_key  # None para Ollama
```

**Logs en consola:**
```
[SERVICE] Inicializando process_message...
[SERVICE] Proveedor: OLLAMA
[SERVICE] Modelo LLM: qwen2.5:7b
[SERVICE] Modelo Embeddings: nomic-embed-text:latest
```

---

### 🎯 PASO 4: Crear Agente RAG

**Archivo:** `chat/services.py` → `_get_agent()`

**Líneas:** 82-160

```python
# Se crea el agente con:
agent = RAGAgent(
    llm_provider=self.provider,  # "ollama"
    llm_model=self.model,  # "qwen2.5:7b"
    vectorstore=vectorstore,  # Conexión a ChromaDB
    use_grading=self.user.use_grading,  # True/False
    use_verification=self.user.use_verification  # True/False
)
```

**Componentes inicializados:**

1. **LLM (Ollama):**
```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.3,  # Desde .env
    num_ctx=2048,  # Contexto de tokens desde .env
    base_url="http://localhost:11434"
)
```

2. **Retriever (ChromaDB):**
```python
retriever = vectorstore.as_retriever(
    search_kwargs={'k': 6}  # Recuperar 6 documentos
)
```

**Logs en consola:**
```
[SERVICE] Creando agente RAG...
INFO:agent_ia_core.agent_graph:Inicializando LLM: ollama - qwen2.5:7b
INFO:agent_ia_core.agent_graph:Inicializando Ollama local con modelo: qwen2.5:7b
INFO:index_build:Cargando índice existente desde data/index/chroma
INFO:index_build:✓ Índice cargado: 235 documentos
[SERVICE] ✓ Agente creado correctamente
```

---

### 🎯 PASO 5: Ejecutar Query en el Agente

**Archivo:** `chat/services.py` → `process_message()`

**Líneas:** 252-284

```python
# Pasar mensaje PURO (sin historial concatenado) + historial separado
result = agent.query(
    question=enriched_message,  # "cual es la licitacion con mas dinero"
    conversation_history=formatted_history  # [{role, content}, ...]
)
```

**El agente recibe:**
```python
{
    "question": "cual es la licitacion con mas dinero",
    "conversation_history": [
        {'role': 'user', 'content': 'hola'},
        {'role': 'assistant', 'content': '¡Hola! ¿En qué puedo ayudarte?'}
    ]
}
```

**Logs en consola:**
```
[SERVICE] Ejecutando query en el agente...
[SERVICE] Mensaje puro (para routing): cual es la licitacion con mas dinero...
[SERVICE] Historial: 2 mensajes
```

---

### 🎯 PASO 6: Iniciar Graph State

**Archivo:** `agent_ia_core/agent_graph.py` → `query()`

**Líneas:** 529-558

```python
initial_state = {
    "question": "cual es la licitacion con mas dinero",  # Solo pregunta actual
    "messages": [],  # Vacío por ahora
    "documents": [],  # Se llenará si busca docs
    "relevant_documents": [],  # Docs después de grading
    "answer": "",  # Se llenará al final
    "route": "",  # "vectorstore" o "general"
    "verified_fields": [],  # Para verificación XML
    "iteration": 0,
    "conversation_history": [  # Historial separado
        {'role': 'user', 'content': 'hola'},
        {'role': 'assistant', 'content': '¡Hola! ¿En qué puedo ayudarte?'}
    ]
}
```

**Logs en consola:**
```
INFO:agent_ia_core.agent_graph:
============================================================
INFO:agent_ia_core.agent_graph:CONSULTA: cual es la licitacion con mas dinero
INFO:agent_ia_core.agent_graph:HISTORIAL: 2 mensajes previos
INFO:agent_ia_core.agent_graph:
============================================================
```

---

## 🤖 LLAMADAS AL LLM

### 📞 LLAMADA #1: ROUTING (Clasificación)

**Archivo:** `agent_ia_core/agent_graph.py` → `_route_node()`

**Líneas:** 262-320

**Propósito:** Decidir si necesita buscar documentos o es conversación general.

#### Prompt enviado al LLM:

**SYSTEM MESSAGE:**
```
Eres un clasificador de consultas para un sistema de licitaciones públicas.

Tu trabajo es decidir si el usuario necesita buscar en la base de datos de licitaciones.

**IMPORTANTE: Analiza el CONTEXTO COMPLETO de la conversación, no solo el mensaje aislado.**

Categorías:
1) "vectorstore" - El usuario pregunta por licitaciones/ofertas/contratos ESPECÍFICOS que están en la base de datos
   Ejemplos:
   - "cual es la mejor licitación en software"
   - "busca ofertas para desarrollo web"
   - "muéstrame contratos disponibles"
   - "qué licitaciones hay en construcción"
   - "propuestas interesantes para mi empresa"

   **CLAVE:** Si la conversación ya está hablando de licitaciones específicas, preguntas como
   "cuánto dinero podría ganar", "cuál es el presupuesto", "cuándo es el plazo" también necesitan vectorstore.

2) "general" - Conversación general, saludos, o preguntas conceptuales que NO requieren buscar en documentos
   Ejemplos:
   - "hola, qué tal"
   - "qué es una licitación pública" (concepto general)
   - "cómo funciona el proceso de licitación" (explicación)
   - "gracias por la ayuda"

REGLAS CRÍTICAS:
- Si el usuario pregunta por licitaciones/ofertas/contratos CONCRETOS que podrían estar en la base de datos → vectorstore
- Si la conversación YA ESTÁ hablando de licitaciones específicas y el usuario hace preguntas de seguimiento → vectorstore
- Si es pregunta conceptual, saludo, o explicación sin contexto de licitaciones específicas → general

Responde SOLO con la categoría: "vectorstore" o "general" (sin explicaciones).
```

**HUMAN MESSAGE:**
```
Contexto de la conversación:
Usuario: hola...
Asistente: ¡Hola! ¿En qué puedo ayudarte?...

---

Mensaje actual del usuario:
"cual es la licitacion con mas dinero"

Considerando el CONTEXTO COMPLETO de la conversación, ¿necesita buscar en la base de datos de licitaciones?
Categoría (vectorstore o general):
```

#### Respuesta del LLM:
```
vectorstore
```

**HTTP Request a Ollama:**
```http
POST http://localhost:11434/api/chat
{
  "model": "qwen2.5:7b",
  "messages": [
    {"role": "system", "content": "Eres un clasificador de consultas..."},
    {"role": "user", "content": "Contexto de la conversación:\nUsuario: hola...\n\n---\n\nMensaje actual del usuario:\n\"cual es la licitacion con mas dinero\"\n\nCategoría (vectorstore o general):"}
  ],
  "temperature": 0.3,
  "stream": false
}
```

**Logs en consola:**
```
[ROUTE] Clasificando mensaje CON contexto: cual es la licitacion con mas dinero
[ROUTE] Historial disponible: 2 mensajes
INFO:httpx:HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
[ROUTE] LLM clasificó como DOCUMENTOS (respuesta: vectorstore)
[ROUTE] Ruta final decidida: vectorstore
```

**Resultado:** `state["route"] = "vectorstore"`

---

### 📞 LLAMADA #2: RETRIEVE (Búsqueda de Documentos)

**Archivo:** `agent_ia_core/agent_graph.py` → `_retrieve_node()`

**Líneas:** 322-365

**Propósito:** Buscar documentos relevantes en ChromaDB.

#### Proceso:

1. **Generar embedding del mensaje:**
```python
# Se convierte el mensaje a vector con Ollama embeddings
query_embedding = embeddings.embed_query("cual es la licitacion con mas dinero")
# Resultado: [0.123, -0.456, 0.789, ...] (vector de 768 dimensiones)
```

**HTTP Request a Ollama:**
```http
POST http://localhost:11434/api/embed
{
  "model": "nomic-embed-text",
  "input": "cual es la licitacion con mas dinero"
}
```

2. **Buscar en ChromaDB:**
```python
# ChromaDB busca los 6 documentos más similares
results = vectorstore.similarity_search(
    query="cual es la licitacion con mas dinero",
    k=6
)
```

#### Documentos recuperados (ejemplo):

```python
[
    Document(
        page_content="Presupuesto estimado: 961,200.00 EUR",
        metadata={
            'ojs_notice_id': '00668461-2025',
            'section': 'budget',
            'buyer_name': 'Fundación Estatal',
            'cpv_codes': '72267100',
            'budget_eur': '961200.0',  # ← AHORA DISPONIBLE
            'publication_date': '2025-09-15'
        }
    ),
    Document(
        page_content="Presupuesto estimado: 750,000.00 EUR",
        metadata={
            'ojs_notice_id': '00677736-2025',
            'section': 'budget',
            'buyer_name': 'Autoridad Portuaria',
            'cpv_codes': '72267100,72212000',
            'budget_eur': '750000.0',
            'publication_date': '2025-09-20'
        }
    ),
    # ... 4 documentos más
]
```

**Logs en consola:**
```
[RETRIEVE] Buscando documentos para: cual es la licitacion con mas dinero
INFO:retriever:Recuperando documentos: query='cual es la licitacion con mas dinero', k=6, filters={}
INFO:httpx:HTTP Request: POST http://localhost:11434/api/embed "HTTP/1.1 200 OK"
INFO:retriever:Recuperados 6 documentos (de 18 candidatos)
[RETRIEVE] Recuperados 6 documentos
```

**Resultado:** `state["documents"] = [doc1, doc2, doc3, doc4, doc5, doc6]`

---

### 📞 LLAMADAS #3-8: GRADING (Opcional - si use_grading=True)

**Archivo:** `agent_ia_core/agent_graph.py` → `_grade_node()`

**Líneas:** 367-407

**Propósito:** Evaluar si cada documento es realmente relevante.

**Se hace UNA llamada al LLM POR CADA DOCUMENTO (6 llamadas en este caso).**

#### Prompt por documento:

**SYSTEM MESSAGE:**
```
Eres un evaluador de relevancia de documentos.

Tu tarea es determinar si un documento recuperado es relevante para responder la pregunta del usuario.

Criterios de relevancia:
- El documento contiene información directamente relacionada con la pregunta
- El documento puede ayudar a responder total o parcialmente la pregunta
- El contenido es específico y no genérico

Si NO es relevante, identifica internamente una razón breve (para logging).
Responde SOLO con "yes" o "no".
```

**HUMAN MESSAGE (ejemplo para documento 1):**
```
Pregunta: cual es la licitacion con mas dinero

Documento:
ID: 00668461-2025
Sección: budget
Contenido: Presupuesto estimado: 961,200.00 EUR

¿Es este documento relevante para responder la pregunta?
Responde solo "yes" o "no":
```

#### Respuesta del LLM:
```
yes
```

**HTTP Requests (6 llamadas):**
```http
POST http://localhost:11434/api/chat  # Doc 1 → yes
POST http://localhost:11434/api/chat  # Doc 2 → yes
POST http://localhost:11434/api/chat  # Doc 3 → yes
POST http://localhost:11434/api/chat  # Doc 4 → no
POST http://localhost:11434/api/chat  # Doc 5 → yes
POST http://localhost:11434/api/chat  # Doc 6 → yes
```

**Logs en consola:**
```
[GRADE] Evaluando relevancia de 6 documentos
[GRADE] Doc 1/6: yes - Presupuesto estimado: 961,200.00 EUR
[GRADE] Doc 2/6: yes - Presupuesto estimado: 750,000.00 EUR
[GRADE] Doc 3/6: yes - Presupuesto estimado: 500,000.00 EUR
[GRADE] Doc 4/6: no - Requisitos de elegibilidad según...
[GRADE] Doc 5/6: yes - Presupuesto estimado: 373,831.76 EUR
[GRADE] Doc 6/6: yes - Presupuesto estimado: 300,000.00 EUR
[GRADE] Documentos relevantes: 5/6
```

**Resultado:** `state["relevant_documents"] = [doc1, doc2, doc3, doc5, doc6]` (5 docs)

---

### 📞 LLAMADA #9: ANSWER (Generación de Respuesta)

**Archivo:** `agent_ia_core/agent_graph.py` → `_answer_node()`

**Líneas:** 409-491

**Propósito:** Generar la respuesta final usando documentos + historial.

#### Construcción del prompt:

**Paso 1: Construir contexto con historial**
```python
def build_context_with_history(current_question: str) -> str:
    if not conversation_history:
        return current_question

    history_text = "Historial de la conversación:\n"
    for msg in conversation_history:
        role_label = "Usuario" if msg['role'] == 'user' else "Asistente"
        history_text += f"{role_label}: {msg['content']}\n"

    return f"{history_text}\n---\n\nPregunta actual del usuario:\n{current_question}"
```

**Resultado:**
```
Historial de la conversación:
Usuario: hola
Asistente: ¡Hola! ¿En qué puedo ayudarte?

---

Pregunta actual del usuario:
cual es la licitacion con mas dinero
```

**Paso 2: Formatear documentos**

Usando `create_answer_prompt()` de `agent_ia_core/prompts.py`:

```python
context_text = """
[Documento 1]
ID: 00668461-2025
Sección: budget
Comprador: Fundación Estatal
CPV: 72267100
Presupuesto: 961200.0 EUR
Publicado: 2025-09-15
Contenido:
Presupuesto estimado: 961,200.00 EUR

---

[Documento 2]
ID: 00677736-2025
Sección: budget
Comprador: Autoridad Portuaria
CPV: 72267100,72212000
Presupuesto: 750000.0 EUR
Publicado: 2025-09-20
Contenido:
Presupuesto estimado: 750,000.00 EUR

---

[Documento 3]
ID: 00670256-2025
Sección: budget
Comprador: Ajuntament de València
CPV: 72267100,48000000
Presupuesto: 500000.0 EUR
Publicado: 2025-09-18
Contenido:
Presupuesto estimado: 500,000.00 EUR

---

[Documento 4]
ID: 00623257-2025
Sección: budget
Comprador: Consejo Insular de Aguas
CPV: 79341000,79341400
Presupuesto: 373831.76 EUR
Publicado: 2025-09-24
Contenido:
Presupuesto estimado: 373,831.76 EUR

---

[Documento 5]
ID: 00660806-2025
Sección: budget
Comprador: Ayuntamiento de El Sauzal
CPV: 72000000,48900000
Presupuesto: 300000.0 EUR
Publicado: 2025-09-22
Contenido:
Presupuesto estimado: 300,000.00 EUR
"""
```

#### Prompt completo enviado al LLM:

**SYSTEM MESSAGE:**
```
Eres un asistente conversacional natural y útil. Tu especialidad es ayudar con licitaciones públicas, pero puedes hablar de cualquier tema.

**Cómo eres:**
- Conversas de forma natural, como un humano amigable
- Respondes de manera clara y directa
- Te adaptas al tono del usuario (formal/informal)
- Eres útil y práctico

**Tu conocimiento:**
- Conoces sobre licitaciones públicas, TED (Tenders Electronic Daily), CPV, plazos, presupuestos
- Tienes acceso a documentos oficiales cuando hay consultas específicas

**Lo importante:**
- Cuando tengas documentos, úsalos para dar información precisa
- Cuando NO tengas documentos, responde natural basándote en tu conocimiento general
- Si algo no lo sabes o no está en los documentos, dilo honestamente
- Puedes usar Markdown para formatear (listas, **negritas**, tablas, etc.)

Responde de la forma más natural y útil posible. No te limites a fórmulas rígidas.
```

**HUMAN MESSAGE:**
```
Historial de la conversación:
Usuario: hola
Asistente: ¡Hola! ¿En qué puedo ayudarte?

---

Pregunta actual del usuario:
cual es la licitacion con mas dinero

---

Tienes acceso a estos documentos de licitaciones:

[Documento 1]
ID: 00668461-2025
Sección: budget
Comprador: Fundación Estatal
CPV: 72267100
Presupuesto: 961200.0 EUR
Publicado: 2025-09-15
Contenido:
Presupuesto estimado: 961,200.00 EUR

---

[Documento 2]
ID: 00677736-2025
Sección: budget
Comprador: Autoridad Portuaria
CPV: 72267100,72212000
Presupuesto: 750000.0 EUR
Publicado: 2025-09-20
Contenido:
Presupuesto estimado: 750,000.00 EUR

---

[Documento 3]
ID: 00670256-2025
Sección: budget
Comprador: Ajuntament de València
CPV: 72267100,48000000
Presupuesto: 500000.0 EUR
Publicado: 2025-09-18
Contenido:
Presupuesto estimado: 500,000.00 EUR

---

[Documento 4]
ID: 00623257-2025
Sección: budget
Comprador: Consejo Insular de Aguas
CPV: 79341000,79341400
Presupuesto: 373831.76 EUR
Publicado: 2025-09-24
Contenido:
Presupuesto estimado: 373,831.76 EUR

---

[Documento 5]
ID: 00660806-2025
Sección: budget
Comprador: Ayuntamiento de El Sauzal
CPV: 72000000,48900000
Presupuesto: 300000.0 EUR
Publicado: 2025-09-22
Contenido:
Presupuesto estimado: 300,000.00 EUR

---

El usuario pregunta: cual es la licitacion con mas dinero

Usa la información de los documentos para responder. Sé útil y claro. Si usas datos específicos de los documentos, cita la fuente con [ID | sección].

Respuesta:
```

#### Respuesta del LLM:

```
Basándome en los documentos proporcionados, la licitación con el presupuesto más alto es:

**Licitación 00668461-2025** [00668461-2025 | budget]
- **Comprador:** Fundación Estatal
- **Presupuesto:** 961,200.00 EUR
- **CPV:** 72267100
- **Fecha de publicación:** 2025-09-15

Esta es la licitación más grande en términos de presupuesto entre las disponibles.

Si necesitas más detalles sobre esta licitación o quieres explorar otras opciones, no dudes en preguntar.
```

**HTTP Request:**
```http
POST http://localhost:11434/api/chat
{
  "model": "qwen2.5:7b",
  "messages": [
    {
      "role": "system",
      "content": "Eres un asistente conversacional natural y útil..."
    },
    {
      "role": "user",
      "content": "Historial de la conversación:\nUsuario: hola\nAsistente: ¡Hola! ¿En qué puedo ayudarte?\n\n---\n\nPregunta actual del usuario:\ncual es la licitacion con mas dinero\n\n---\n\nTienes acceso a estos documentos de licitaciones:\n\n[Documento 1]\nID: 00668461-2025\n..."
    }
  ],
  "temperature": 0.3,
  "num_ctx": 2048,
  "stream": false
}
```

**Logs en consola:**
```
[ANSWER] Generando respuesta
[ANSWER] Usando historial de 2 mensajes para contexto
[ANSWER] Respuesta con 5 documentos
INFO:httpx:HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
[ANSWER] Respuesta generada (285 caracteres)
```

**Resultado:** `state["answer"] = "Basándome en los documentos proporcionados..."`

---

### 🎯 PASO 7: Guardar Respuesta en BD

**Archivo:** `chat/views.py` → líneas 130-160

```python
# Crear mensaje del asistente
assistant_message = ChatMessage.objects.create(
    session=session,
    role='assistant',
    content=response['content'],  # La respuesta del LLM
    metadata={
        'route': response['metadata'].get('route'),  # "vectorstore"
        'num_documents': response['metadata'].get('num_documents'),  # 5
        'total_tokens': response['metadata'].get('total_tokens'),  # 450
        'cost_eur': response['metadata'].get('cost_eur')  # 0.0000 (Ollama)
    }
)
```

**Logs en consola:**
```
[SERVICE] ✓ Query ejecutado correctamente
[SERVICE] ✓ Respuesta procesada: 285 caracteres
[SERVICE] Documentos recuperados: 5
[SERVICE] Tokens totales: 450 (in: 220, out: 230)
[SERVICE] Costo: €0.0000
```

---

### 🎯 PASO 8: Enviar Respuesta al Frontend

**Archivo:** `chat/views.py` → líneas 180-195

```python
return JsonResponse({
    'success': True,
    'message': {
        'id': assistant_message.id,
        'content': assistant_message.content,
        'created_at': assistant_message.created_at.isoformat(),
        'role': 'assistant',
        'metadata': assistant_message.metadata
    }
})
```

**JSON enviado al navegador:**
```json
{
  "success": true,
  "message": {
    "id": 1234,
    "content": "Basándome en los documentos proporcionados, la licitación con el presupuesto más alto es:\n\n**Licitación 00668461-2025**...",
    "created_at": "2025-01-19T14:30:45.123456",
    "role": "assistant",
    "metadata": {
      "route": "vectorstore",
      "num_documents": 5,
      "total_tokens": 450,
      "cost_eur": 0.0
    }
  }
}
```

---

## 📊 Resumen de Llamadas al LLM

Para la query: **"cual es la licitacion con mas dinero"** (con `use_grading=True`)

| # | Tipo | Propósito | Input Tokens | Output Tokens | Modelo |
|---|------|-----------|--------------|---------------|--------|
| 1 | Routing | Clasificar query | ~50 | ~5 | qwen2.5:7b |
| 2 | Embed | Generar vector de búsqueda | ~15 | 768 dim | nomic-embed-text |
| 3 | Grading | Evaluar doc 1 | ~30 | ~3 | qwen2.5:7b |
| 4 | Grading | Evaluar doc 2 | ~30 | ~3 | qwen2.5:7b |
| 5 | Grading | Evaluar doc 3 | ~30 | ~3 | qwen2.5:7b |
| 6 | Grading | Evaluar doc 4 | ~30 | ~3 | qwen2.5:7b |
| 7 | Grading | Evaluar doc 5 | ~30 | ~3 | qwen2.5:7b |
| 8 | Grading | Evaluar doc 6 | ~30 | ~3 | qwen2.5:7b |
| 9 | Answer | Generar respuesta | ~220 | ~230 | qwen2.5:7b |
| **TOTAL** | | | **~465** | **~256** | |

**Con `use_grading=False`:** Solo 3 llamadas (routing, embed, answer) = ~285 tokens total

---

## 🔄 Diagrama de Flujo Visual

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUARIO ENVÍA MENSAJE                        │
│                "cual es la licitacion con mas dinero"            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1: Django View (chat/views.py)                            │
│  - Crear ChatMessage en BD                                       │
│  - Obtener historial de conversación                            │
│  - Logs: [CHAT REQUEST] Usuario, Sesión, Mensaje                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2: ChatAgentService (chat/services.py)                    │
│  - Leer config del usuario (provider, modelo, API key)          │
│  - Crear agente RAG con LLM + Retriever                         │
│  - Logs: [SERVICE] Proveedor, Modelo LLM, Modelo Embeddings     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 3: Iniciar Agent Graph (agent_ia_core/agent_graph.py)     │
│  - Crear initial_state con question + conversation_history      │
│  - Logs: [CONSULTA] Pregunta, [HISTORIAL] X mensajes            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  🤖 LLAMADA LLM #1: ROUTING                                      │
│                                                                  │
│  Input:                                                          │
│  - System: "Eres un clasificador de consultas..."               │
│  - Human: "Contexto:\nUsuario: hola\n...\n---\nMensaje actual:  │
│            cual es la licitacion con mas dinero"                │
│                                                                  │
│  Output: "vectorstore"                                           │
│                                                                  │
│  HTTP: POST localhost:11434/api/chat                             │
│  Logs: [ROUTE] Clasificó como DOCUMENTOS                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │  route=vectorstore │
                   └─────────┬─────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  🔍 LLAMADA #2: EMBED (Generar vector)                           │
│                                                                  │
│  Input: "cual es la licitacion con mas dinero"                  │
│  Output: [0.123, -0.456, 0.789, ...] (768 dimensiones)          │
│                                                                  │
│  HTTP: POST localhost:11434/api/embed                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  📚 BUSCAR EN CHROMADB                                           │
│  - Similarity search con vector                                 │
│  - Recuperar top 6 documentos                                   │
│  - Logs: [RETRIEVE] Recuperados 6 documentos                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │   use_grading=True?             │
            └────┬─────────────────────┬──────┘
                 │ YES                 │ NO
                 ▼                     │
┌────────────────────────────┐         │
│  🤖 LLAMADAS #3-8: GRADING │         │
│                            │         │
│  Por cada documento (6):   │         │
│  - System: "Evaluador..."  │         │
│  - Human: "Pregunta: ...   │         │
│           Documento: ...   │         │
│           ¿Relevante?"     │         │
│  - Output: "yes" o "no"    │         │
│                            │         │
│  HTTP: 6x POST /api/chat   │         │
│  Logs: [GRADE] 5/6 docs OK │         │
└────────────┬───────────────┘         │
             │                         │
             └─────────┬───────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  🤖 LLAMADA #9: ANSWER (Generar respuesta)                       │
│                                                                  │
│  Input:                                                          │
│  - System: "Eres un asistente conversacional natural..."        │
│  - Human: "Historial:\nUsuario: hola\nAsistente: ...\n---\n     │
│            Pregunta actual: cual es...\n---\n                   │
│            Documentos:\n[Documento 1]\nID: 00668461-2025\n      │
│            Presupuesto: 961200.0 EUR\n...\n[Documento 2]..."    │
│                                                                  │
│  Output: "Basándome en los documentos proporcionados, la        │
│           licitación con el presupuesto más alto es:\n          │
│           **Licitación 00668461-2025**..."                      │
│                                                                  │
│  HTTP: POST localhost:11434/api/chat                             │
│  Logs: [ANSWER] Respuesta generada (285 caracteres)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 4: Guardar en BD (chat/views.py)                          │
│  - Crear ChatMessage con role='assistant'                       │
│  - Guardar metadata (route, num_documents, tokens, cost)        │
│  - Logs: [SERVICE] ✓ Respuesta procesada                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 5: Enviar JSON al Frontend                                │
│  {                                                               │
│    "success": true,                                              │
│    "message": {                                                  │
│      "id": 1234,                                                 │
│      "content": "Basándome en los documentos...",               │
│      "role": "assistant",                                        │
│      "metadata": {                                               │
│        "route": "vectorstore",                                   │
│        "num_documents": 5,                                       │
│        "total_tokens": 450                                       │
│      }                                                            │
│    }                                                              │
│  }                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     USUARIO VE RESPUESTA                         │
│  "Basándome en los documentos proporcionados, la licitación con │
│   el presupuesto más alto es: **Licitación 00668461-2025**..."  │
│                                                                  │
│  5 documento(s) consultado(s)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Ejemplos Reales

### Ejemplo 1: Mensaje Simple (Sin Documentos)

**Input:** "hola"

**Llamadas al LLM:**
1. **Routing:** "general"
2. **Answer:** Respuesta directa sin docs

**Total:** 2 llamadas, ~80 tokens

---

### Ejemplo 2: Pregunta Específica (Con Documentos)

**Input:** "cual es la licitacion con mas dinero"

**Llamadas al LLM:**
1. **Routing:** "vectorstore"
2. **Embed:** Generar vector
3. **Grading x6:** Evaluar cada doc
4. **Answer:** Generar respuesta con docs

**Total:** 9 llamadas, ~465 tokens

---

### Ejemplo 3: Pregunta de Seguimiento (Contextual)

**Historial:**
- Usuario: "busca licitaciones de software"
- Asistente: "He encontrado 6 licitaciones..."

**Input:** "cuanto dinero podria ganar"

**Llamadas al LLM:**
1. **Routing CON CONTEXTO:** "vectorstore" (detecta continuación)
2. **Embed:** Generar vector
3. **Grading x6:** Evaluar cada doc
4. **Answer CON HISTORIAL:** Generar respuesta con contexto

**Total:** 9 llamadas, ~520 tokens (más largo por historial)

---

## ⚙️ Configuración (Variables de .env)

```bash
# LLM Settings
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
LLM_TEMPERATURE=0.3
OLLAMA_CONTEXT_LENGTH=2048
LLM_TIMEOUT=120

# Retrieval Settings
DEFAULT_K_RETRIEVE=6
MIN_SIMILARITY_SCORE=0.5

# Agent Features
USE_GRADING=True
USE_XML_VERIFICATION=False

# Conversation
MAX_CONVERSATION_HISTORY=10
```

---

## 🔍 Debugging

Para ver TODO el flujo en tiempo real, revisa los logs en la consola del servidor:

```bash
# Terminal donde corre: python manage.py runserver 8001

======================================================================
[CHAT REQUEST] Usuario: pepe2012 (OLLAMA)
[CHAT REQUEST] Sesión ID: 42 | Título: Consulta licitaciones
[CHAT REQUEST] Mensaje: cual es la licitacion con mas dinero
======================================================================
[SERVICE] Inicializando process_message...
[SERVICE] Proveedor: OLLAMA
[SERVICE] Modelo LLM: qwen2.5:7b
[SERVICE] Creando agente RAG...
INFO:agent_ia_core.agent_graph:CONSULTA: cual es la licitacion con mas dinero
[ROUTE] Clasificando mensaje CON contexto: cual es la licitacion con mas dinero
INFO:httpx:HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
[ROUTE] LLM clasificó como DOCUMENTOS (respuesta: vectorstore)
[RETRIEVE] Buscando documentos para: cual es la licitacion con mas dinero
INFO:httpx:HTTP Request: POST http://localhost:11434/api/embed "HTTP/1.1 200 OK"
INFO:retriever:Recuperados 6 documentos
[GRADE] Evaluando relevancia de 6 documentos
[GRADE] Documentos relevantes: 5/6
[ANSWER] Generando respuesta
INFO:httpx:HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 200 OK"
[ANSWER] Respuesta generada (285 caracteres)
[SERVICE] ✓ Respuesta procesada: 285 caracteres
[SERVICE] Documentos recuperados: 5
[SERVICE] Tokens totales: 450
```

---

**Fecha de creación:** 2025-01-19
**Versión del sistema:** v1.4.0
**Autor:** Claude Code Assistant
