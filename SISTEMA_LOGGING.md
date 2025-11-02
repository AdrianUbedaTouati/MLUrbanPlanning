# Sistema de Logging Detallado y Transparente - v3.3.0

## Objetivo

Crear un sistema de logging **completamente transparente** que registre TODO lo que ocurre en la plataforma, especialmente en las interacciones con el LLM, sin modificar ni filtrar nada.

Este sistema permite auditar, depurar y entender exactamente qué está pasando en cada conversación.

## Estructura de Logs

```
logs/
├── chat/               # Logs de conversaciones
│   ├── session_1_20251102_234500.log
│   ├── session_2_20251102_235100.log
│   └── ...
├── indexacion/         # Logs de indexación de XMLs
│   ├── indexacion_20251102_120000.log
│   └── ...
└── obtener/            # Logs de descarga de licitaciones
    ├── descarga_20251102_100000.log
    └── ...
```

## Loggers Disponibles

### 1. ChatLogger

**Propósito**: Registrar TODA la interacción del chat, línea a línea, sin modificar.

**Ubicación de logs**: `logs/chat/session_{session_id}_{timestamp}.log`

**Qué registra**:

1. **Mensaje del usuario** (texto original completo)
2. **Request al LLM** (todos los mensajes enviados + tools disponibles)
3. **Respuesta del LLM** (respuesta completa, sin modificar)
4. **Llamadas a tools** (nombre + input)
5. **Resultados de tools** (output completo)
6. **Mensaje final del asistente** (con metadata completa)
7. **Errores** (si ocurren)

**Ejemplo de uso**:

```python
from core.logging_config import ChatLogger

# En ChatAgentService
chat_logger = ChatLogger(session_id=123, user_id=456)

# Log mensaje del usuario
chat_logger.log_user_message("¿Cuáles son las mejores licitaciones?")

# Log request al LLM
chat_logger.log_llm_request(
    provider='openai',
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': '...'}],
    tools=[...]
)

# Log respuesta del LLM
chat_logger.log_llm_response(response_object)

# Log tool call
chat_logger.log_tool_call('search_tenders', {'query': 'software'})

# Log tool result
chat_logger.log_tool_result('search_tenders', {'tenders': [...]})

# Log mensaje final
chat_logger.log_assistant_message("Aquí están las licitaciones...", metadata={...})
```

### 2. IndexacionLogger

**Propósito**: Registrar el proceso de indexación de XMLs a base de datos.

**Ubicación de logs**: `logs/indexacion/indexacion_{timestamp}.log`

**Qué registra**:

1. Inicio de indexación (nombre del XML)
2. Campos extraídos del XML (JSON completo)
3. XPaths usados para cada campo
4. Guardado en base de datos (creado/actualizado)
5. Vectorización (número de chunks)
6. Éxito o error

**Ejemplo de uso**:

```python
from core.logging_config import IndexacionLogger

logger = IndexacionLogger()

logger.log_start("715770-2025.xml")
logger.log_parsing({'title': '...', 'contact_email': '...', ...})
logger.log_xpaths_used({'title': './/cbc:Name/text()', ...})
logger.log_db_save('715770-2025', created=True)
logger.log_vectorization('715770-2025', chunks_count=12)
logger.log_success('715770-2025')
```

### 3. ObtenerLogger

**Propósito**: Registrar el proceso de descarga de licitaciones desde TED.

**Ubicación de logs**: `logs/obtener/descarga_{timestamp}.log`

**Qué registra**:

1. Inicio de descarga (query de búsqueda)
2. Request a API de TED (URL + parámetros)
3. Respuesta de API (status + número de notices)
4. Descarga de cada XML (éxito/fallo + ruta)
5. Resumen final (total/descargadas/fallidas)

**Ejemplo de uso**:

```python
from core.logging_config import ObtenerLogger

logger = ObtenerLogger()

logger.log_start("software AND cpv:48000000")
logger.log_api_request("https://ted.europa.eu/api/...", {'q': '...', 'limit': 100})
logger.log_api_response(200, notice_count=45)

for notice in notices:
    logger.log_download(notice_id, success=True, file_path="data/xml/...")

logger.log_summary(total=45, downloaded=43, failed=2)
```

## Formato de Logs

### Timestamp y Nivel

Cada línea de log incluye:

```
2025-11-02 23:45:12.123456 | INFO | Mensaje del log
```

### Estructura de Mensajes

Los mensajes se organizan con separadores visuales:

