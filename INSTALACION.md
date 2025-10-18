# 🚀 Guía de Instalación - TenderAI Platform

Esta guía te llevará paso a paso para instalar TenderAI Platform en tu máquina local.

---

## 📋 Requisitos Previos

- **Python**: 3.10, 3.11 o 3.12
- **Git**: Para clonar el repositorio
- **Espacio en disco**: Mínimo 5GB (50GB si usas Ollama)
- **Sistema Operativo**: Windows, Linux o macOS

---

## 🔧 Instalación Paso a Paso

### **1. Clonar el Repositorio**

```bash
git clone https://github.com/AdrianUbedaTouati/TED.git
cd TED
```

### **2. Crear Entorno Virtual**

**Windows (PowerShell/CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### **3. Actualizar pip**

```bash
python -m pip install --upgrade pip
```

### **4. Instalar Dependencias**

```bash
pip install -r requirements.txt
```

**⚠️ Si hay errores de conflicto:**
```bash
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### **5. Configurar Variables de Entorno**

**Crear archivo `.env` desde la plantilla:**

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux/macOS:**
```bash
cp .env.example .env
```

**Editar el archivo `.env` y configurar:**

```env
# Clave secreta (cambiar en producción)
SECRET_KEY=django-insecure-cambiar-en-produccion-123456789

# Modo debug (True solo en desarrollo)
DEBUG=True

# Hosts permitidos
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (SQLite por defecto)
DATABASE_URL=sqlite:///db.sqlite3

# URL del sitio
SITE_URL=http://localhost:8001

# Email (console para desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_VERIFICATION_REQUIRED=False

# Autenticación
LOGIN_ATTEMPTS_ENABLED=False
```

### **6. Aplicar Migraciones**

```bash
python manage.py migrate
```

### **7. Crear Superusuario (Opcional)**

```bash
python manage.py createsuperuser
```

Sigue las instrucciones e ingresa:
- Username
- Email
- Password (mínimo 8 caracteres)

### **8. Iniciar Servidor de Desarrollo**

```bash
python manage.py runserver 8001
```

**Servidor corriendo en:** http://127.0.0.1:8001/

---

## 🦙 Instalación de Ollama (Opcional)

Ollama permite ejecutar modelos de IA localmente (gratis, privado, sin límites).

### **Opción A: Script Automático (Windows)**

```cmd
# Ejecutar como administrador
instalar_ollama.bat
```

### **Opción B: Instalación Manual**

**1. Descargar Ollama:**
- Windows: https://ollama.com/download/OllamaSetup.exe
- Linux/macOS: https://ollama.com/download

**2. Instalar:**
- Windows: Ejecutar `OllamaSetup.exe`
- Linux: `curl -fsSL https://ollama.com/install.sh | sh`
- macOS: `brew install ollama`

**3. Descargar Modelos:**
```bash
# Modelo de chat (15-30 minutos, ~41GB)
ollama pull qwen2.5:72b

# Modelo de embeddings (2-3 minutos, ~274MB)
ollama pull nomic-embed-text

# Verificar instalación
ollama list
```

**4. Configurar en TenderAI:**
1. Ir a: http://127.0.0.1:8001/perfil/
2. Proveedor de IA: **Ollama (Local)**
3. Modelo Ollama: `qwen2.5:72b`
4. Modelo Embeddings: `nomic-embed-text`
5. **Guardar cambios**

**5. Verificar:**
```
http://127.0.0.1:8001/ollama/check/
```

**Ver guía completa:** [GUIA_INSTALACION_OLLAMA.md](GUIA_INSTALACION_OLLAMA.md)

---

## 🔑 Configuración de API Keys (Para Proveedores Cloud)

Si prefieres usar **Gemini, OpenAI o NVIDIA** en lugar de Ollama:

### **Google Gemini (Recomendado - Gratis)**
1. Ir a: https://aistudio.google.com/apikey
2. Crear API Key
3. En TenderAI: Perfil → Proveedor: **Google Gemini** → Pegar API Key

### **OpenAI**
1. Ir a: https://platform.openai.com/api-keys
2. Crear API Key
3. En TenderAI: Perfil → Proveedor: **OpenAI** → Pegar API Key

### **NVIDIA NIM**
1. Ir a: https://build.nvidia.com/settings/api-keys
2. Crear API Key (gratis hasta 10K requests)
3. En TenderAI: Perfil → Proveedor: **NVIDIA NIM** → Pegar API Key

---

## 🎯 Verificación de Instalación

### **Comprobar que todo funciona:**

```bash
# 1. Verificar paquetes instalados
pip list | grep langchain

# 2. Verificar migraciones
python manage.py showmigrations

# 3. Verificar servidor
python manage.py check

# 4. Acceder a la aplicación
# Abrir navegador en: http://127.0.0.1:8001/
```

### **URLs Principales:**

- **Home**: http://127.0.0.1:8001/
- **Login**: http://127.0.0.1:8001/login/
- **Registro**: http://127.0.0.1:8001/register/
- **Perfil**: http://127.0.0.1:8001/perfil/
- **Chat**: http://127.0.0.1:8001/chat/
- **Licitaciones**: http://127.0.0.1:8001/tenders/
- **Admin**: http://127.0.0.1:8001/admin/
- **Verificación Ollama**: http://127.0.0.1:8001/ollama/check/

---

## ❌ Solución de Problemas Comunes

### **Error: "SECRET_KEY not found"**

```bash
# Copiar archivo .env.example a .env
cp .env.example .env  # Linux/macOS
Copy-Item .env.example .env  # Windows PowerShell
```

### **Error: Conflicto de versiones en langchain**

```bash
# Limpiar cache e instalar de nuevo
pip cache purge
pip uninstall -y langchain langchain-core langchain-ollama
pip install -r requirements.txt
```

### **Error: "Port 8001 already in use"**

```bash
# Cambiar a otro puerto
python manage.py runserver 8002

# O matar el proceso en el puerto 8001 (Windows)
netstat -ano | findstr :8001
taskkill /PID <numero_pid> /F
```

### **Error: "No module named 'langchain'"**

```bash
# Verificar que el entorno virtual está activado
# Debería ver (.venv) al inicio de la línea de comandos

# Si no está activado:
# Windows:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# Luego instalar dependencias
pip install -r requirements.txt
```

### **Error: "Ollama server not running"**

```bash
# Iniciar servidor Ollama
ollama serve

# En otra terminal, verificar
ollama list
```

---

## 📦 Estructura del Proyecto

```
TenderAI_Platform/
├── .env                    # Variables de entorno (NO subir a git)
├── .env.example            # Plantilla de variables
├── requirements.txt        # Dependencias Python
├── manage.py               # Script Django
├── db.sqlite3              # Base de datos SQLite
├── instalar_ollama.bat     # Script instalación Ollama (Windows)
├── INSTALACION.md          # Esta guía
├── GUIA_INSTALACION_OLLAMA.md  # Guía detallada Ollama
├── ARCHITECTURE.md         # Arquitectura del sistema
│
├── TenderAI/               # Configuración Django
├── authentication/         # App de autenticación
├── core/                   # App núcleo
├── company/                # App perfiles empresariales
├── tenders/                # App licitaciones
├── chat/                   # App chat RAG
├── agent_ia_core/          # Módulo IA (LangGraph)
│
├── static/                 # Archivos estáticos
├── templates/              # Templates Django
├── media/                  # Archivos subidos
└── data/                   # Datos (XMLs, índices)
```

---

## 🎉 ¡Instalación Completada!

Tu plataforma TenderAI está lista para usarse.

**Siguiente paso**: Registrar un usuario y configurar tu perfil empresarial.

### **Recursos Adicionales:**

- **Documentación**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Guía Ollama**: [GUIA_INSTALACION_OLLAMA.md](GUIA_INSTALACION_OLLAMA.md)
- **Repositorio GitHub**: https://github.com/AdrianUbedaTouati/TED
- **Issues/Soporte**: https://github.com/AdrianUbedaTouati/TED/issues

---

**¿Problemas con la instalación?** Abre un issue en GitHub con los detalles del error.

**¡Disfruta de TenderAI Platform!** 🚀✨
