# Changelog

Todas las cambios notables en TenderAI Platform serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.1.0] - 2025-10-16

### Añadido
- **Sistema de descarga automatizada desde TED API**
  - Interfaz de configuración con parámetros personalizables
  - Filtros de búsqueda: CPV codes, país/región (PLACE), tipo de aviso (NOTICE_TYPE)
  - Progreso en tiempo real con Server-Sent Events (SSE)
  - Log estilo terminal con colores y emojis
  - Barra de progreso visual con porcentaje y contador
  - Búsqueda por ventanas de fechas para evitar límites de API
  - Detección automática de duplicados
  - Parseo y guardado automático en base de datos

- **Servicio TED Downloader** (`tenders/ted_downloader.py`)
  - `search_tenders_by_date_windows()` - Búsqueda inteligente por períodos
  - `download_and_save_tenders()` - Descarga y almacenamiento
  - Sistema de callbacks para reportar progreso
  - Integración con API TED v3

- **Vistas de descarga**
  - `DownloadTendersFormView` - Formulario de configuración
  - `DownloadTendersExecuteView` - Endpoint SSE con streaming en tiempo real
  - Thread separado para descarga sin bloquear la interfaz
  - Queue-based communication entre thread y SSE

- **Template de descarga** (`tender_download.html`)
  - Formulario con filtros CPV, PLACE, NOTICE_TYPE
  - Panel de progreso oculto que se muestra al iniciar
  - Log terminal con auto-scroll
  - Indicadores visuales (⏳ → 🔍 → ⬇️ → 🎉)
  - Manejo de eventos SSE con JavaScript EventSource

### Mejorado
- **Búsqueda de licitaciones**
  - Filtros avanzados: CPV codes, NUTS regions, presupuesto, fechas
  - Autocompletado de CPV y NUTS con AJAX
  - Validación de rangos de presupuesto y fechas
  - Mensajes informativos cuando no hay resultados

- **Logging y debugging**
  - Logs detallados en stderr para todas las operaciones de descarga
  - Prefijos [DOWNLOAD START], [SSE], [CALLBACK], [THREAD] para claridad
  - Información de parámetros en cada descarga

### Técnico
- Uso de `StreamingHttpResponse` para SSE
- Serialización JSON personalizada para objetos date/datetime
- Manejo de heartbeat para mantener conexión SSE viva
- Thread daemon para descargas en background
- Error handling robusto en descarga y parseo

## [1.0.0] - 2025-10-15

### Añadido
- Lanzamiento inicial de TenderAI Platform
- Sistema de autenticación completo
- Perfiles de empresa con autocompletado IA
- Motor de recomendaciones multicriteria
- Chat inteligente con RAG
- Gestión CRUD de licitaciones
- Integración con Google Gemini
- Admin interface configurado
- Templates Bootstrap 5 responsivos

### Apps Implementadas
- `authentication` - Login, registro, recuperación de contraseña
- `core` - Home, perfil de usuario
- `company` - Perfiles empresariales detallados
- `tenders` - Gestión de licitaciones y recomendaciones
- `chat` - Sesiones de chat con IA

### Servicios de IA
- `ChatAgentService` - RAG con LangChain + LangGraph
- `TenderRecommendationService` - Evaluación multicriteria
- `CompanyProfileAIService` - Extracción de información empresarial
- `TenderIndexingService` - Indexación en ChromaDB

---

## Tipos de Cambios
- **Añadido**: Para nuevas características
- **Cambiado**: Para cambios en funcionalidad existente
- **Deprecado**: Para características que serán eliminadas
- **Eliminado**: Para características eliminadas
- **Corregido**: Para corrección de bugs
- **Seguridad**: En caso de vulnerabilidades
- **Mejorado**: Para mejoras en rendimiento o UX
- **Técnico**: Para cambios técnicos internos
