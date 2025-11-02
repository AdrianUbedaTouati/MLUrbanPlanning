# Re-indexación de Información de Contacto - v3.2.11

## Problema Identificado

El usuario preguntó por la información de contacto de la licitación 715770-2025 y el agente respondió que no estaba disponible, a pesar de que:

1. El XML SÍ contiene la información de contacto
2. El fix de v3.2.9 corrigió los XPaths para extraer contacto
3. La tool `get_tender_details` funciona correctamente

### Causa Raíz

Las **30 licitaciones en la base de datos fueron indexadas ANTES del fix v3.2.9** (29 oct 2025), cuando los XPaths de contacto estaban incorrectos (0% de coverage).

**Consecuencia**: Los campos `contact_email`, `contact_phone`, `contact_url`, `contact_fax` estaban **vacíos en la base de datos**, aunque el XML original SÍ tenía la información.

## Solución Aplicada

### Re-indexación Completa

Se ejecutó un script de re-indexación que:

1. Lee cada licitación de la base de datos (30 total)
2. Re-parsea el XML original con los XPaths corregidos
3. Actualiza los 4 campos de contacto
4. Guarda los cambios en la base de datos

### Resultados

```
================================================================================
RESUMEN DE RE-INDEXACIÓN
================================================================================
Total procesadas:    30
Actualizadas:        29
Sin cambios:         1  (ya tenía la info)
Errores:             0
================================================================================
```

## Verificación

### Licitación 715770-2025 (Ejemplo)

**ANTES de re-indexación**:
```json
{
  "id": "715770-2025",
  "title": "Licitación 715770-2025",
  "buyer_name": "Organismo público (por determinar)"
  // contact: NO EXISTE
}
```

**DESPUÉS de re-indexación**:
```json
{
  "id": "715770-2025",
  "title": "Licitación 715770-2025",
  "buyer_name": "Organismo público (por determinar)",
  "contact": {
    "email": "Contratacion@fecyt.es",
    "phone": "914250909",
    "url": "http://www.fecyt.es",
    "fax": "915712172"
  }
}
```

### Verificación de Otras Licitaciones

Ejemplos de información de contacto ahora disponible:

| ID | Email | Teléfono | URL |
|----|-------|----------|-----|
| 668692-2025 | cdgrree.scs@gobiernodecanarias.org | 928118908 | http://www3.gobiernodecanarias.org/sanidad/scs/ |
| 668461-2025 | licitaciones@fundae.es | +34 911195030 | http://www.fundae.es |
| 667665-2025 | contratacion@guaguas.com | 928305808 | https://www.guaguas.com/empresa/perfil-del-contratante |
| 666616-2025 | perfildelcontratante@malaga.eu | +34 951929312 | http://www.malaga.eu |
| 715770-2025 | Contratacion@fecyt.es | 914250909 | http://www.fecyt.es |

## Estadísticas de Cobertura

### ANTES de v3.2.9 (XPaths incorrectos)
- Email: 0/30 (0%)
- Teléfono: 0/30 (0%)
- URL: 0/30 (0%)
- Fax: 0/30 (0%)

### DESPUÉS de v3.2.9 + Re-indexación
- Email: 30/30 (100%)
- Teléfono: 30/30 (100%)
- URL: 29/30 (96.7%)
- Fax: 18/30 (60%)

## Próximos Pasos para el Usuario

### El Agente Ahora Puede Mostrar Contactos

Cuando el usuario pregunte de nuevo por información de contacto, el agente DEBE poder:

1. Llamar a `get_tender_details(tender_id='715770-2025')`
2. Recibir el objeto completo con `contact: {...}`
3. Extraer y mostrar al usuario:
   - Email
   - Teléfono
   - URL
   - Fax (si está disponible)

### Ejemplo de Respuesta Esperada

**Usuario**: "dame la url el telefono y el email de contacto de esa oferta"

**Agente** (debería responder):
```
Información de contacto para la licitación 715770-2025:

📧 Email: Contratacion@fecyt.es
📞 Teléfono: 914250909
🌐 URL: http://www.fecyt.es
📠 Fax: 915712172
```

## Notas Técnicas

### ¿Por Qué No Se Hizo Automáticamente?

Las licitaciones existentes NO se re-indexan automáticamente cuando se mejora el parser porque:

1. **Preservación de datos**: No queremos sobrescribir datos manualmente corregidos
2. **Performance**: Re-indexar 1000+ licitaciones sería muy costoso
3. **Trazabilidad**: Es mejor hacer re-indexaciones explícitas y documentadas

### Licitaciones Futuras

Las **nuevas licitaciones** que se indexen a partir de ahora SÍ tendrán la información de contacto automáticamente, gracias al fix de v3.2.9.

### Base de Datos

Los cambios están en `db.sqlite3`, que contiene:
- Tabla `tenders_tender` con 30 registros
- Campos actualizados: `contact_email`, `contact_phone`, `contact_url`, `contact_fax`

**IMPORTANTE**: `db.sqlite3` NO se incluye en commits de git (está en .gitignore), por lo que esta actualización solo afecta al entorno local.

## Troubleshooting

### El Agente Sigue Sin Mostrar Contactos

**Posibles causas**:

1. **Cache del agente**: Reiniciar el servidor Django
   ```bash
   python manage.py runserver
   ```

2. **Sesión de chat antigua**: Crear una nueva sesión de chat

3. **Problema en el prompt del LLM**: El LLM puede estar recibiendo la información pero no la está mostrando al usuario

**Verificar manualmente**:
```bash
python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TenderAI.settings')
django.setup()

from agent_ia_core.tools.tender_tools import GetTenderDetailsTool

tool = GetTenderDetailsTool()
result = tool.run(tender_id='715770-2025')

print(result.get('tender', {}).get('contact', {}))
"
```

**Resultado esperado**:
```python
{
  'email': 'Contratacion@fecyt.es',
  'phone': '914250909',
  'url': 'http://www.fecyt.es',
  'fax': '915712172'
}
```

---

**Fecha de Re-indexación**: 2025-11-02 23:45
**Versión**: 3.2.11
**Estado**: ✅ Completado, 29/30 licitaciones actualizadas
**Impacto**: Información de contacto ahora disponible para todas las licitaciones
