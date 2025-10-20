# 📚 Índice de Documentación - TenderAI v3.0

**Sistema de Function Calling Multi-Proveedor para Análisis de Licitaciones**

---

## 🎯 Empezar Aquí

Si es tu primera vez, lee en este orden:

1. **[README.md](README.md)** ← Empieza aquí
   - Visión general del proyecto
   - Instalación y configuración
   - Guía de uso rápida
   - Comparación de proveedores LLM

2. **[TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)** ← Lee esto segundo
   - Documentación completa de las 9 tools
   - Ejemplos de uso para cada tool
   - Casos de uso típicos
   - Estadísticas de frecuencia

3. **[ARCHITECTURE.md](ARCHITECTURE.md)** ← Lee esto para entender el sistema
   - Arquitectura de alto nivel
   - Componentes principales
   - Flujo de datos completo
   - Integración entre componentes

---

## 📖 Documentación Principal

### 🏠 **README.md**

**Qué contiene:**
- Características principales del sistema
- Requisitos e instalación
- Configuración de proveedores (Ollama, OpenAI, Gemini)
- Guía de uso paso a paso
- Solución de problemas
- Roadmap

**Cuándo leerlo:**
- Primera vez usando el sistema
- Instalación en un nuevo entorno
- Configuración de un nuevo proveedor LLM

---

### 🛠️ **TOOLS_REFERENCE.md**

**Qué contiene:**
- Documentación completa de las 9 tools:
  - `search_tenders` - Búsqueda semántica
  - `find_by_budget` - Filtro presupuesto
  - `find_by_deadline` - Filtro fecha límite
  - `find_by_cpv` - Filtro sector CPV
  - `find_by_location` - Filtro geográfico NUTS
  - `get_tender_details` - Detalles completos
  - `get_tender_xml` - XML completo
  - `get_statistics` - Estadísticas agregadas
  - `get_compare_tenders` - Comparación lado a lado
- Parámetros de cada tool
- Ejemplos de uso
- Respuestas esperadas
- Casos de uso típicos

**Cuándo leerlo:**
- Quieres entender qué puede hacer el sistema
- Necesitas saber qué tool usar para un caso específico
- Estás desarrollando nuevas features
- Debugging de consultas

**Ejemplos que encontrarás:**
```
Usuario: "Busca licitaciones de IT con presupuesto > 50k"
→ Tools: find_by_cpv("IT") + find_by_budget(min_budget=50000)

Usuario: "Compara licitaciones 123 y 456"
→ Tools: compare_tenders(tender_ids=["123", "456"])
```

---

### 🏗️ **ARCHITECTURE.md**

**Qué contiene:**
- Arquitectura de alto nivel
- Componentes principales:
  - FunctionCallingAgent
  - ToolRegistry
  - 9 Tools especializadas
  - SchemaConverter
  - ChatAgentService
  - Retriever (ChromaDB)
- Flujo de datos completo
- Comparación de proveedores
- Métricas de rendimiento
- Base de datos (modelos Django + ChromaDB)

**Cuándo leerlo:**
- Quieres entender cómo funciona el sistema internamente
- Estás desarrollando nuevas features
- Necesitas optimizar rendimiento
- Debugging de problemas técnicos
- Planificación de escalabilidad

**Diagramas que encontrarás:**
- Flujo de ejecución completo (9 pasos)
- Arquitectura de componentes
- Integración entre Django y agent_ia_core

---

### ⚙️ **CONFIGURACION_AGENTE.md**

**Qué contiene:**
- Configuración completa del agente RAG
- Variables de entorno (.env)
- Configuración por proveedor
- Parámetros de retrieval
- Opciones de grading y verificación
- Configuración de ChromaDB
- Límites y timeouts

**Cuándo leerlo:**
- Configuración inicial del sistema
- Ajustar parámetros de rendimiento
- Cambiar proveedor LLM
- Optimizar retrieval
- Debugging de problemas de configuración

