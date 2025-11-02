# Correcciones Context Tools - Versión 3.2.1

## Problemas Solucionados

### 1. GetTendersSummaryTool Retornaba Datos Vacíos

**Problema**:
- El tool mostraba "Título: Sin título, Organismo: N/A, CPV: N/A" para todas las licitaciones
- Causa: `parsed_summary` tiene estructura anidada `{REQUIRED: {...}, OPTIONAL: {...}}` pero el código accedía directamente a `parsed.get('title')`

**Solución Aplicada**:
Actualizado [context_tools.py](agent_ia_core/tools/context_tools.py) líneas 183-220:

```python
# ANTES (incorrecto):
title = parsed.get('title', 'Sin título')
buyer = parsed.get('buyer_name', 'N/A')

# DESPUÉS (correcto):
required = parsed.get('REQUIRED', {})
optional = parsed.get('OPTIONAL', {})

ojs_id = required.get('ojs_notice_id', 'N/A')
title = required.get('title', 'Sin título')[:80]
buyer = required.get('buyer_name', 'N/A')[:50]
cpv = required.get('cpv_main', 'N/A')
budget = optional.get('budget_eur', 'N/A')
deadline = optional.get('tender_deadline_date', 'N/A')
```

También corregido en `tenders_list`:
```python
# Líneas 215 y 220 - ahora usan 'required' en lugar de 'parsed'
'title': required.get('title', 'Sin título'),
'publication_date': required.get('publication_date', 'N/A')
```

### 2. Metadata de Tools y Tokens

**Estado**: El código ya está correctamente implementado para mostrar:
- ✅ Herramientas usadas (tools_used)
- ✅ Tokens de entrada/salida/total
- ✅ Costo en EUR

**Ubicaciones**:
- **Backend**: [chat/services.py](chat/services.py:427) - metadata incluye `tools_used`
- **Frontend**: [chat/templates/chat/session_detail.html](chat/templates/chat/session_detail.html:82-91) - muestra herramientas
- **Frontend**: [chat/templates/chat/session_detail.html](chat/templates/chat/session_detail.html:99-129) - muestra tokens y costo

## Cómo Probar

### Test 1: Verificar GetTendersSummaryTool Funciona

1. Reiniciar servidor Django:
```bash
python manage.py runserver
```

2. Crear **NUEVA** sesión de chat (importante: no reutilizar sesión antigua)

3. Enviar mensaje de prueba:
```
¿Cuál es la mejor licitación disponible entre las que hay ahora y por qué?
```

4. **Verificar en logs del servidor** (consola):
```
[QUERY] Primer mensaje - Llamando automáticamente a get_tenders_summary...
[REGISTRY] Ejecutando tool 'get_tenders_summary'...
[TOOL] Ejecutando get_tenders_summary con args: {'limit': 20}
[TOOL] get_tenders_summary completado exitosamente
[QUERY] ✓ Resumen de licitaciones cargado (20 licitaciones)
```

5. **Verificar en respuesta del agente**:
- Debe mencionar títulos reales de licitaciones (no "Sin título")
- Debe mencionar organismos reales (no "N/A")
- Debe incluir presupuestos y CPV codes

### Test 2: Verificar Metadata de Tools se Muestra en UI

1. En la misma sesión de chat, enviar:
```
¿Cómo se llama mi empresa?
```

2. **Verificar en logs del servidor**:
```
[TOOLS] LLM solicitó 1 tool(s)
[REGISTRY] Ejecutando tool 'get_company_info'...
[TOOL] Ejecutando get_company_info con args: {}
[TOOL] get_company_info completado exitosamente
[SERVICE] Herramientas usadas (1): get_company_info
```

3. **Verificar en UI del chat**:
- Debajo del mensaje del asistente, debe aparecer:
  ```
  🔧 Herramientas: get_company_info
  ```

### Test 3: Verificar Tokens se Muestran en UI

1. En la sesión de chat, verificar cada mensaje del asistente

2. **Para OpenAI** (si usas OpenAI como provider):
- Debe aparecer un panel morado con:
  ```
  💰 Tokens: 150 entrada + 75 salida = 225
  💵 Coste: €0.0024 (aprox.)
  ```

3. **Para Ollama** (si usas Ollama como provider):
- Debe aparecer un panel verde con:
  ```
  ✓ 225 tokens procesados • 100% GRATIS con Ollama
  ```

## Estructura de Metadata

Cada mensaje del asistente ahora incluye en `metadata`:

```json
{
  "route": "function_calling",
  "documents_used": [
    {
      "id": "00708076-2025",
      "section": "description",
      "content_preview": "..."
    }
  ],
  "verified_fields": [],
  "iterations": 2,
  "num_documents": 1,
  "tools_used": ["get_tenders_summary", "get_company_info"],
  "input_tokens": 1250,
  "output_tokens": 450,
  "total_tokens": 1700,
  "cost_eur": 0.0034
}
```

## Notas Importantes

### ⚠️ Mensajes Antiguos NO se Actualizan

Los mensajes creados **antes** de estos cambios NO tendrán:
- `tools_used` en metadata
- Datos correctos de licitaciones (si usaron get_tenders_summary)

**Solución**: Crear una NUEVA sesión de chat para probar

### ✅ Cambios Aplicados en Esta Versión

1. **[context_tools.py](agent_ia_core/tools/context_tools.py:183-220)** - Corregido acceso a estructura REQUIRED/OPTIONAL
2. **[services.py](chat/services.py:427)** - Ya incluía `tools_used` en metadata
3. **[session_detail.html](chat/templates/chat/session_detail.html:82-91)** - Ya mostraba tools
4. **[session_detail.html](chat/templates/chat/session_detail.html:99-129)** - Ya mostraba tokens

### 📊 Logs Mejorados

El servidor ahora muestra en consola:
```
[SERVICE] ✓ Respuesta procesada: 1234 caracteres
[SERVICE] Documentos recuperados: 3
[SERVICE] Herramientas usadas (2): get_tenders_summary → get_company_info
[SERVICE] Tokens totales: 1700 (in: 1250, out: 450)
[SERVICE] Costo: €0.0034
```

## Siguiente Pasos

1. ✅ Probar con nueva sesión de chat
2. ✅ Verificar que licitaciones muestren datos reales
3. ✅ Verificar que tools aparezcan en UI
4. ✅ Verificar que tokens aparezcan en UI
5. ⏳ Si hay problemas, revisar consola del navegador (F12) para errores JavaScript
6. ⏳ Si metadata no aparece, verificar que ChatMessage.metadata sea JSONField en base de datos

---

**Fecha**: 2025-11-02
**Versión**: 3.2.1
**Estado**: ✅ Implementado y listo para pruebas
