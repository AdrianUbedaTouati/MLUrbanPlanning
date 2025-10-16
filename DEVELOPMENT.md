# Guía de Desarrollo - TenderAI Platform

Esta guía proporciona instrucciones detalladas para configurar el entorno de desarrollo y retomar el proyecto fácilmente.

## 📋 Requisitos del Sistema

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Git
- SQLite (incluido con Python)
- Google Gemini API Key ([Obtener aquí](https://aistudio.google.com/app/apikey))

## 🚀 Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone <repo-url>
cd TenderAI_Platform
```

### 2. Crear Entorno Virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias principales:**
- Django 5.2.7
- LangChain 0.3.14
- LangGraph 0.2.63
- langchain-google-genai 2.0.8
- ChromaDB 0.6.3
- python-decouple
- requests

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (`TenderAI_Platform/.env`):

```env
# Django Configuration
SECRET_KEY=tu-secret-key-super-segura-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite por defecto para desarrollo)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Email (console backend para desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Authentication Settings
LOGIN_ATTEMPTS_ENABLED=True
MAX_LOGIN_ATTEMPTS=5
LOGIN_COOLDOWN_MINUTES=30

# Agent_IA Configuration
LLM_PROVIDER=google
DEFAULT_K_RETRIEVE=5
CHROMA_COLLECTION_NAME=licitaciones
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

**Generar SECRET_KEY:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Aplicar Migraciones

```bash
python manage.py migrate
```

Esto creará:
- Tablas de autenticación (User, PasswordResetToken)
- Tablas de perfiles (CompanyProfile)
- Tablas de licitaciones (Tender, SavedTender, TenderRecommendation)
- Tablas de chat (ChatSession, ChatMessage)

### 6. Crear Superusuario

```bash
python manage.py createsuperuser
```

Proporciona:
- Email (se usa como username)
- Contraseña

### 7. Cargar Datos de Ejemplo (Opcional)

Si tienes fixtures preparados:
```bash
python manage.py loaddata initial_data.json
```

### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver 8001
```

Accede a:
- **Frontend**: http://127.0.0.1:8001/
- **Admin**: http://127.0.0.1:8001/admin/

## 🔑 Configurar API Key Personal

1. Inicia sesión con tu usuario
2. Ve a **Mi Perfil** (menú superior derecho)
3. Click en **Editar Perfil**
4. En la sección **Configuración de IA**, ingresa tu Google Gemini API Key
5. Guarda los cambios

**Sin API key configurada, no funcionarán:**
- Chat inteligente
- Recomendaciones IA
- Autocompletado de perfil de empresa

## 📁 Estructura del Proyecto

```
TenderAI_Platform/
├── TenderAI/                  # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── authentication/            # Sistema de usuarios
│   ├── models.py             # User, PasswordResetToken
│   ├── views.py              # Login, Registro, Recuperación
│   ├── forms.py
│   └── backends.py
│
├── core/                     # Vistas base
│   ├── views.py              # Home, Perfil
│   └── forms.py
│
├── company/                  # Perfiles empresariales
│   ├── models.py             # CompanyProfile
│   ├── views.py              # ProfileView, ExtractCompanyInfoView
│   └── services.py           # CompanyProfileAIService
│
├── tenders/                  # Gestión de licitaciones
│   ├── models.py             # Tender, SavedTender, TenderRecommendation
│   ├── views.py              # Dashboard, List, Search, Download
│   ├── services.py           # TenderRecommendationService, TenderIndexingService
│   ├── ted_downloader.py     # Descarga desde TED API
│   └── templates/tenders/
│       ├── tender_download.html  # Interfaz de descarga con SSE
│       └── ...
│
├── chat/                     # Chat con IA
│   ├── models.py             # ChatSession, ChatMessage
│   ├── views.py              # SessionList, MessageCreate
│   └── services.py           # ChatAgentService
│
├── agent_ia_core/            # Motor de IA
│   ├── agent_graph.py        # LangGraph workflow
│   ├── recommendation_engine.py
│   ├── retriever.py
│   ├── xml_parser.py
│   └── config.py
│
├── static/                   # Archivos estáticos
│   ├── chat/
│   │   ├── css/chat.css
│   │   └── js/chat.js
│   └── core/
│       ├── css/style.css
│       └── js/main.js
│
├── templates/                # Templates base
├── chroma_db/               # Base de datos vectorial (gitignored)
├── db.sqlite3               # Base de datos (gitignored)
├── manage.py
├── requirements.txt
├── .env                     # Variables de entorno (gitignored)
├── README.md
├── CHANGELOG.md
├── ARCHITECTURE.md
└── DEVELOPMENT.md (este archivo)
```

## 🛠️ Comandos Útiles

### Gestión de Base de Datos

```bash
# Crear migraciones después de cambiar modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Resetear base de datos (¡cuidado en producción!)
python manage.py flush

# Exportar datos
python manage.py dumpdata app_name > fixtures.json

# Importar datos
python manage.py loaddata fixtures.json
```

### Gestión de Usuarios

```bash
# Crear superusuario
python manage.py createsuperuser

# Cambiar contraseña de usuario
python manage.py changepassword email@example.com
```

### Servidor de Desarrollo

```bash
# Servidor en puerto por defecto (8000)
python manage.py runserver

# Servidor en puerto específico
python manage.py runserver 8001

# Servidor accesible desde red local
python manage.py runserver 0.0.0.0:8001
```

### Archivos Estáticos

```bash
# Colectar archivos estáticos (producción)
python manage.py collectstatic

# Verificar archivos estáticos
python manage.py findstatic archivo.css
```

### Shell Interactivo

```bash
# Shell de Django
python manage.py shell

# Ejemplo: listar usuarios
>>> from authentication.models import User
>>> User.objects.all()

# Ejemplo: crear licitación
>>> from tenders.models import Tender
>>> Tender.objects.create(title="Test", ojs_notice_id="2024-123456")
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Ejecutar tests de una app específica
python manage.py test authentication

# Ejecutar un test específico
python manage.py test authentication.tests.TestUserModel

# Con verbosidad
python manage.py test --verbosity=2

# Mantener base de datos de test
python manage.py test --keepdb
```

## 🐛 Debugging

### Activar Django Debug Toolbar (Opcional)

1. Instalar:
```bash
pip install django-debug-toolbar
```

2. Añadir a `settings.py`:
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

3. Añadir a `urls.py`:
```python
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
```

### Ver Logs en Terminal

Para ver todos los logs de descarga TED:
```bash
python manage.py runserver 8001 2>&1 | grep -E "\[DOWNLOAD|\[SSE|\[CALLBACK|\[THREAD"
```

En Windows PowerShell:
```powershell
python manage.py runserver 8001 2>&1 | Select-String "\[DOWNLOAD|\[SSE|\[CALLBACK|\[THREAD"
```

### Errores Comunes

**Error: "No module named 'decouple'"**
```bash
pip install python-decouple
```

**Error: "ImproperlyConfigured: SECRET_KEY"**
- Verifica que el archivo `.env` existe
- Verifica que `SECRET_KEY` está definido en `.env`

**Error: "OperationalError: no such table"**
```bash
python manage.py migrate
```

**Error: CSS/JS no se cargan**
1. Verifica `DEBUG=True` en `.env`
2. Archivos deben estar en `static/` con estructura correcta
3. Limpia caché del navegador (Ctrl + Shift + R)
4. Reinicia el servidor

## 📊 Base de Datos

### SQLite (Desarrollo)
- Archivo: `db.sqlite3`
- No requiere servidor separado
- Perfecto para desarrollo local

### Ver contenido de la BD

**Opción 1: Admin de Django**
```
http://127.0.0.1:8001/admin/
```

**Opción 2: SQLite Browser**
- Descargar: https://sqlitebrowser.org/
- Abrir: `db.sqlite3`

**Opción 3: Línea de comandos**
```bash
python manage.py dbshell
.tables
SELECT * FROM authentication_user;
.quit
```

## 🔄 Workflow de Desarrollo

### Añadir una nueva funcionalidad

1. **Crear rama de feature**
```bash
git checkout -b feature/nombre-feature
```

2. **Desarrollar y probar localmente**
```bash
python manage.py runserver 8001
```

3. **Crear/modificar migraciones si cambiaste modelos**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Ejecutar tests**
```bash
python manage.py test
```

5. **Commit y push**
```bash
git add .
git commit -m "Add: descripción de la feature"
git push origin feature/nombre-feature
```

6. **Crear Pull Request**

### Retomar el Proyecto

Si no has trabajado en el proyecto por un tiempo:

1. **Activar entorno virtual**
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. **Actualizar dependencias** (por si hay cambios)
```bash
pip install -r requirements.txt
```

3. **Aplicar migraciones** (por si hay nuevas)
```bash
python manage.py migrate
```

4. **Verificar que todo funciona**
```bash
python manage.py check
python manage.py runserver 8001
```

5. **Revisar CHANGELOG.md** para ver qué ha cambiado

## 🚀 Funcionalidades Implementadas

### 1. Descarga desde TED API
- **Archivo**: `tenders/ted_downloader.py`
- **Vista**: `DownloadTendersExecuteView` en `tenders/views.py`
- **Template**: `tenders/templates/tenders/tender_download.html`
- **URL**: `/licitaciones/obtener/`

**Flujo**:
1. Usuario configura filtros (CPV, país, tipo de aviso)
2. Click en "Iniciar Descarga"
3. Vista establece SSE streaming
4. Thread separado ejecuta descarga
5. Callbacks reportan progreso a través de Queue
6. SSE envía eventos al frontend
7. JavaScript actualiza UI en tiempo real

### 2. Chat con IA
- **Servicio**: `ChatAgentService` en `chat/services.py`
- **Motor**: LangGraph workflow en `agent_ia_core/agent_graph.py`
- **URL**: `/chat/`

**Flujo**:
1. Usuario escribe mensaje
2. Vista crea ChatMessage
3. Service invoca agent_graph con API key del usuario
4. Agente: Route → Retrieve → Grade → Verify → Answer
5. Respuesta guardada con metadata
6. JavaScript muestra mensaje con animaciones

### 3. Recomendaciones IA
- **Servicio**: `TenderRecommendationService` en `tenders/services.py`
- **Motor**: `recommendation_engine.py` en `agent_ia_core/`
- **URL**: `/licitaciones/generar-recomendaciones/`

**Flujo**:
1. Usuario completa perfil de empresa
2. Click en "Generar Recomendaciones"
3. Service obtiene perfil y licitaciones
4. Motor evalúa cada licitación en 5 dimensiones
5. Crea TenderRecommendation con scores
6. Dashboard muestra top recomendaciones

## 📝 Convenciones de Código

### Python
- PEP 8 para estilo de código
- Docstrings para funciones/clases públicas
- Type hints donde sea apropiado
- Nombres descriptivos en español para variables de negocio

### Django
- Una app = una responsabilidad
- Models en singular (Tender, no Tenders)
- Views basadas en clases (CBV) cuando sea apropiado
- Templates organizados por app

### Git Commits
```
Add: nueva funcionalidad
Update: cambio en funcionalidad existente
Fix: corrección de bug
Refactor: mejora de código sin cambio funcional
Docs: cambios en documentación
Style: cambios de formato, espacios, etc.
```

## 🔐 Seguridad

### En Desarrollo
- `DEBUG=True` está bien
- SQLite es suficiente
- Email backend console es apropiado

### En Producción
- `DEBUG=False` siempre
- Usar PostgreSQL
- Configurar email real (SMTP)
- Usar HTTPS
- Configurar `ALLOWED_HOSTS` correctamente
- Usar servidor WSGI (Gunicorn) + Nginx
- Configurar CORS apropiadamente
- Backups regulares de BD

## 📚 Recursos

- [Documentación Django](https://docs.djangoproject.com/en/5.2/)
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/docs)
- [TED API v3](https://ted.europa.eu/api/v3/documentation)
- [ChromaDB Docs](https://docs.trychroma.com/)

## 🆘 Ayuda

Si encuentras problemas:

1. Revisa `CHANGELOG.md` para cambios recientes
2. Verifica que todas las dependencias están instaladas
3. Asegúrate de que las migraciones están aplicadas
4. Revisa los logs del servidor
5. Consulta la documentación técnica en `ARCHITECTURE.md`

---

**Última actualización**: 2025-10-16
**Versión**: 1.1.0