```
================================================================================
USER MESSAGE (session 123)
================================================================================
¿Cuáles son las mejores licitaciones para mi empresa?

================================================================================
LLM REQUEST → openai/gpt-4o-mini
================================================================================
MESSAGES:
  [0] Role: system
      Eres un asistente experto en licitaciones públicas...
  [1] Role: user
      ¿Cuáles son las mejores licitaciones para mi empresa?

TOOLS AVAILABLE:
  [0] search_tenders
      Description: Busca licitaciones en la base de datos vectorizada...
  [1] get_tender_details
      Description: Obtiene los detalles completos de una licitación...

================================================================================
LLM RESPONSE ←
================================================================================
{
  "answer": "He encontrado 3 licitaciones que podrían interesarte...",
  "route": "function_calling",
  "documents": [...],
  "tools_used": ["search_tenders", "get_tender_details"],
  "iterations": 1,
  "total_tokens": 1234,
  "cost_eur": 0.0045
}

--------------------------------------------------------------------------------
TOOL CALL: search_tenders
--------------------------------------------------------------------------------
INPUT:
  {
    "query": "software desarrollo web",
    "k": 6
  }

--------------------------------------------------------------------------------
TOOL RESULT: search_tenders
--------------------------------------------------------------------------------
  {
    "tenders": [
      {"id": "715770-2025", "title": "..."},
      ...
    ]
  }

================================================================================
ASSISTANT MESSAGE
================================================================================
He encontrado 3 licitaciones que podrían interesarte:

1. **Licitación 715770-2025**
   - Organismo: FECYT
   - Presupuesto: €1,362,932.26
   ...

METADATA:
  {
    "provider": "openai",
    "route": "function_calling",
    "documents_used": [...],
    "tools_used": ["search_tenders", "get_tender_details"],
    "total_tokens": 1234,
    "cost_eur": 0.0045
  }
```

## Características Clave

### 1. Transparencia Total

- **SIN FILTROS**: Se registra TODO tal como es
- **SIN MODIFICACIONES**: Texto original completo
- **LÍNEA A LÍNEA**: Cada línea del contenido se registra por separado

### 2. Trazabilidad Completa

Cada log permite:
- Reconstruir exactamente qué pasó en una conversación
- Ver qué se envió al LLM y qué respondió
- Auditar llamadas a tools y sus resultados
- Verificar costos y tokens usados

### 3. Separación por Componente

- **Chat**: Conversaciones de usuario
- **Indexación**: Proceso de ingesta de XMLs
- **Obtención**: Descarga de licitaciones

Cada componente tiene su propio logger y directorio.

### 4. Timestamps Precisos

Timestamps con microsegundos para orden exacto de eventos:
```
2025-11-02 23:45:12.123456
```

## Integración en el Código

### ChatAgentService

El servicio de chat ahora incluye logging automático:

```python
# chat/services.py

class ChatAgentService:
    def __init__(self, user, session_id=None):
        # ...
        self.chat_logger = None
        if session_id:
            self.chat_logger = ChatLogger(session_id=session_id, user_id=user.id)

    def process_message(self, message, conversation_history=None):
        # Log mensaje del usuario
        if self.chat_logger:
            self.chat_logger.log_user_message(message)

        # ... (procesamiento)

        # Log request al LLM
        if self.chat_logger:
            self.chat_logger.log_llm_request(provider, model, messages, tools)

        # Ejecutar query
        result = agent.query(...)

        # Log respuesta del LLM
        if self.chat_logger:
            self.chat_logger.log_llm_response(result)

        # ... (procesamiento de respuesta)

        # Log mensaje final del asistente
        if self.chat_logger:
            self.chat_logger.log_assistant_message(response_content, metadata)

        return {'content': response_content, 'metadata': metadata}
```

### ChatSessionMessageView

La vista de chat pasa el `session_id` al servicio:

```python
# chat/views.py

chat_service = ChatAgentService(request.user, session_id=session.id)
```

## Cómo Ver los Logs

### Logs de Chat

```bash
# Ver log de una sesión específica
tail -f logs/chat/session_123_*.log

# Ver últimas líneas de todos los logs de chat
tail -n 50 logs/chat/*.log

# Buscar una palabra en todos los logs de chat
grep -r "error" logs/chat/

# Ver logs de hoy
find logs/chat -name "*.log" -mtime -1
```

### Logs de Indexación

```bash
# Ver último proceso de indexación
tail -f logs/indexacion/indexacion_*.log

# Buscar errores en indexación
grep "ERROR" logs/indexacion/*.log
```

### Logs de Obtención

```bash
# Ver última descarga
tail -f logs/obtener/descarga_*.log

# Ver resumen de descargas
grep "RESUMEN" logs/obtener/*.log
```

## Análisis de Logs

### Ejemplo: Ver toda una conversación

```bash
# Sesión 123
cat logs/chat/session_123_20251102_234500.log
```