**Variables importantes:**
```env
USE_FUNCTION_CALLING=true
LLM_PROVIDER=ollama
DEFAULT_K_RETRIEVE=6
LLM_TEMPERATURE=0.3
```

---

### 🔄 **FLUJO_EJECUCION_CHAT.md**

**Qué contiene:**
- Flujo completo de una consulta de chat
- Paso a paso desde frontend hasta respuesta
- Routing per-message
- Integración con agent_ia_core
- Procesamiento de tool calls
- Generación de respuesta final

**Cuándo leerlo:**
- Debugging de flujo de chat
- Entender cómo se procesan las consultas
- Desarrollo de nuevas features de chat
- Optimización de latencia

---

### 📝 **CHANGELOG.md**

**Qué contiene:**
- Historial completo de versiones
- v3.0.0: Sistema Function Calling completo
- v1.4.0: Routing per-message + Ollama
- v1.3.0: Descarga TED mejorada
- v1.2.0: Recomendaciones IA
- v1.1.0: Descarga TED inicial
- v1.0.0: Lanzamiento inicial
- Roadmap de futuras mejoras

**Cuándo leerlo:**
- Quieres saber qué cambió entre versiones
- Planificación de migración
- Entender evolución del proyecto
- Conocer features futuras (roadmap)

---

## 🎓 Guías por Rol

### Para Usuarios Finales

**Lee en orden:**
1. README.md (sección "Guía de Uso")
2. TOOLS_REFERENCE.md (ejemplos de uso)

**Preguntas frecuentes:**
- ¿Cómo buscar licitaciones? → README.md sección "Usar Chat"
- ¿Qué puedo preguntar? → TOOLS_REFERENCE.md sección "Ejemplos"
- ¿Cuál proveedor usar? → README.md sección "Comparación de Proveedores"

---

### Para Administradores

**Lee en orden:**
1. README.md (instalación y configuración)
2. CONFIGURACION_AGENTE.md (configuración avanzada)
3. ARCHITECTURE.md (arquitectura y escalabilidad)

**Preguntas frecuentes:**
- ¿Cómo instalar? → README.md sección "Instalación"
- ¿Cómo configurar Ollama? → README.md sección "Opción A: Ollama"
- ¿Cómo optimizar? → ARCHITECTURE.md sección "Métricas de Rendimiento"

---

### Para Desarrolladores

**Lee en orden:**
1. ARCHITECTURE.md (arquitectura completa)
2. TOOLS_REFERENCE.md (referencia de tools)
3. FLUJO_EJECUCION_CHAT.md (flujo de ejecución)
4. Código fuente en `agent_ia_core/`

**Preguntas frecuentes:**
- ¿Cómo funciona Function Calling? → ARCHITECTURE.md sección "FunctionCallingAgent"
- ¿Cómo crear nueva tool? → TOOLS_REFERENCE.md sección "Buenas Prácticas"
- ¿Cómo se ejecuta una query? → FLUJO_EJECUCION_CHAT.md
- ¿Cómo agregar proveedor? → ARCHITECTURE.md sección "Proveedores LLM"

---

## 🔍 Búsqueda Rápida

### ¿Necesitas información sobre...?

**Instalación:**
→ README.md sección "Instalación"

**Proveedores LLM (Ollama, OpenAI, Gemini):**
→ README.md sección "Configuración de Proveedores"
→ ARCHITECTURE.md sección "Proveedores LLM"

**Tools disponibles:**
→ TOOLS_REFERENCE.md (completo)

**Ejemplos de uso:**
→ TOOLS_REFERENCE.md sección "Ejemplos de Uso"

**Arquitectura técnica:**
→ ARCHITECTURE.md

**Configuración avanzada:**
→ CONFIGURACION_AGENTE.md

**Flujo de ejecución:**
→ FLUJO_EJECUCION_CHAT.md

**Historial de cambios:**
→ CHANGELOG.md

