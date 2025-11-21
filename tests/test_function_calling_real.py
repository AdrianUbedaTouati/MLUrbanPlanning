"""
Test de integración real del sistema de Function Calling.
Prueba con Ollama, retriever real y base de datos Django.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from agent_ia_core.agent_function_calling import FunctionCallingAgent
from agent_ia_core.indexing.retriever import create_retriever
from django.db import connection


def test_function_calling_agent():
    """Test completo del agente con function calling."""

    print("\n" + "="*80)
    print("TEST: Function Calling Agent con Ollama")
    print("="*80)

    # Inicializar retriever
    print("\n[SETUP] Inicializando retriever...")
    retriever = create_retriever(
        k=6,
        provider='ollama',
        api_key=None,
        embedding_model='nomic-embed-text'
    )
    print("[SETUP] OK Retriever inicializado")

    # Inicializar agente
    print("\n[SETUP] Inicializando FunctionCallingAgent...")
    agent = FunctionCallingAgent(
        llm_provider='ollama',
        llm_model='qwen2.5:7b',
        llm_api_key=None,
        retriever=retriever,
        db_session=None,  # Usará conexión default
        max_iterations=5,
        temperature=0.3
    )
    print(f"[SETUP] OK Agente inicializado: {agent}")
    print(f"[SETUP] Tools disponibles: {agent.tool_registry.get_tool_names()}")

    # ==========================================================================
    # TEST 1: Búsqueda simple con search_tenders
    # ==========================================================================
    print("\n\n" + "#"*80)
    print("# TEST 1: Búsqueda simple - 'busca licitaciones de software'")
    print("#"*80)

    result1 = agent.query("busca licitaciones de software")

    print(f"\n[RESULTADO TEST 1]:")
    print(f"   Respuesta: {result1['answer'][:200]}...")
    print(f"   Tools usadas: {result1['tools_used']}")
    print(f"   Iteraciones: {result1['iterations']}")
    print(f"   Metadata: {result1['metadata']}")

    # ==========================================================================
    # TEST 2: Búsqueda por presupuesto con find_by_budget
    # ==========================================================================
    print("\n\n" + "#"*80)
    print("# TEST 2: Búsqueda por presupuesto - 'dame la licitación con más dinero'")
    print("#"*80)

    result2 = agent.query("dame la licitación con más dinero")

    print(f"\n[RESULTADO TEST 2]:")
    print(f"   Respuesta: {result2['answer'][:200]}...")
    print(f"   Tools usadas: {result2['tools_used']}")
    print(f"   Iteraciones: {result2['iterations']}")

    # ==========================================================================
    # TEST 3: Detalles específicos con get_tender_details
    # ==========================================================================
    print("\n\n" + "#"*80)
    print("# TEST 3: Detalles - 'dame todos los detalles de la primera'")
    print("#"*80)

    # Simular conversación: primero buscar, luego pedir detalles
    history = [
        {'role': 'user', 'content': 'busca licitaciones de software'},
        {'role': 'assistant', 'content': result1['answer']}
    ]

    result3 = agent.query(
        "dame todos los detalles de la primera licitación",
        conversation_history=history
    )

    print(f"\n[RESULTADO TEST 3]:")
    print(f"   Respuesta: {result3['answer'][:200]}...")
    print(f"   Tools usadas: {result3['tools_used']}")
    print(f"   Iteraciones: {result3['iterations']}")

    # ==========================================================================
    # TEST 4: Consulta compleja que requiere múltiples tools
    # ==========================================================================
    print("\n\n" + "#"*80)
    print("# TEST 4: Consulta compleja - 'busca licitaciones de software con más de 500k euros'")
    print("#"*80)

    result4 = agent.query("busca licitaciones de software con más de 500000 euros")

    print(f"\n[RESULTADO TEST 4]:")
    print(f"   Respuesta: {result4['answer'][:200]}...")
    print(f"   Tools usadas: {result4['tools_used']}")
    print(f"   Iteraciones: {result4['iterations']}")

    # ==========================================================================
    # RESUMEN FINAL
    # ==========================================================================
    print("\n\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)

    tests_results = [
        ("TEST 1: Búsqueda simple", result1),
        ("TEST 2: Por presupuesto", result2),
        ("TEST 3: Detalles con historial", result3),
        ("TEST 4: Consulta compleja", result4)
    ]

    for name, result in tests_results:
        status = "[PASS]" if result['answer'] and not result['answer'].startswith('Lo siento') else "[FAIL]"
        print(f"{status} | {name}")
        print(f"       Tools: {', '.join(result['tools_used']) if result['tools_used'] else 'ninguna'}")
        print(f"       Iteraciones: {result['iterations']}")

    print("\n" + "="*80)
    print("TESTS COMPLETADOS")
    print("="*80)


if __name__ == "__main__":
    try:
        test_function_calling_agent()
    except Exception as e:
        print(f"\n[ERROR FATAL]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
