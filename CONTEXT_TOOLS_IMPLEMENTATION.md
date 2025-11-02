# Implementación de Tools de Contexto

## 🎯 Objetivo

Cambiar la forma en que el agente accede a información de contexto (empresa y licitaciones), pasando de un **system prompt estático** a **herramientas dinámicas** que el agente puede llamar cuando las necesite.

## 📋 Resumen de Cambios

### Antes (System Prompt Estático)
- El contexto de empresa se añadía al system prompt **solo en el primer mensaje**
- El resumen de licitaciones se añadía al system prompt **solo en el primer mensaje**
- Problema: Si había historial previo, el contexto NO se cargaba
- Problema: El contexto consumía muchos tokens en cada mensaje

### Después (Tools Dinámicas)
- **2 nuevas herramientas** disponibles para el agente:
  - `get_company_info`: Obtiene información de la empresa del usuario
  - `get_tenders_summary`: Obtiene resumen de licitaciones disponibles
- El agente las llama **cuando las necesita**
- `get_tenders_summary` se llama **automáticamente** en el primer mensaje
- El contexto **siempre está disponible** mediante tools

## 🆕 Nuevas Tools Implementadas

### 1. `GetCompanyInfoTool`
**Ubicación**: `agent_ia_core/tools/context_tools.py`

**Descripción**: Obtiene información sobre la empresa del usuario del perfil de CompanyProfile.

**Sin parámetros** (consulta directa)

**Retorna**:
```python
{
    'success': True,
    'data': {
        'formatted_context': str,  # Texto formateado para el LLM
        'structured_data': {
            'company_name': str,
            'sector': str,
            'num_employees': int,
            'cpv_codes': List[str],
            'nuts_regions': List[str],
            'capabilities': str,
            'certifications': List[str],
            'min_budget': float,
            'max_budget': float,
            'geographic_scope': List[str]
        }
    }
}
```

**Cuándo se usa**:
- El usuario pregunta sobre su empresa
- El agente necesita información para dar recomendaciones personalizadas
- El usuario pide licitaciones "adecuadas para mi empresa"

### 2. `GetTendersSummaryTool`
**Ubicación**: `agent_ia_core/tools/context_tools.py`

**Descripción**: Obtiene un resumen de las licitaciones más recientes en la base de datos.

**Parámetros**:
- `limit` (opcional): Número máximo de licitaciones (1-50, default: 20)

**Retorna**:
```python
{
    'success': True,
    'data': {
        'formatted_summary': str,  # Texto formateado con lista de licitaciones
        'tenders_list': List[Dict],  # Datos estructurados de cada licitación
        'total_count': int
    }
}
```

**Cuándo se usa**:
- **Automáticamente en el primer mensaje** de cada conversación nueva
- El usuario pregunta qué licitaciones hay disponibles
- El agente necesita contexto general de las licitaciones

## 📝 Archivos Modificados

### 1. `agent_ia_core/tools/context_tools.py` (NUEVO)
**Qué hace**: Define las 2 nuevas tools (GetCompanyInfoTool, GetTendersSummaryTool)

**Clases**:
- `GetCompanyInfoTool`: Consulta CompanyProfile del usuario
- `GetTendersSummaryTool`: Consulta Tender model, devuelve últimas N licitaciones

### 2. `agent_ia_core/tools/registry.py`
**Cambios**:
- Añadido parámetro `user` al `__init__`
- Registro automático de tools de contexto si hay usuario
- Import de `context_tools`

**Antes**:
```python
def __init__(self, retriever, db_session=None):
    self.tools = {}
    self._register_all_tools()
```

**Después**:
```python
def __init__(self, retriever, db_session=None, user=None):
    self.user = user
    self.tools = {}
    self._register_all_tools()

def _register_all_tools(self):
    if self.user:
        self.tools['get_company_info'] = GetCompanyInfoTool(self.user)
        self.tools['get_tenders_summary'] = GetTendersSummaryTool(self.user)
```

### 3. `agent_ia_core/agent_function_calling.py`
**Cambios**:

