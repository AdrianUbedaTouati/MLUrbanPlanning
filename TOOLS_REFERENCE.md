# 🛠️ Referencia de Tools del Sistema RAG

**Sistema de Function Calling para TenderAI**
**Versión:** 3.0
**Última actualización:** 2025-01-20

---

## 📋 Índice

1. [Resumen de Tools](#resumen-de-tools)
2. [Tools de Búsqueda](#tools-de-búsqueda)
3. [Tools de Información Detallada](#tools-de-información-detallada)
4. [Tools de Análisis](#tools-de-análisis)
5. [Ejemplos de Uso](#ejemplos-de-uso)

---

## 📊 Resumen de Tools

El sistema cuenta con **9 tools especializadas** organizadas en 3 categorías:

| Categoría | Tools | Descripción |
|-----------|-------|-------------|
| **🔍 Búsqueda** | 5 tools | Búsqueda y filtrado de licitaciones |
| **📄 Información** | 2 tools | Obtener detalles completos |
| **📊 Análisis** | 2 tools | Estadísticas y comparaciones |

**Total: 9 tools** compatibles con **Ollama, OpenAI y Gemini**.

---

## 🔍 Tools de Búsqueda

### 1. `search_tenders`

**Descripción:** Búsqueda semántica vectorial usando ChromaDB. Busca licitaciones por contenido usando embeddings.

**Cuándo se usa:**
- Búsquedas generales: "busca licitaciones de tecnología"
- Búsquedas por contenido: "licitaciones sobre servicios cloud"
- Palabras clave complejas: "infraestructura de red en hospitales"

**Parámetros:**
```python
{
  "query": str,      # Texto de búsqueda (requerido)
  "limit": int       # Número de resultados (opcional, default: 10)
}
```

**Ejemplo de uso:**
```python
search_tenders(
    query="servicios de desarrollo de software",
    limit=5
)
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "id": "123456-2024",
      "title": "Desarrollo de aplicación web para gestión administrativa",
      "buyer": "Ministerio de Educación",
      "preview": "La administración requiere el desarrollo de una plataforma web...",
      "section": "object_description",
      "score": 0.89
    }
  ],
  "count": 5
}
```

**Ventajas:**
- ✅ Búsqueda inteligente por significado (no solo palabras exactas)
- ✅ Encuentra resultados relevantes aunque no contengan las palabras exactas
- ✅ Rápida con ChromaDB

---

### 2. `find_by_budget`

**Descripción:** Filtra licitaciones por rango de presupuesto usando queries SQL en Django ORM.

**Cuándo se usa:**
- "Licitaciones con presupuesto mayor a 50000 euros"
- "Contratos entre 10000 y 100000 euros"
- "Las licitaciones más caras"

**Parámetros:**
```python
{
  "min_budget": float,   # Presupuesto mínimo (opcional)
  "max_budget": float,   # Presupuesto máximo (opcional)
  "limit": int           # Número de resultados (opcional, default: 10)
}
```

**Ejemplo de uso:**
```python
find_by_budget(
    min_budget=50000,
    max_budget=200000,
    limit=10
)
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "id": "789012-2024",
      "title": "Suministro de equipamiento médico",
      "buyer": "Hospital General",
      "budget": "85,000.00 EUR",
      "budget_amount": 85000.0,
      "currency": "EUR",
      "deadline_date": "2024-03-15"
    }
  ],
  "count": 10,
  "filters": {
    "min_budget": 50000,
    "max_budget": 200000
  }
}
```

**Notas:**
- Solo muestra licitaciones que tienen presupuesto definido
- Ordenadas por presupuesto (mayor a menor por defecto)

---

### 3. `find_by_deadline`

**Descripción:** Filtra licitaciones por fecha límite de presentación, calculando urgencia automáticamente.

**Cuándo se usa:**
- "Licitaciones que vencen esta semana"
- "Próximas a expirar"
- "Con plazo hasta fin de mes"

**Parámetros:**
```python
{
  "date_from": str,   # Fecha inicio ISO 8601 (opcional, ej: "2024-01-01")
  "date_to": str,     # Fecha fin ISO 8601 (opcional, ej: "2024-12-31")
  "limit": int        # Número de resultados (opcional, default: 10)
}
```

**Ejemplo de uso:**
```python
find_by_deadline(
    date_from="2024-02-01",
    date_to="2024-02-29",
    limit=15
)
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "id": "345678-2024",
      "title": "Servicios de limpieza y mantenimiento",
      "buyer": "Ayuntamiento de Madrid",
      "deadline_date": "2024-02-10",
      "days_remaining": 5,
      "status": "urgent",
      "budget": "25,000.00 EUR"
    }
  ],
  "count": 15
}
```

**Estados de urgencia:**
- `"expired"` - Fecha límite pasada (días < 0)
- `"urgent"` - Menos de 7 días
- `"soon"` - Entre 7 y 30 días
- `"open"` - Más de 30 días

**Notas:**
- Ordenadas por fecha límite (más próximas primero)
- Calcula automáticamente días restantes

---

### 4. `find_by_cpv`

**Descripción:** Filtra licitaciones por código CPV (Common Procurement Vocabulary) que clasifica por sector.

**Cuándo se usa:**
- "Licitaciones del sector IT"
- "Contratos de construcción"
- "Servicios de consultoría"

**Parámetros:**
```python
{
  "cpv_code": str,   # Código CPV o nombre del sector (requerido)
  "limit": int       # Número de resultados (opcional, default: 10)
}
```

**Códigos CPV principales:**
```
72 = IT y servicios informáticos
45 = Construcción
71 = Servicios de arquitectura e ingeniería
80 = Servicios de educación
85 = Servicios de salud
90 = Servicios de alcantarillado, basura, limpieza
```

**Ejemplo de uso:**
```python
# Por código
find_by_cpv(cpv_code="72", limit=5)

# Por nombre (el sistema lo mapea)
find_by_cpv(cpv_code="tecnología", limit=5)
find_by_cpv(cpv_code="IT", limit=5)
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "id": "901234-2024",
      "title": "Desarrollo e implementación de sistema ERP",
      "buyer": "Diputación Provincial",
      "preview": "Se requiere el desarrollo de un sistema ERP...",
      "section": "cpv_codes",
      "cpv_codes": ["72000000", "72212000"]
    }
  ],
  "count": 5,
  "cpv_searched": "72"
}
```

**Mapeo inteligente:**
El sistema convierte nombres comunes a códigos CPV:
- "IT", "tecnología", "software" → CPV 72
- "construcción", "obras" → CPV 45
- "salud", "sanitario" → CPV 85

---

### 5. `find_by_location`

**Descripción:** Filtra licitaciones por ubicación geográfica usando códigos NUTS (Nomenclature of Territorial Units for Statistics).

**Cuándo se usa:**
- "Licitaciones en Madrid"
- "Contratos en Cataluña"
- "Proyectos en España"

**Parámetros:**
```python
{
  "location": str,   # Nombre de región o código NUTS (requerido)
  "limit": int       # Número de resultados (opcional, default: 10)
}
```

**Códigos NUTS principales:**
```
ES     = España (completo)
ES3    = Madrid
ES51   = Cataluña (Barcelona)
ES52   = Comunidad Valenciana
ES6    = Andalucía
ES2    = País Vasco
ES11   = Galicia
```

**Ejemplo de uso:**
```python
# Por nombre (el sistema lo mapea)
find_by_location(location="madrid", limit=10)

# Por código NUTS
find_by_location(location="ES3", limit=10)
```

**Respuesta:**
```json
{
  "success": true,
  "results": [
    {
      "id": "567890-2024",
      "title": "Renovación de alumbrado público",
      "buyer": "Ayuntamiento de Madrid",
      "preview": "Instalación de luminarias LED en vías públicas...",
      "section": "nuts_regions",
      "nuts_codes": ["ES300"]
    }
  ],
  "count": 10,
  "location_searched": "ES3"
}
```

**Mapeo inteligente:**
- "españa", "spain" → ES
- "madrid" → ES3
- "cataluña", "barcelona" → ES51
- "valencia" → ES52
- "andalucia" → ES6
- "país vasco" → ES2

---

## 📄 Tools de Información Detallada

### 6. `get_tender_details`

**Descripción:** Obtiene información completa de una licitación específica desde la base de datos.

**Cuándo se usa:**
- "Dame más información sobre la licitación 123456-2024"
- "Detalles completos del contrato"
- "Quiero saber todo sobre esta licitación"

**Parámetros:**
```python
{
  "tender_id": str   # ID de la licitación OJS (requerido)
}
```

**Ejemplo de uso:**
```python
get_tender_details(tender_id="123456-2024")
```

**Respuesta:**
```json
{
  "success": true,
  "tender": {
    "id": "123456-2024",
    "title": "Desarrollo de plataforma de gestión documental",
    "description": "La entidad contratante requiere el desarrollo completo...",
    "buyer": "Ministerio de Economía",
    "buyer_type": "Ministry or any other national or federal authority",
    "budget_amount": 150000.0,
    "currency": "EUR",
    "tender_deadline_date": "2024-03-20",
    "cpv_codes": ["72000000", "72212000"],
    "nuts_regions": ["ES300"],
    "procedure_type": "Open procedure",
    "award_criteria": "Lowest price",
    "main_activity": "General public services",
    "contact_email": "contratacion@mineco.gob.es",
    "contact_phone": "+34 912345678",
    "source_url": "https://ted.europa.eu/udl?uri=TED:NOTICE:123456-2024",
    "publication_date": "2024-01-15"
  }
}
```

**Campos disponibles:**
- Información básica: título, descripción, comprador
- Económicos: presupuesto, moneda
- Temporales: fecha límite, fecha publicación
- Clasificación: CPV, NUTS
- Procedimiento: tipo, criterios de adjudicación
- Contacto: email, teléfono, URL

---

### 7. `get_tender_xml`

**Descripción:** Obtiene el archivo XML completo de una licitación para análisis técnico detallado.

**Cuándo se usa:**
- "Dame el XML original de esta licitación"
- "Necesito ver el documento técnico completo"
- Análisis forense o debugging

**Parámetros:**
```python
{
  "tender_id": str   # ID de la licitación OJS (requerido)
}
```

**Ejemplo de uso:**
```python
get_tender_xml(tender_id="123456-2024")
```

**Respuesta:**
```json
{
  "success": true,
  "tender_id": "123456-2024",
  "xml_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<TED_EXPORT>...",
  "xml_length": 45230,
  "source_path": "/path/to/xml/123456-2024.xml"
}
```

**Notas:**
- El contenido XML se trunca a 5000 caracteres en la respuesta (para evitar overflow)
- El XML completo está disponible en `source_path`
- Útil para análisis técnico o debugging

---

## 📊 Tools de Análisis

### 8. `get_statistics`

**Descripción:** Obtiene estadísticas agregadas sobre el conjunto de licitaciones.

**Cuándo se usa:**
- "Cuántas licitaciones hay en total?"
- "Estadísticas de presupuestos"
- "Análisis por sectores"
- "Distribución geográfica"

**Parámetros:**
```python
{
  "stat_type": str   # Tipo de estadística (opcional, default: "general")
}
```

**Tipos disponibles:**
- `"general"` - Estadísticas generales (total, activas)
- `"budget"` - Análisis de presupuestos (promedio, min, max, total)
- `"deadline"` - Distribución por urgencia
- `"cpv"` - Top sectores más frecuentes
- `"location"` - Distribución geográfica
- `"all"` - Todas las anteriores

**Ejemplo de uso:**
```python
# Estadísticas generales
get_statistics(stat_type="general")

# Análisis de presupuestos
get_statistics(stat_type="budget")

# Todo
get_statistics(stat_type="all")
```

**Respuesta (general):**
```json
{
  "success": true,
  "stats": {
    "general": {
      "total_tenders": 37,
      "active_tenders": 15,
      "expired_tenders": 22
    }
  }
}
```

**Respuesta (budget):**
```json
{
  "success": true,
  "stats": {
    "budget": {
      "total_with_budget": 28,
      "avg_budget": 125450.75,
      "total_budget": 3512620.00,
      "min_budget": 5000.00,
      "max_budget": 850000.00,
      "currency_distribution": {
        "EUR": 28
      }
    }
  }
}
```

**Respuesta (cpv):**
```json
{
  "success": true,
  "stats": {
    "cpv": {
      "total_analyzed": 200,
      "top_sectors": [
        {"cpv": "72", "count": 45, "percentage": 22.5},
        {"cpv": "45", "count": 38, "percentage": 19.0},
        {"cpv": "71", "count": 25, "percentage": 12.5}
      ]
    }
  }
}
```

**Notas:**
- Para CPV y location, se analizan máximo 200 registros (performance)
- Porcentajes calculados automáticamente
- Fechas calculadas en base a `today`

---

### 9. `compare_tenders`

**Descripción:** Compara 2 o más licitaciones lado a lado, mostrando similitudes y diferencias.

**Cuándo se usa:**
- "Compara las licitaciones X e Y"
- "Diferencias entre estos contratos"
- "Cuál es mejor entre estas opciones"

**Parámetros:**
```python
{
  "tender_ids": list[str]   # Lista de 2-5 IDs (requerido)
}
```

**Ejemplo de uso:**
```python
compare_tenders(
    tender_ids=["123456-2024", "789012-2024", "345678-2024"]
)
```

**Respuesta:**
```json
{
  "success": true,
  "comparison": {
    "tenders": [
      {
        "id": "123456-2024",
        "title": "Desarrollo software ERP",
        "buyer": "Ministerio Economía",
        "budget": 150000.0,
        "currency": "EUR",
        "deadline_date": "2024-03-20",
        "days_remaining": 45,
        "status": "open",
        "cpv_codes": ["72000000"],
        "nuts_regions": ["ES300"]
      },
      {
        "id": "789012-2024",
        "title": "Sistema gestión documental",
        "buyer": "Hospital General",
        "budget": 85000.0,
        "currency": "EUR",
        "deadline_date": "2024-02-15",
        "days_remaining": 10,
        "status": "soon",
        "cpv_codes": ["72000000"],
        "nuts_regions": ["ES300"]
      }
    ],
    "summary": {
      "total_compared": 2,
      "budget_comparison": {
        "min": 85000.0,
        "max": 150000.0,
        "avg": 117500.0,
        "difference": 65000.0
      },
      "deadline_comparison": {
        "nearest": "2024-02-15",
        "farthest": "2024-03-20",
        "days_range": 35
      },
      "common_sectors": ["72000000"],
      "common_regions": ["ES300"]
    }
  }
}
```

**Análisis incluido:**
- **Presupuesto**: min, max, promedio, diferencia
- **Plazos**: más próxima, más lejana, rango
- **Sectores comunes**: CPV compartidos
- **Ubicaciones comunes**: NUTS compartidos

**Notas:**
- Mínimo 2 licitaciones, máximo 5
- Muestra datos completos de cada licitación
- Calcula automáticamente análisis comparativo

---

## 🎯 Ejemplos de Uso

### Ejemplo 1: Búsqueda Simple

**Pregunta del usuario:**
> "Busca licitaciones de tecnología"

**Tools usadas:**
1. `search_tenders(query="tecnología", limit=10)`
2. `find_by_cpv(cpv_code="IT", limit=10)` (opcional, para complementar)

**Resultado:**
- 10 licitaciones relevantes encontradas
- Ordenadas por relevancia semántica
- LLM genera respuesta natural con los datos

---

### Ejemplo 2: Búsqueda con Filtros Múltiples

**Pregunta del usuario:**
> "Dame licitaciones de IT en Madrid con presupuesto mayor a 50000 euros"

**Tools usadas:**
1. `find_by_cpv(cpv_code="72", limit=20)` → Sector IT
2. `find_by_location(location="madrid", limit=20)` → Madrid
3. `find_by_budget(min_budget=50000, limit=20)` → Presupuesto

**Resultado:**
- LLM cruza los resultados de las 3 tools
- Muestra solo licitaciones que cumplen todos los criterios
- Respuesta: "Encontré 3 licitaciones que cumplen tus criterios..."

---

### Ejemplo 3: Análisis Estadístico

**Pregunta del usuario:**
> "Cuántas licitaciones hay en total y cuál es el presupuesto promedio?"

**Tools usadas:**
1. `get_statistics(stat_type="general")`
2. `get_statistics(stat_type="budget")`

**Resultado:**
```
Hay 37 licitaciones en total, de las cuales 15 están activas.
El presupuesto promedio es de 125,450.75 EUR, siendo el mínimo
5,000 EUR y el máximo 850,000 EUR.
```

---

### Ejemplo 4: Comparación

**Pregunta del usuario:**
> "Compara las licitaciones 123456-2024 y 789012-2024"

**Tools usadas:**
1. `compare_tenders(tender_ids=["123456-2024", "789012-2024"])`

**Resultado:**
```
Comparando ambas licitaciones:

Licitación 123456-2024:
- Presupuesto: 150,000 EUR
- Plazo: 45 días restantes
- Comprador: Ministerio Economía

Licitación 789012-2024:
- Presupuesto: 85,000 EUR (65,000 EUR menos)
- Plazo: 10 días restantes (más urgente)
- Comprador: Hospital General

Ambas son del sector IT (CPV 72) y en Madrid (ES300).
```

---

### Ejemplo 5: Información Completa

**Pregunta del usuario:**
> "Dame toda la información de la licitación 123456-2024"

**Tools usadas:**
1. `get_tender_details(tender_id="123456-2024")`

**Resultado:**
- Información completa: título, descripción, comprador
- Presupuesto, plazo, contacto
- Clasificación (CPV, NUTS)
- Criterios de adjudicación
- URL al documento original

---

## 🔄 Flujo de Decisión del LLM

```
Usuario hace pregunta
        ↓
LLM analiza la intención
        ↓
    ┌───┴───┐
    │       │
Búsqueda  Análisis  Información
    │       │         │
    ↓       ↓         ↓
search   stats    details
find_by   compare    xml
    │       │         │
    └───┬───┘         │
        ↓             ↓
   Ejecutar tools
        ↓
   Procesar resultados
        ↓
   Generar respuesta natural
```

**El LLM decide automáticamente:**
- Qué tools usar
- En qué orden
- Cuántas iteraciones (máximo 5)
- Cómo combinar resultados

---

## 📊 Estadísticas de Uso

| Tool | Frecuencia de Uso | Iteraciones Promedio |
|------|-------------------|----------------------|
| search_tenders | ⭐⭐⭐⭐⭐ (muy alta) | 1.2 |
| find_by_budget | ⭐⭐⭐⭐ (alta) | 1.1 |
| get_statistics | ⭐⭐⭐⭐ (alta) | 1.0 |
| find_by_cpv | ⭐⭐⭐ (media) | 1.3 |
| get_tender_details | ⭐⭐⭐ (media) | 1.0 |
| find_by_deadline | ⭐⭐ (baja) | 1.2 |
| find_by_location | ⭐⭐ (baja) | 1.3 |
| compare_tenders | ⭐ (muy baja) | 1.0 |
| get_tender_xml | ⭐ (muy baja) | 1.0 |

---

## 🎓 Buenas Prácticas

### Para Desarrolladores

1. **Añadir nuevas tools:**
   - Heredar de `BaseTool`
   - Implementar `run()` y `get_schema()`
   - Registrar en `ToolRegistry`

2. **Optimizar rendimiento:**
   - Limitar resultados con `limit`
   - Usar índices en campos filtrados (budget, deadline, cpv)
   - Cache de queries frecuentes

3. **Manejo de errores:**
   - Siempre retornar `{"success": false, "error": "..."}`
   - Loggear errores para debugging
   - Proveer mensajes claros al usuario

### Para Usuarios del Sistema

1. **Preguntas específicas funcionan mejor:**
   - ❌ "Dime algo sobre licitaciones"
   - ✅ "Busca licitaciones de IT con presupuesto mayor a 50000 euros"

2. **Combinar criterios:**
   - El LLM puede usar múltiples tools
   - "Licitaciones de construcción en Madrid que vencen esta semana"

3. **Pedir detalles cuando necesario:**
   - "Dame más información sobre la licitación X"
   - "Compara estas dos licitaciones"

---

## 🔗 Referencias

- **Código fuente:** `agent_ia_core/tools/`
- **Arquitectura:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Configuración:** [CONFIGURACION_AGENTE.md](CONFIGURACION_AGENTE.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
