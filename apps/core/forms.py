from django import forms
from django.core.exceptions import ValidationError
from apps.authentication.models import User


class EditProfileForm(forms.ModelForm):
    """Formulario para editar el perfil de usuario"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
    )
    first_name = forms.CharField(
        required=False,
        label='Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    last_name = forms.CharField(
        required=False,
        label='Apellidos',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        })
    )
    phone = forms.CharField(
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de teléfono'
        })
    )
    city = forms.CharField(
        required=False,
        label='Ciudad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu ciudad (ej: Madrid, Barcelona, Alicante)'
        })
    )
    work_mode = forms.ChoiceField(
        required=False,
        label='Modalidad de trabajo',
        choices=[
            ('any', 'Indiferente'),
            ('remote', 'Remoto'),
            ('onsite', 'Presencial'),
            ('hybrid', 'Híbrido'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    llm_provider = forms.ChoiceField(
        required=False,
        label='Proveedor de IA',
        choices=[
            ('gemini', 'Google Gemini'),
            ('openai', 'OpenAI'),
            ('nvidia', 'NVIDIA NIM'),
            ('ollama', 'Ollama (Local)'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'llm_provider_select'
        })
    )
    llm_api_key = forms.CharField(
        required=False,
        label='API Key',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu API key del proveedor seleccionado',
            'type': 'password',
            'id': 'llm_api_key_input'
        }),
        help_text='No es necesaria para Ollama (modelo local)'
    )
    openai_model = forms.ChoiceField(
        required=False,
        label='Modelo OpenAI',
        choices=[
            ('gpt-4o', 'GPT-4o (Más potente)'),
            ('gpt-4o-mini', 'GPT-4o-mini (Recomendado)'),
            ('gpt-4-turbo', 'GPT-4 Turbo'),
            ('gpt-3.5-turbo', 'GPT-3.5 Turbo (Económico)'),
        ],
        initial='gpt-4o-mini',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'openai_model_select'
        })
    )
    ollama_model = forms.CharField(
        required=False,
        label='Modelo Ollama',
        initial='qwen2.5:72b',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: qwen2.5:72b',
            'id': 'ollama_model_input'
        })
    )
    ollama_embedding_model = forms.CharField(
        required=False,
        label='Modelo de Embeddings Ollama',
        initial='nomic-embed-text',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: nomic-embed-text',
            'id': 'ollama_embedding_input'
        })
    )

    # Google Search API settings
    use_web_search = forms.BooleanField(
        required=False,
        label='Activar Búsqueda Web',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'use_web_search_checkbox'
        }),
        help_text='Permite buscar ofertas de empleo en internet'
    )
    google_search_api_key = forms.CharField(
        required=False,
        label='Google Search API Key',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'AIza...',
            'type': 'password',
            'id': 'google_search_api_key_input'
        }),
        help_text='API key de Google Custom Search API (100 búsquedas/día gratis)'
    )
    google_search_engine_id = forms.CharField(
        required=False,
        label='Google Custom Search Engine ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'a1b2c3d4e5f6g7h8i',
            'id': 'google_search_engine_id_input'
        }),
        help_text='ID del motor de búsqueda personalizado'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'city', 'work_mode',
                 'llm_provider', 'llm_api_key', 'openai_model', 'ollama_model', 'ollama_embedding_model',
                 'use_web_search', 'google_search_api_key', 'google_search_engine_id')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = kwargs.get('instance')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.current_user.pk).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.current_user.pk).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username


class CVImageUploadForm(forms.Form):
    """Formulario para subir imagen o PDF del CV para análisis con Vision API"""
    cv_file = forms.FileField(
        required=True,
        label='CV (Imagen o PDF)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        }),
        help_text='Sube una imagen (JPG, PNG) o PDF de tu CV. Se analizará con GPT-4 Vision.'
    )

    def clean_cv_file(self):
        file = self.cleaned_data.get('cv_file')
        if file:
            ext = file.name.lower().split('.')[-1]
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf']:
                raise forms.ValidationError('Formato no soportado. Usa JPG, PNG o PDF.')
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede superar 10MB.')
        return file
