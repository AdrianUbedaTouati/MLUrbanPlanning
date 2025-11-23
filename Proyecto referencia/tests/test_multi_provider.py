# -*- coding: utf-8 -*-
"""
Test de validación para Function Calling con múltiples proveedores.

IMPORTANTE: Requiere API keys configuradas:
- OpenAI: export OPENAI_API_KEY='sk-...'
- Gemini: export GOOGLE_API_KEY='AIza...'

Para Ollama: Asegúrate de tener Ollama ejecutándose (ollama serve)
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from agent_ia_core.agent_function_calling import FunctionCallingAgent
from agent_ia_core.indexing.retriever import create_retriever


def test_provider(provider: str, model: str, api_key: str = None):
    """
    Prueba el Function Calling con un proveedor específico.

    Args:
        provider: 'ollama', 'openai', 'google'
        model: Nombre del modelo
        api_key: API key (None para Ollama)
    """
    print("\n" + "="*80)
    print(f"TEST: {provider.upper()} - {model}")
    print("="*80)

    try:
        # Crear retriever
        print(f"\n[1/5] Creando retriever...")
        retriever = create_retriever(
            k=3,
            provider='ollama' if provider == 'ollama' else provider,
            api_key=None if provider == 'ollama' else api_key,
            embedding_model='nomic-embed-text' if provider == 'ollama' else None
        )
        print(f"✓ Retriever creado")

        # Crear agente
        print(f"\n[2/5] Creando FunctionCallingAgent...")
        agent = FunctionCallingAgent(
            llm_provider=provider,
            llm_model=model,
            llm_api_key=api_key,
            retriever=retriever,
            temperature=0.3
        )
        print(f"✓ Agente creado con {len(agent.tool_registry.tools)} tools")

        # Test 1: Búsqueda simple
        print(f"\n[3/5] Test 1: Búsqueda simple")
        result1 = agent.query("busca licitaciones de tecnología")
        print(f"  Respuesta: {result1['answer'][:100]}...")
        print(f"  Tools usadas: {result1['tools_used']}")
        print(f"  Iterations: {result1['iterations']}")

        # Test 2: Filtrado por presupuesto
        print(f"\n[4/5] Test 2: Filtrado por presupuesto")
        result2 = agent.query("dame licitaciones con presupuesto mayor a 50000 euros")
        print(f"  Respuesta: {result2['answer'][:100]}...")
        print(f"  Tools usadas: {result2['tools_used']}")
        print(f"  Iterations: {result2['iterations']}")

        # Test 3: Estadísticas
        print(f"\n[5/5] Test 3: Estadísticas")
        result3 = agent.query("cuántas licitaciones hay en total?")
        print(f"  Respuesta: {result3['answer'][:100]}...")
        print(f"  Tools usadas: {result3['tools_used']}")
        print(f"  Iterations: {result3['iterations']}")

        # Verificaciones
        print(f"\n[VERIFICACIÓN]")
        assert len(result1['tools_used']) > 0, "No se usaron tools en Test 1"
        assert len(result2['tools_used']) > 0, "No se usaron tools en Test 2"
        assert 'get_statistics' in result3['tools_used'], "get_statistics no usada en Test 3"

        print(f"✅ Todas las verificaciones pasaron")
        print(f"\n{'='*80}")
        print(f"✅ {provider.upper()} - TESTS COMPLETADOS CON ÉXITO")
        print(f"{'='*80}\n")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n{'='*80}")
        print(f"❌ {provider.upper()} - TESTS FALLIDOS")
        print(f"{'='*80}\n")
        return False


def main():
    """Ejecuta tests para todos los proveedores configurados."""
    print("\n" + "="*80)
    print("TESTS DE FUNCTION CALLING MULTI-PROVEEDOR")
    print("="*80)

    results = {}

    # Test 1: Ollama (siempre disponible)
    print("\n🚀 Iniciando tests de Ollama...")
    results['ollama'] = test_provider('ollama', 'qwen2.5:7b', None)

    # Test 2: OpenAI (si hay API key)
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("\n🚀 Iniciando tests de OpenAI...")
        results['openai'] = test_provider('openai', 'gpt-4o-mini', openai_key)
    else:
        print("\n⏸️  Saltando tests de OpenAI (No API key configurada)")
        print("   Para probar OpenAI: export OPENAI_API_KEY='sk-...'")
        results['openai'] = None

    # Test 3: Gemini (si hay API key)
    gemini_key = os.getenv('GOOGLE_API_KEY')
    if gemini_key:
        print("\n🚀 Iniciando tests de Gemini...")
        results['gemini'] = test_provider('google', 'gemini-2.0-flash-exp', gemini_key)
    else:
        print("\n⏸️  Saltando tests de Gemini (No API key configurada)")
        print("   Para probar Gemini: export GOOGLE_API_KEY='AIza...'")
        results['gemini'] = None

    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)

    for provider, result in results.items():
        status = "✅ PASÓ" if result else ("⏸️  SALTADO" if result is None else "❌ FALLÓ")
        print(f"{provider.upper():10} : {status}")

    print("="*80)

    # Determinar si todos los tests disponibles pasaron
    tested_results = [r for r in results.values() if r is not None]
    if tested_results and all(tested_results):
        print("\n✅ TODOS LOS TESTS DISPONIBLES PASARON")
        return 0
    elif not tested_results:
        print("\n⚠️  NO SE EJECUTARON TESTS (Configura API keys)")
        return 1
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        return 1


if __name__ == "__main__":
    sys.exit(main())
