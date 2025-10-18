# 🦙 Guía de Instalación de Ollama para TenderAI Platform

Esta guía te enseñará a instalar y configurar **Ollama** para ejecutar modelos de IA localmente en TenderAI Platform, con **máxima calidad**, **privacidad total** y **costo cero**.

---

## 📋 Requisitos del Sistema

### Hardware Recomendado

Para ejecutar **Qwen2.5 72B** (el modelo recomendado para análisis de licitaciones):

- **RAM**: 32GB+ (tu máquina con 32GB es perfecta)
- **GPU**: NVIDIA RTX 5080 (16GB VRAM) ✅ EXCELENTE
- **Disco**: 50GB libres (para modelo + datos)
- **CPU**: Cualquier procesador moderno

### Hardware Mínimo

Si quieres probar con modelos más pequeños:

- **RAM**: 16GB
- **GPU**: NVIDIA GTX 1060 6GB o superior
- **Disco**: 10GB libres

---

## 🚀 Paso 1: Instalar Ollama

### Windows

1. **Descargar el instalador**:
   - Ve a: https://ollama.com/download/windows
   - Descarga `OllamaSetup.exe`

2. **Ejecutar el instalador**:
   - Doble clic en `OllamaSetup.exe`
   - Sigue las instrucciones del asistente
   - Se instalará en `C:\Program Files\Ollama\`

3. **Verificar instalación**:
   ```cmd
   ollama --version
   ```
   Deberías ver algo como: `ollama version 0.3.0`

### Linux / WSL

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS

```bash
brew install ollama
```

---

## 🤖 Paso 2: Descargar el Modelo Qwen2.5 72B

Este es el **mejor modelo** para análisis de licitaciones públicas debido a su:
- ✅ Calidad comparable a GPT-4
- ✅ Excelente razonamiento analítico
- ✅ Mejor comprensión del español técnico
- ✅ Capacidad de análisis comparativo

### Descargar Qwen2.5 72B

```cmd
ollama pull qwen2.5:72b
```

**Tiempo estimado**: 15-30 minutos (descarga ~41GB)

### Verificar descarga

```cmd
ollama list
```

Deberías ver:
```
NAME                MODIFIED      SIZE
qwen2.5:72b         2 hours ago   41GB
```

---

## 📦 Paso 3: Descargar Modelo de Embeddings

Para vectorización de licitaciones, descarga **nomic-embed-text**:

```cmd
ollama pull nomic-embed-text
```

**Tiempo estimado**: 1-2 minutos (descarga ~274MB)

### Verificar embeddings

```cmd
ollama list
```

Deberías ver:
```
NAME                    MODIFIED      SIZE
qwen2.5:72b             2 hours ago   41GB
nomic-embed-text        1 hour ago    274MB
```

---

## ⚙️ Paso 4: Iniciar el Servidor Ollama

Ollama necesita estar corriendo en segundo plano.

### Windows

Ollama se inicia automáticamente al instalarse. Verifica que esté corriendo:

```cmd
ollama serve
```

Si ves `Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address`, significa que **ya está corriendo** ✅

### Linux / macOS

```bash
ollama serve
```

Deja esta terminal abierta.

---

## 🔧 Paso 5: Verificar que Funciona

### Probar el modelo de chat

```cmd
ollama run qwen2.5:72b
```

Escribe una pregunta de prueba:
```
>>> Analiza las ventajas de usar LLMs locales vs cloud para análisis de licitaciones
```

Deberías recibir una respuesta detallada en español.

Para salir: escribe `/bye`

### Probar embeddings

```cmd
ollama run nomic-embed-text "Este es un texto de prueba para vectorización"
```

Deberías ver un vector de números (embedding generado).

---

## 🎯 Paso 6: Configurar TenderAI Platform

### 6.1. Instalar langchain-ollama

```cmd
cd "c:\Users\andri\Desktop\Proyectos\Pagina web Agent_IA\Pagina web Agent_IA\TenderAI_Platform"
pip install langchain-ollama
```

### 6.2. Aplicar Migraciones de Base de Datos

```cmd
python manage.py makemigrations
python manage.py migrate
```

Esto añadirá los campos `ollama_model` y `ollama_embedding_model` al modelo User.

### 6.3. Reiniciar el Servidor Django

```cmd
python manage.py runserver 8001
```

---

## 🌐 Paso 7: Configurar tu Perfil de Usuario

1. **Abrir tu navegador**:
   - Ve a: http://127.0.0.1:8001/perfil/

2. **Seleccionar Proveedor**:
   - En "Proveedor de IA", selecciona: **Ollama (Local)**

3. **Configurar Modelos**:
   - **Modelo Ollama**: `qwen2.5:72b`
   - **Modelo de Embeddings Ollama**: `nomic-embed-text`

4. **API Key**:
   - Déjalo vacío (Ollama no requiere API key)

5. **Guardar Cambios**

---

## ✅ Paso 8: Probar la Integración

### Opción A: Probar el Chat

1. Ve a: http://127.0.0.1:8001/chat/
2. Crea una nueva sesión de chat
3. Pregunta algo como:
   ```
   ¿Cuáles son las licitaciones más relevantes para mi empresa?
   ```

Deberías ver:
- ✅ Indicador "Pensando..." rotando
- ✅ Respuesta generada por Qwen2.5 72B
- ✅ Costo: **€0.00 (Gratis)** ← Sin cargos

### Opción B: Indexar Licitaciones

1. Ve a: http://127.0.0.1:8001/tenders/
2. Descarga algunas licitaciones XML
3. Ve a la pestaña "Vectorización"
4. Haz clic en "Indexar Todo"

Verás:
- ✅ Indexación con embeddings de `nomic-embed-text`
- ✅ Costo total: **€0.00 (Gratis)**
- ✅ Sin límites de uso

---

## 🎨 Modelos Alternativos

Si Qwen2.5 72B es demasiado lento o necesitas probar otros modelos:

### Para CHAT

| Modelo | Tamaño | Velocidad | Calidad | Comando |
|--------|--------|-----------|---------|---------|
| **Qwen2.5 72B** ⭐ | 41GB | Media | Máxima | `ollama pull qwen2.5:72b` |
| Llama 3.3 70B | 40GB | Media | Muy Alta | `ollama pull llama3.3:70b` |
| DeepSeek-R1 14B | 9GB | Rápida | Alta | `ollama pull deepseek-r1:14b` |
| Llama 3.1 8B | 4.7GB | Muy Rápida | Media | `ollama pull llama3.1:8b` |
| Mistral 7B | 4.1GB | Muy Rápida | Media-Alta | `ollama pull mistral:7b` |

### Para EMBEDDINGS

| Modelo | Tamaño | Contexto | Calidad | Comando |
|--------|--------|----------|---------|---------|
| **nomic-embed-text** ⭐ | 274MB | 8192 tokens | Alta | `ollama pull nomic-embed-text` |
| mxbai-embed-large | 669MB | 512 tokens | Muy Alta (español) | `ollama pull mxbai-embed-large` |

### Cambiar de Modelo

1. Descarga el nuevo modelo:
   ```cmd
   ollama pull llama3.3:70b
   ```

2. Ve a tu perfil: http://127.0.0.1:8001/perfil/
3. Cambia "Modelo Ollama" a: `llama3.3:70b`
4. Guarda cambios

---

## 🔍 Solución de Problemas

### Problema 1: "Error: connect ECONNREFUSED 127.0.0.1:11434"

**Causa**: Ollama no está corriendo

**Solución**:
```cmd
ollama serve
```

### Problema 2: "Error: model 'qwen2.5:72b' not found"

**Causa**: No has descargado el modelo

**Solución**:
```cmd
ollama pull qwen2.5:72b
```

### Problema 3: Respuestas muy lentas

**Causa**: Modelo demasiado grande para tu GPU

**Soluciones**:
1. Usar un modelo más pequeño (ej: `deepseek-r1:14b`)
2. Cerrar otras aplicaciones para liberar VRAM
3. Verificar que la GPU esté siendo utilizada:
   ```cmd
   nvidia-smi
   ```

### Problema 4: "Out of memory"

**Causa**: RAM o VRAM insuficiente

**Soluciones**:
1. Cerrar navegadores y aplicaciones pesadas
2. Usar un modelo más pequeño (ej: `mistral:7b`)
3. Reiniciar Ollama:
   ```cmd
   taskkill /F /IM ollama.exe
   ollama serve
   ```

### Problema 5: Modelo se descarga lentamente

**Causa**: Conexión lenta

**Solución**:
- Sé paciente (modelos grandes tardan)
- Verifica velocidad de internet
- Pausa y resume la descarga:
  ```cmd
  # Si se interrumpe, simplemente vuelve a ejecutar:
  ollama pull qwen2.5:72b
  # Ollama resume desde donde se quedó
  ```

---

## 📊 Comparativa: Ollama vs APIs Cloud

| Aspecto | Ollama Local | Gemini/OpenAI/NVIDIA |
|---------|--------------|----------------------|
| **Privacidad** | ⭐⭐⭐⭐⭐ Máxima | ⭐⭐⭐ Media |
| **Costo** | ⭐⭐⭐⭐⭐ Gratis | ⭐⭐ De pago |
| **Velocidad** | ⭐⭐⭐⭐ Depende HW | ⭐⭐⭐⭐ Consistente |
| **Calidad (72B)** | ⭐⭐⭐⭐⭐ Comparable GPT-4 | ⭐⭐⭐⭐⭐ Alta |
| **Offline** | ⭐⭐⭐⭐⭐ Sí | ❌ No |
| **Límites** | ⭐⭐⭐⭐⭐ Ilimitado | ⭐⭐⭐ Cuotas |
| **Facilidad** | ⭐⭐⭐ Técnico | ⭐⭐⭐⭐⭐ Simple |

---

## 🎓 Recursos Adicionales

- **Documentación Oficial**: https://ollama.com/library
- **Modelos Disponibles**: https://ollama.com/library/qwen2.5
- **GitHub de Ollama**: https://github.com/ollama/ollama
- **Comunidad Discord**: https://discord.gg/ollama

---

## 💡 Consejos de Uso

### Para Máximo Rendimiento

1. **Usa GPU**: Ollama detecta automáticamente tu NVIDIA RTX 5080
2. **Cierra aplicaciones**: Libera RAM/VRAM para el modelo
3. **Deja calentarse el modelo**: Primera consulta puede tardar más

### Para Máxima Calidad

1. **Usa Qwen2.5 72B**: Mejor para análisis complejos
2. **Configura temperatura**: Baja (0.3-0.5) para respuestas precisas
3. **Proporciona contexto**: Más detalles = mejores respuestas

### Para Máxima Privacidad

1. **Datos locales**: Nada sale de tu máquina
2. **Sin telemetría**: Ollama no envía datos a servidores
3. **GDPR compliant**: Ideal para licitaciones confidenciales

---

## 📞 Soporte

Si tienes problemas:

1. **Verifica logs de Ollama**:
   - Windows: `C:\Users\<tu-usuario>\.ollama\logs\server.log`
   - Linux: `~/.ollama/logs/server.log`

2. **Reporta issues**:
   - GitHub TenderAI: https://github.com/tu-repo/issues
   - GitHub Ollama: https://github.com/ollama/ollama/issues

---

## ✅ Checklist Final

Marca cada paso cuando lo completes:

- [ ] Ollama instalado y `ollama --version` funciona
- [ ] Modelo `qwen2.5:72b` descargado (`ollama list`)
- [ ] Embeddings `nomic-embed-text` descargado
- [ ] Servidor Ollama corriendo (`ollama serve`)
- [ ] `langchain-ollama` instalado (`pip list | grep ollama`)
- [ ] Migraciones aplicadas (`python manage.py migrate`)
- [ ] Perfil configurado con provider "Ollama (Local)"
- [ ] Chat funcionando con respuestas de Qwen2.5
- [ ] Indexación funcionando con costo €0.00

---

## 🎉 ¡Listo!

Ahora tienes:
- ✅ Modelo de **calidad GPT-4** corriendo localmente
- ✅ **Privacidad total** - nada sale de tu máquina
- ✅ **Costo cero** - sin límites de uso
- ✅ **Rendimiento excelente** con tu RTX 5080

**¡Disfruta de TenderAI con Ollama!** 🦙🚀