**Salida**:
```
2025-11-02 23:45:12.123456 | INFO | ================================================================================
2025-11-02 23:45:12.123457 | INFO | USER MESSAGE (session 123)
2025-11-02 23:45:12.123458 | INFO | ================================================================================
2025-11-02 23:45:12.123459 | INFO | ¿Cuáles son las mejores licitaciones?

2025-11-02 23:45:12.234567 | INFO | ================================================================================
2025-11-02 23:45:12.234568 | INFO | LLM REQUEST → openai/gpt-4o-mini
2025-11-02 23:45:12.234569 | INFO | ================================================================================
...
```

### Ejemplo: Contar tokens totales de una sesión

```bash
grep "total_tokens" logs/chat/session_123_*.log | grep -oP "\d+" | awk '{s+=$1} END {print s}'
```

### Ejemplo: Ver qué tools se usaron

```bash
grep "TOOL CALL:" logs/chat/session_123_*.log
```

**Salida**:
```
2025-11-02 23:45:15.456789 | INFO | TOOL CALL: search_tenders
2025-11-02 23:45:16.123456 | INFO | TOOL CALL: get_tender_details
```

## Privacidad y Seguridad

### ⚠️ IMPORTANTE

Los logs contienen información sensible:
- Mensajes completos de usuarios
- Respuestas del LLM
- Datos de licitaciones
- API keys (NO se registran, pero cuidado con otros datos)

### Recomendaciones

1. **NO subir logs a git** (ya incluido en `.gitignore`)
2. **Proteger el directorio `logs/`** con permisos restrictivos
3. **Rotar logs periódicamente** (implementar rotación semanal/mensual)
4. **Cumplir GDPR** si hay datos personales

### Rotación de Logs (TODO)

Implementar rotación automática:

```python
# En core/logging_config.py
from logging.handlers import TimedRotatingFileHandler

handler = TimedRotatingFileHandler(
    log_file,
    when='midnight',
    interval=1,
    backupCount=30,  # Guardar 30 días
    encoding='utf-8'
)
```

## Beneficios del Sistema

### Para Desarrollo

- **Debugging más fácil**: Ver exactamente qué está pasando
- **Reproducir bugs**: Logs contienen TODO lo necesario
- **Optimizar prompts**: Ver qué se envía al LLM y cómo responde
- **Medir costos**: Tokens y costos exactos por conversación

### Para Producción

- **Auditoría completa**: Rastrear todas las interacciones
- **Análisis de uso**: Qué tools se usan más, qué preguntan los usuarios
- **Detección de problemas**: Errores y excepciones registradas
- **Cumplimiento legal**: Logs completos para auditorías

### Para el Usuario (tú)

- **Transparencia total**: Ver exactamente qué hace el agente
- **Entender el sistema**: Cómo funciona el RAG internamente
- **Verificar respuestas**: Qué documentos se usaron
- **Optimizar configuración**: Qué modelo/provider funciona mejor

## Próximos Pasos

### Implementados ✅

1. ChatLogger con logging completo de conversaciones
2. Estructura de directorios `logs/chat/`, `logs/indexacion/`, `logs/obtener/`
3. Integración en `ChatAgentService`
4. Integración en `chat/views.py`
5. `.gitignore` actualizado

### Pendientes ⏳

1. Implementar `IndexacionLogger` en el proceso de indexación
2. Implementar `ObtenerLogger` en el downloader de TED
3. Rotación automática de logs
4. Dashboard web para visualizar logs (opcional)
5. Herramienta de análisis de logs (scripts)

## Troubleshooting

### Problema 1: No se crean logs

**Verificar**:
1. ¿El directorio `logs/` existe?
   ```bash
   ls -la logs/
   ```

2. ¿Permisos de escritura?
   ```bash
   chmod 755 logs/
   ```

3. ¿El `session_id` se pasa correctamente?
   ```python
   print(f"Session ID: {session.id}")
   ```

### Problema 2: Logs incompletos

**Causa**: Excepción antes de completar el logging

**Solución**: Revisar logs de Django/servidor:
```bash
python manage.py runserver --verbosity=3
```

### Problema 3: Logs muy grandes

**Solución temporal**: Limpiar manualmente
```bash
# Borrar logs de más de 7 días
find logs/ -name "*.log" -mtime +7 -delete
```

**Solución permanente**: Implementar rotación automática

---

**Fecha de Implementación**: 2025-11-02
**Versión**: 3.3.0
**Estado**: ✅ Implementado (ChatLogger), ⏳ Pendiente (Indexación/Obtención)
**Archivos Creados**:
- [core/logging_config.py](core/logging_config.py) (NUEVO)

**Archivos Modificados**:
- [chat/services.py](chat/services.py) - Logging integrado
- [chat/views.py](chat/views.py) - Pasar session_id
- [.gitignore](.gitignore) - Excluir logs/