**Solución de problemas:**
→ README.md sección "Solución de Problemas"

---

## 📊 Comparación de Documentos

| Documento | Audiencia | Complejidad | Tiempo Lectura |
|-----------|-----------|-------------|----------------|
| README.md | Todos | Baja | 10-15 min |
| TOOLS_REFERENCE.md | Usuarios + Devs | Media | 20-30 min |
| ARCHITECTURE.md | Devs + Admins | Alta | 30-45 min |
| CONFIGURACION_AGENTE.md | Admins + Devs | Media | 15-20 min |
| FLUJO_EJECUCION_CHAT.md | Devs | Media-Alta | 15-20 min |
| CHANGELOG.md | Todos | Baja | 5-10 min |

---

## 🎯 Casos de Uso

### Caso 1: "Soy nuevo, ¿por dónde empiezo?"

1. **README.md** - Entender qué hace el sistema
2. **README.md** (instalación) - Instalar el sistema
3. **TOOLS_REFERENCE.md** - Ver ejemplos de consultas
4. **Probar en el chat** - Hacer preguntas

---

### Caso 2: "Quiero agregar una nueva tool"

1. **ARCHITECTURE.md** - Entender arquitectura de tools
2. **TOOLS_REFERENCE.md** - Ver estructura de tools existentes
3. **Código fuente** `agent_ia_core/tools/base.py` - Ver clase base
4. **Código fuente** `agent_ia_core/tools/search_tools.py` - Ver ejemplos
5. Implementar nueva tool
6. Registrar en `registry.py`

---

### Caso 3: "El chat no funciona bien"

1. **README.md** (Solución de Problemas) - Problemas comunes
2. **CONFIGURACION_AGENTE.md** - Verificar configuración
3. **FLUJO_EJECUCION_CHAT.md** - Entender flujo para debugging
4. **Logs del servidor** - Ver errores específicos

---

### Caso 4: "Quiero cambiar de Ollama a OpenAI"

1. **README.md** (Opción B: OpenAI) - Instrucciones específicas
2. **CONFIGURACION_AGENTE.md** - Verificar variables de entorno
3. **Perfil de usuario** - Cambiar proveedor y API key
4. **ARCHITECTURE.md** (Proveedores) - Entender diferencias

---

## 📁 Estructura de Archivos

```
TenderAI_Platform/
├── DOCS_INDEX.md              ← Este archivo (índice de docs)
├── README.md                  ← Documentación principal
├── TOOLS_REFERENCE.md         ← Referencia de las 9 tools
├── ARCHITECTURE.md            ← Arquitectura técnica
├── CONFIGURACION_AGENTE.md    ← Configuración del agente
├── FLUJO_EJECUCION_CHAT.md    ← Flujo de ejecución del chat
├── CHANGELOG.md               ← Historial de versiones
└── agent_ia_core/             ← Código fuente
    ├── agent_function_calling.py
    ├── retriever.py
    └── tools/
        ├── base.py
        ├── search_tools.py
        ├── tender_tools.py
        ├── registry.py
        └── schema_converters.py
```

---

## 🔗 Enlaces Rápidos

- **Inicio**: [README.md](README.md)
- **Tools**: [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)
- **Arquitectura**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Configuración**: [CONFIGURACION_AGENTE.md](CONFIGURACION_AGENTE.md)
- **Flujo**: [FLUJO_EJECUCION_CHAT.md](FLUJO_EJECUCION_CHAT.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

## 💡 Consejos

- **Primero README**: Siempre empieza por README.md
- **Ejemplos primero**: TOOLS_REFERENCE.md tiene muchos ejemplos prácticos
- **Usa Ctrl+F**: Busca palabras clave en cada documento
- **Arquitectura para debugging**: ARCHITECTURE.md es clave para resolver problemas técnicos
- **CHANGELOG para cambios**: Consulta CHANGELOG.md antes de actualizar

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