1. **Añadido parámetro `user` al `__init__`**:
```python
def __init__(
    self,
    llm_provider: str,
    llm_model: str,
    llm_api_key: Optional[str],
    retriever,
    db_session=None,
    user=None,  # NUEVO
    max_iterations: int = 5,
    temperature: float = 0.3,
    company_context: str = "",  # DEPRECATED
    tenders_summary: str = ""   # DEPRECATED
):
```

2. **Registry inicializado con usuario**:
```python
self.tool_registry = ToolRegistry(retriever, db_session, user=user)
```

3. **Eliminado contexto del system prompt**:
   - Ya NO se añade `company_context` al system prompt
   - Ya NO se añade `tenders_summary` al system prompt
   - Se añaden instrucciones para usar las tools

4. **Llamada automática a `get_tenders_summary` en primer mensaje**:
```python
# En el primer mensaje, llamar automáticamente a get_tenders_summary
if is_first_message and self.user and 'get_tenders_summary' in self.tool_registry.tools:
    logger.info("[QUERY] Primer mensaje - Llamando automáticamente a get_tenders_summary...")
    summary_result = self.tool_registry.execute_tool('get_tenders_summary', limit=20)

    if summary_result.get('success'):
        # Añadir resultado como mensaje del sistema
        messages.append({
            'role': 'system',
            'content': f"CONTEXTO AUTOMÁTICO (resumen de licitaciones):\n\n{formatted_summary}"
        })
```

### 4. `chat/services.py`
**Cambios**:
- Pasar `user=self.user` al crear FunctionCallingAgent
- Actualizar mensajes de log

**Antes**:
```python
self._agent = FunctionCallingAgent(
    llm_provider=self.provider,
    llm_model=model,
    llm_api_key=api_key,
    retriever=retriever,
    db_session=None,
    company_context=self.company_context,
    tenders_summary=self.tenders_summary
)
```

**Después**:
```python
self._agent = FunctionCallingAgent(
    llm_provider=self.provider,
    llm_model=model,
    llm_api_key=api_key,
    retriever=retriever,
    db_session=None,
    user=self.user,  # NUEVO
    company_context=self.company_context,  # Deprecated
    tenders_summary=self.tenders_summary   # Deprecated
)
```

## 🔄 Flujo de Funcionamiento

### Caso 1: Primer Mensaje de Nueva Conversación

```
Usuario: "Hola, ¿qué licitaciones tenéis?"

1. ChatAgentService crea FunctionCallingAgent con user
2. ToolRegistry registra get_company_info y get_tenders_summary
3. Agent.query() detecta is_first_message = True
4. Agent llama AUTOMÁTICAMENTE a get_tenders_summary(limit=20)
5. Resultado se añade como mensaje del sistema
6. LLM recibe:
   - System prompt con instrucciones
   - Contexto automático con 20 licitaciones
   - Pregunta del usuario
7. LLM genera respuesta usando el contexto
```

### Caso 2: Usuario Pregunta por Su Empresa

```
Usuario: "¿Cómo se llama mi empresa?"

1. LLM recibe la pregunta
2. LLM decide llamar a get_company_info (sin parámetros)
3. ToolRegistry ejecuta GetCompanyInfoTool
4. Tool consulta CompanyProfile del usuario
5. Devuelve información formateada
6. LLM genera respuesta usando la información:
   "Tu empresa se llama Koralya, sois una empresa de consultoría..."
```

### Caso 3: Recomendaciones Personalizadas

```
Usuario: "Recomiéndame licitaciones adecuadas para mi empresa"

1. LLM analiza la pregunta
2. LLM decide llamar AMBAS tools:
   - get_company_info (para saber perfil de usuario)
   - search_tenders (para buscar licitaciones)
3. ToolRegistry ejecuta ambas
4. get_company_info devuelve: CPV codes, regiones NUTS, sector, etc.
5. search_tenders busca licitaciones relacionadas
6. LLM combina ambos resultados para dar recomendaciones personalizadas
```

## 🎯 Ventajas del Nuevo Sistema

### 1. **Contexto Siempre Disponible**
- ✅ No importa si es el primer mensaje o el mensaje 100
- ✅ El agente puede llamar a las tools en cualquier momento
- ✅ No depende del historial de conversación

