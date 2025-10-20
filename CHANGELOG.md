# 📝 Changelog - TenderAI Platform

---

## [3.0.0] - 2025-01-20

### ✨ **MAYOR: Sistema Function Calling Multi-Proveedor**

#### Nuevas Características

**9 Tools Especializadas:**
- ✅ `search_tenders` - Búsqueda semántica vectorial (ChromaDB)
- ✅ `find_by_budget` - Filtrado por presupuesto (Django ORM)
- ✅ `find_by_deadline` - Filtrado por fecha límite con cálculo de urgencia
- ✅ `find_by_cpv` - Filtrado por sector CPV (ChromaDB)
- ✅ `find_by_location` - Filtrado geográfico NUTS (ChromaDB)
- ✅ `get_tender_details` - Detalles completos de licitación
- ✅ `get_tender_xml` - Obtener XML completo para análisis
- ✅ `get_statistics` - Estadísticas agregadas (Count, Avg, Sum, Min, Max)
- ✅ `compare_tenders` - Comparación lado a lado de 2-5 licitaciones

**3 Proveedores LLM Soportados:**
- ✅ **Ollama** (local, gratis): qwen2.5:7b y otros modelos
- ✅ **OpenAI** (cloud, pago): gpt-4o-mini y otros
- ✅ **Google Gemini** (cloud, pago): gemini-2.0-flash-exp y otros

**Sistema Function Calling:**
- Decisión automática del LLM sobre qué tools usar
- Iteración inteligente (máximo 5 pasos)
- Conversión automática de schemas entre formatos de proveedores
- Integración transparente con Django via ChatAgentService

#### Nuevos Archivos

**Código:**
- `agent_ia_core/agent_function_calling.py` - Agente principal (442 líneas)
- `agent_ia_core/tools/base.py` - Clase base para tools (107 líneas)
- `agent_ia_core/tools/search_tools.py` - 5 tools de búsqueda (650+ líneas)
- `agent_ia_core/tools/tender_tools.py` - 4 tools de info/análisis (450+ líneas)
- `agent_ia_core/tools/registry.py` - Registro de tools (230 líneas)
- `agent_ia_core/tools/schema_converters.py` - Conversión entre proveedores (280 líneas)
- `agent_ia_core/tools/__init__.py` - Exports

**Tests:**
- `test_multi_provider.py` - Test de validación para los 3 proveedores

**Documentación:**
- `TOOLS_REFERENCE.md` - Documentación completa de las 9 tools con ejemplos
- `ARCHITECTURE.md` - Arquitectura técnica del sistema
- `CHANGELOG_v3.md` - Este changelog

#### Archivos Modificados

- `chat/services.py` - Actualizado para soportar Function Calling
- `agent_ia_core/retriever.py` - Método `retrieve()` para filters
- Modelos Django - Campo `use_function_calling` en User

#### Mejoras

- **Conversión automática de schemas**: Cada proveedor recibe tools en su formato nativo
- **Manejo robusto de errores**: Try/except en todas las tools y llamadas LLM
- **Logging detallado**: Trazabilidad completa de ejecución
- **Extracción de documentos**: Compatibilidad con ChatAgentService legacy

### 🗑️ **Limpieza de Documentación**

**Archivos Eliminados** (redundantes de desarrollo):
- `PLAN_FUNCTION_CALLING.md`
- `PLAN_FUNCTION_CALLING_V2.md`
- `FUNCTION_CALLING_IMPLEMENTATION.md`
- `RESUMEN_IMPLEMENTACION_COMPLETA.md`
- `FASE_2_COMPLETADA.md`
- `FASE_2_COMPLETA_FINAL.md`
- `FASE_3_MULTI_PROVIDER.md`
- `RESUMEN_FASE_3.md`
- `INSTRUCCIONES_FASE_3.md`

**Documentos Consolidados:**
- `TOOLS_REFERENCE.md` - Referencia única de tools
- `ARCHITECTURE.md` - Arquitectura consolidada
- `README.md` - Actualizado con v3.0
- `CHANGELOG_v3.md` - Changelog limpio

### 📊 Métricas

- **Líneas de código agregadas**: ~2,200
- **Tools implementadas**: 9
- **Proveedores soportados**: 3
- **Tests creados**: 1 (multi-proveedor)
- **Documentación**: 3 archivos principales

---

## [1.4.0] - 2025-01-15

### ✨ **Sistema de Chat Inteligente Completado**

