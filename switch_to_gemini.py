"""
Script para cambiar el usuario pepe2012 de NVIDIA a Gemini
NVIDIA/Llama tiene políticas muy estrictas que rechazan preguntas legítimas de negocios
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TenderAI.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Get user
try:
    user = User.objects.get(username='pepe2012')

    print(f"\n=== CAMBIO DE PROVEEDOR LLM ===")
    print(f"Usuario: {user.username}")
    print(f"Proveedor actual: {user.llm_provider}")
    print(f"API Key actual: {user.llm_api_key[:20] if user.llm_api_key else 'No configurada'}...")

    # Cambiar a Gemini
    user.llm_provider = 'gemini'

    # Pedir nueva API key de Gemini
    print("\n" + "="*60)
    print("NECESITAS UNA API KEY DE GOOGLE GEMINI")
    print("="*60)
    print("1. Ve a: https://aistudio.google.com/app/apikey")
    print("2. Haz clic en 'Create API Key'")
    print("3. Copia la API key que empieza con 'AIzaSy...'")
    print("="*60)

    gemini_key = input("\nPega tu API key de Gemini aquí (o Enter para mantener la actual): ").strip()

    if gemini_key:
        user.llm_api_key = gemini_key
        print(f"\n✓ API key de Gemini configurada")
    else:
        print(f"\n! Manteniendo API key actual (puede no funcionar con Gemini)")

    # Guardar cambios
    user.save()

    print(f"\n✓ Usuario actualizado:")
    print(f"  - Proveedor: {user.llm_provider}")
    print(f"  - API Key: {user.llm_api_key[:20]}... (primeros 20 caracteres)")

    print(f"\n=== RAZÓN DEL CAMBIO ===")
    print(f"NVIDIA/Llama rechazaba preguntas legítimas como:")
    print(f'  - "Cuál es la oferta que más se adecúa a mi empresa?"')
    print(f'  - "Dame los puntos fuertes de cada oferta"')
    print(f"\nEstas son preguntas perfectamente legítimas de análisis de negocio.")
    print(f"Gemini es más flexible y responde apropiadamente a estas consultas.")

    print(f"\n✓ Listo! Ahora puedes usar el chat con Gemini")
    print(f"  URL: http://127.0.0.1:8001/chat/")

except User.DoesNotExist:
    print("ERROR: Usuario pepe2012 no existe")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