### 2. **Ahorro de Tokens**
- ✅ Contexto NO se repite en cada mensaje
- ✅ Solo se carga cuando se necesita
- ✅ System prompt mucho más corto

### 3. **Flexibilidad**
- ✅ El agente decide cuándo necesita la información
- ✅ Puede llamar solo a `get_company_info` sin `get_tenders_summary`
- ✅ Puede re-llamar las tools si necesita actualizar datos

### 4. **Mejor Debugging**
- ✅ Logs claros de cuándo se llaman las tools
- ✅ Fácil ver qué información se consultó
- ✅ Metadata incluye qué tools se usaron

### 5. **Escalabilidad**
- ✅ Fácil añadir más tools de contexto
- ✅ Cada tool es independiente y testeable
- ✅ Sistema más modular

## 📊 Comparación de Tokens

### Antes (System Prompt con Contexto)

```
System Prompt: ~1500 tokens
- Instrucciones base: 500 tokens
- Contexto de empresa: 300 tokens
- Resumen 50 licitaciones: 700 tokens

Mensaje 1: 1500 (system) + 50 (user) = 1550 tokens
Mensaje 2: 1500 (system) + 100 (history) + 50 (user) = 1650 tokens
Mensaje 3: 1500 (system) + 200 (history) + 50 (user) = 1750 tokens
```

### Después (Tools Dinámicas)

```
System Prompt: ~300 tokens
- Instrucciones base: 250 tokens
- Instrucciones para tools: 50 tokens

Mensaje 1: 300 (system) + 50 (user) + 700 (tool result) = 1050 tokens (-500!)
Mensaje 2: 300 (system) + 100 (history) + 50 (user) = 450 tokens (-1200!)
Mensaje 3: 300 (system) + 200 (history) + 50 (user) = 550 tokens (-1200!)
```

**Ahorro total en 3 mensajes**: ~2900 tokens (~60% de reducción)

## 🧪 Cómo Probar

### Test 1: Información de Empresa
```
1. Crear nueva sesión de chat
2. Enviar: "¿Cómo se llama mi empresa y a qué me dedico?"
3. Verificar en logs del servidor:
   - "[TOOL] Ejecutando get_company_info..."
   - "[TOOL] get_company_info completado exitosamente"
4. Verificar respuesta incluye nombre y descripción de Koralya
```

### Test 2: Resumen Automático de Licitaciones
```
1. Crear nueva sesión de chat
2. Enviar: "Hola"
3. Verificar en logs del servidor:
   - "[QUERY] Primer mensaje - Llamando automáticamente a get_tenders_summary..."
   - "[QUERY] ✓ Resumen de licitaciones cargado (20 licitaciones)"
4. El agente debería tener contexto de las 20 licitaciones más recientes
```

### Test 3: Contexto Disponible en Mensaje N
```
1. Crear nueva sesión de chat
2. Enviar: "Hola" (mensaje 1)
3. Enviar: "¿Qué tiempo hace?" (mensaje 2)
4. Enviar: "¿Cómo se llama mi empresa?" (mensaje 3)
5. Verificar que en mensaje 3 el agente puede acceder a get_company_info
6. El agente debe responder correctamente a pesar de no ser el primer mensaje
```

## 📈 Próximos Pasos

1. ✅ Implementar tools de contexto
2. ✅ Integrar en ToolRegistry
3. ✅ Modificar FunctionCallingAgent
4. ✅ Actualizar ChatAgentService
5. ⏳ Probar en desarrollo
6. ⏳ Verificar ahorro de tokens
7. ⏳ Documentar para usuarios

## 🐛 Problemas Resueltos

### Problema Original
"El agente respondía que no tenía acceso a información de la empresa cuando se le preguntaba en mensajes que no fueran el primero"

### Causa
El contexto de empresa solo se añadía en `is_first_message = True`, pero cuando había historial previo, `is_first_message` era `False`.

### Solución
Convertir el contexto en tools que **siempre están disponibles**, independientemente del estado de la conversación.

---

**Fecha de Implementación**: 2025-11-02
**Versión**: 3.2.0
**Estado**: ✅ Implementado, pendiente de pruebas