#### Routing Per-Message
- Routing 100% LLM que clasifica cada mensaje de forma independiente
- Sin keywords rígidas: El LLM entiende sinónimos e intención automáticamente
- Cambio dinámico entre general/vectorstore según cada mensaje
- Historial contextual usado solo para respuestas, NO para clasificación

#### Integración Ollama
- Soporte completo para modelos Ollama (qwen2.5:7b, llama3.1, etc.)
- Sin costos: No se requiere API key ni pagos
- 100% Privado: Todos los datos quedan en tu máquina
- ChromaDB con 235+ documentos indexados de 37 licitaciones
- Embeddings locales con `nomic-embed-text`

#### Configuración Avanzada
- Sistema completamente configurable vía `.env`
- Archivo `CONFIGURACION_AGENTE.md` con guía completa
- Settings de grading y verificación por usuario
- Control de context length, temperatura, timeout, etc.

#### UI/UX Mejorada
- Diseño premium ultra-moderno para chat
- Gradientes vibrantes y animaciones suaves
- Markdown rendering con sintaxis highlight
- Citation badges con efectos de brillo
- Paneles de costos diferenciados (Ollama vs Cloud)

---

## [1.3.0] - 2025-01-10

### ✨ **Descarga TED API Mejorada**

#### Cancelación en Tiempo Real
- Botón "Cancelar Descarga" dedicado
- Sistema de flags por usuario thread-safe
- Detención inmediata del proceso

#### Precarga Inteligente
- Formulario pre-rellena con datos del perfil de empresa
- CPV codes, región, etc. automáticos en primera visita

#### Correcciones
- Filtros CPV múltiples con paréntesis correctos
- Solución error HTTP 406 en descarga de XMLs
- Persistencia de datos en perfil de empresa
- Headers anti-caché para datos siempre actualizados

---

## [1.2.0] - 2024-12-20

### ✨ **Sistema de Recomendaciones IA**

- Motor de recomendaciones multicriteria
- 5 dimensiones: Técnico (30%), Presupuesto (25%), Geográfico (20%), Experiencia (15%), Competencia (10%)
- Integración con Google Gemini
- Evaluación de hasta 50 licitaciones

### ✨ **Autocompletado de Perfil con IA**

- Extracción automática desde texto libre
- Relleno inteligente de 20+ campos
- Validación y sugerencias

---

## [1.1.0] - 2024-12-10

### ✨ **Descarga Automatizada TED API**

- Interfaz con progreso en tiempo real (SSE)
- Filtros CPV, NUTS, país, tipo de aviso
- Autocompletado con burbujas
- Búsqueda por ventanas de fechas
- Detección de duplicados
- Log estilo terminal

### ✨ **Chat Básico**

- Interfaz estilo Apple minimalista
- AJAX sin recargas
- Historial de conversaciones
- Typing indicator

---

## [1.0.0] - 2024-12-01

### ✨ **Lanzamiento Inicial**

- Sistema de autenticación completo
- Perfiles de empresa con 20+ campos
- CRUD de licitaciones
- Búsqueda y filtrado
- Admin interface
- Templates Bootstrap 5

---

## 🔜 Roadmap

### Fase 4: Optimización (Opcional)
- Cache de embeddings
- Pool de conexiones a LLMs
- Retry logic con exponential backoff
- Timeout management por proveedor

### Fase 5: UI/UX (Opcional)
- Selector de proveedor en UI
- Indicador de tokens usados
- Comparación de respuestas entre proveedores
- Feedback del usuario

### Fase 6: Analytics (Opcional)
- Dashboard de métricas por proveedor
- Tiempo de respuesta, tasa de éxito, tokens consumidos
- Alertas de errores

### Otras Mejoras
- Notificaciones por email
- Exportación a PDF
- API REST
- Programación de descargas periódicas
- Modo multi-agente

---

## 📌 Notas de Versión

**v3.0.0** es una actualización mayor que introduce **Function Calling** completo con soporte multi-proveedor.

**Breaking Changes:**
- Se requiere configurar `USE_FUNCTION_CALLING=true` en `.env` para usar el nuevo sistema
- Los usuarios deben seleccionar `use_function_calling=True` en su perfil

**Compatibilidad:**
- El sistema legacy (EFormsRAGAgent) sigue disponible si `USE_FUNCTION_CALLING=false`
- Migración gradual recomendada

**Recomendaciones:**
- Usar **Ollama** para desarrollo y testing (gratis, local)
- Considerar **OpenAI/Gemini** para producción si se necesita mayor calidad

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
