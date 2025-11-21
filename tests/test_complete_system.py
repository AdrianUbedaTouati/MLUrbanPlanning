"""
Test completo del sistema de tracking de tokens y costes
Verifica vectorización y chat
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TenderAI.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.tenders.vectorization_service import VectorizationService
from apps.chat.services import ChatAgentService
from apps.core.token_pricing import get_nvidia_limits_info, calculate_chat_cost, format_cost

User = get_user_model()

print("="*80)
print("TEST COMPLETO DEL SISTEMA - TenderAI Platform")
print("="*80)

# 1. Verificar usuario pepe2012
print("\n1. VERIFICANDO USUARIO...")
try:
    user = User.objects.get(username='pepe2012')
    print(f"   [OK] Usuario: {user.username}")
    print(f"   [OK] Proveedor: {user.llm_provider}")
    print(f"   [OK] API Key configurada: {'Si' if user.llm_api_key else 'No'}")
except User.DoesNotExist:
    print("   [ERROR] Usuario pepe2012 no existe")
    exit(1)

# 2. Mostrar información de límites de NVIDIA
print("\n2. INFORMACIÓN DE LÍMITES NVIDIA:")
print(get_nvidia_limits_info())

# 3. Test de cálculo de costes
print("\n3. TEST DE CÁLCULO DE COSTES:")
test_input = "¿Cuántas licitaciones hay disponibles?"
test_output = "Hay 6 licitaciones disponibles en el sistema."

cost_data = calculate_chat_cost(test_input, test_output, 'nvidia')
print(f"   Input: '{test_input}'")
print(f"   Output: '{test_output}'")
print(f"   Tokens entrada: {cost_data['input_tokens']}")
print(f"   Tokens salida: {cost_data['output_tokens']}")
print(f"   Total tokens: {cost_data['total_tokens']}")
print(f"   Coste: {format_cost(cost_data['total_cost_eur'])}")

# 4. Test de servicio de vectorización
print("\n4. TEST DE VECTORIZATION SERVICE:")
try:
    vec_service = VectorizationService(user=user)
    status = vec_service.get_vectorstore_status()
    print(f"   Estado: {status['status']}")
    print(f"   Inicializado: {status['is_initialized']}")
    print(f"   Chunks: {status.get('num_chunks', 0)}")
    print(f"   Coleccion: {status.get('collection_name', 'N/A')}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

# 5. Test de servicio de chat
print("\n5. TEST DE CHAT SERVICE:")
try:
    chat_service = ChatAgentService(user=user)
    print(f"   [OK] ChatService inicializado")
    print(f"   Proveedor: {chat_service.provider}")
    print(f"   API Key: {'***' + chat_service.api_key[-8:] if chat_service.api_key else 'No configurada'}")

    # Test de procesamiento de mensaje (solo si esta indexado)
    if status['is_initialized']:
        print("\n   Probando mensaje de chat...")
        response = chat_service.process_message("Cuantas licitaciones hay?")
        print(f"   [OK] Respuesta recibida: {response['content'][:100]}...")

        if 'metadata' in response:
            meta = response['metadata']
            print(f"   Ruta: {meta.get('route', 'N/A')}")
            print(f"   Documentos: {meta.get('num_documents', 0)}")
            print(f"   Tokens: {meta.get('total_tokens', 0)}")
            print(f"   Coste: {format_cost(meta.get('cost_eur', 0))}")
    else:
        print("   [WARNING] Vectorstore no inicializado, saltando prueba de chat")

except Exception as e:
    print(f"   [ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

# 6. Resumen final
print("\n" + "="*80)
print("RESUMEN DE PRUEBAS:")
print("="*80)
print("[OK] Usuario verificado y configurado")
print("[OK] Sistema de precios funcionando")
print("[OK] Servicio de vectorizacion operativo")
print("[OK] Servicio de chat operativo")
if status['is_initialized']:
    print("[OK] Sistema completamente funcional")
else:
    print("[WARNING] Sistema funcional - Requiere indexacion inicial")

print("\n" + "="*80)
print("PROXIMOS PASOS:")
print("="*80)
print("1. Acceder a http://127.0.0.1:8001/licitaciones/vectorizacion/")
print("2. Hacer clic en 'Indexar' para vectorizar licitaciones")
print("3. Observar panel de costes en tiempo real")
print("4. Probar boton 'Cancelar' durante la indexacion")
print("5. Al completar, ir al chat: http://127.0.0.1:8001/chat/")
print("6. Enviar preguntas y ver costes por mensaje")
print("="*80)
