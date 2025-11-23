# Changelog - TenderAI Platform

## [v3.7.1] - 2025-11-21

### Reestructuracion de agent_ia_core
- **Nueva estructura modular** con carpetas organizadas:
  - `parser/` - XML parsing y chunking (xml_parser.py, chunking.py, tools_xml.py)
  - `prompts/` - System prompts del agente
  - `indexing/` - RAG retrieval e indexacion (retriever.py, index_build.py, ingest.py)
  - `download/` - Descarga TED (descarga_xml.py, token_tracker.py)
  - `engines/` - Motores especializados (recommendation_engine.py)
- **Todos los imports actualizados** en apps/, tests/, y tools/

### Correcciones
- **Fix web_search**: Ahora busca realmente en internet (antes mostraba datos inventados)
  - Agregada tool web_search al system prompt del agente
- **Fix LOGS_DIR**: Los logs ahora se crean en la carpeta raiz del proyecto
- **Fix TenderAI.settings**: Todas las referencias cambiadas a config.settings
- **Fix static files**: Restaurado Dark Mode CSS que se habia perdido en refactoring

### Documentacion
- README.md movido a la raiz del proyecto
- Actualizada estructura de proyecto con nueva organizacion
- Agregada tabla de almacenamiento (donde se guarda cada cosa)

---

## [v3.7.0] - 2025-11-15

### BrowseInteractiveTool con Playwright
- **Navegador Chromium headless** con Playwright
- **JavaScript completo** (SPA, React, Vue, Angular)
- **Modo inteligente con LLM**: Analiza pagina -> Decide accion -> Ejecuta -> Repite
- **Acciones soportadas**: Click, fill forms, wait, scroll, navigate
- **95-98% success rate** en sitios gubernamentales

---

## [v3.6.0] - 2025-11-10

### Review Loop Automatico
- **ResponseReviewer** evalua TODAS las respuestas
- **3 criterios**: Formato (30%), Contenido (40%), Analisis (30%)
- **Segunda iteracion SIEMPRE ejecutada** con prompt mejorado
- **Merge inteligente** de documentos de ambas iteraciones

---

## [v3.0.0] - 2025-10-01

### Sistema Function Calling Completo
- **16 tools especializadas** (11 activas + 5 opcionales)
- **Hasta 15 iteraciones automaticas**
- **SchemaConverter** para multi-proveedor LLM
- **ToolRegistry** con categorias: Context, Search, Info, Analysis, Quality, Web

---

## [v1.4.0] - 2025-09-15

### Routing per-message + Ollama
- **100% local** con Ollama (sin API keys)
- **Routing LLM** per-message

---

## [v1.3.0] - 2025-09-01

### Descarga TED mejorada
- **Cancelacion en tiempo real**
- **Precarga automatica** de perfil de empresa
- **Correccion filtros CPV** multiples

---

## [v1.2.0] - 2025-08-15

### Recomendaciones IA Multicriteria
- **Motor de recomendaciones** con 5 dimensiones
- Score tecnico, presupuesto, geografico, experiencia, competencia

---

## [v1.1.0] - 2025-08-01

### Descarga TED inicial
- **Integracion TED API**
- **Progreso en tiempo real** con SSE

---

## [v1.0.0] - 2025-07-15

### Lanzamiento inicial
- Sistema de autenticacion
- Perfiles de empresa
- Chat RAG basico
- Gestion de licitaciones
