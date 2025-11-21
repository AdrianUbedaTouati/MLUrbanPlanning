# -*- coding: utf-8 -*-
"""
Test del sistema de revisión LLM
Verifica que el bucle de mejora funcione correctamente
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.chat.response_reviewer import ResponseReviewer
from apps.authentication.models import User


def test_reviewer_initialization():
    """Test 1: Verificar que ResponseReviewer se puede inicializar"""
    print("\n" + "="*80)
    print("TEST 1: Inicialización de ResponseReviewer")
    print("="*80)

    try:
        # Obtener un usuario con API key configurada
        user = User.objects.filter(llm_api_key__isnull=False).first()

        if not user:
            print("[FAIL] No hay usuarios con API key configurada")
            return False

        print(f"[OK] Usuario encontrado: {user.email}")
        print(f"[OK] Proveedor: {user.llm_provider}")

        # Crear un LLM mock para testing
        from langchain_google_genai import ChatGoogleGenerativeAI

        if user.llm_provider == 'google':
            llm = ChatGoogleGenerativeAI(
                model='gemini-2.0-flash-exp',
                google_api_key=user.llm_api_key,
                temperature=0.3
            )
        else:
            print(f"⚠️ Proveedor {user.llm_provider} no soportado en este test, usando Gemini por defecto")
            # Aquí podrías añadir soporte para otros providers
            return False

        # Crear reviewer
        reviewer = ResponseReviewer(llm)
        print(f"✓ ResponseReviewer creado correctamente")

        return True

    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_review_response():
    """Test 2: Verificar que review_response funciona con una respuesta real"""
    print("\n" + "="*80)
    print("TEST 2: Revisión de una respuesta de prueba")
    print("="*80)

    try:
        # Obtener usuario
        user = User.objects.filter(llm_api_key__isnull=False, llm_provider='google').first()

        if not user:
            print("❌ No hay usuarios con Gemini configurado")
            return False

        # Crear LLM
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model='gemini-2.0-flash-exp',
            google_api_key=user.llm_api_key,
            temperature=0.3
        )

        # Crear reviewer
        reviewer = ResponseReviewer(llm)

        # Respuesta de prueba (MAL FORMATEADA - debería detectar problemas)
        bad_response = """Aquí están las licitaciones que encontré:

1. Licitación de servicios informáticos - Presupuesto: 500000 EUR
2. Licitación de mantenimiento de software - Presupuesto: 250000 EUR
3. Licitación de desarrollo web - Presupuesto: 100000 EUR

Estas son las que más te pueden interesar."""

        # Metadata de prueba
        metadata = {
            'documents_used': [
                {'id': '00668461-2025', 'section': 'title'},
                {'id': '00668462-2025', 'section': 'description'}
            ],
            'tools_used': ['search_by_cpv'],
            'route': 'vectorstore'
        }

        # Ejecutar revisión
        print("\n[REVIEWER] Llamando a review_response()...")
        review_result = reviewer.review_response(
            user_question="Dame las mejores licitaciones para desarrollo de software",
            conversation_history=[],
            initial_response=bad_response,
            metadata=metadata
        )

        print(f"\n[RESULTADO]")
        print(f"Status: {review_result['status']}")
        print(f"Score: {review_result['score']}/100")
        print(f"\nIssues ({len(review_result['issues'])}):")
        for issue in review_result['issues']:
            print(f"  - {issue}")
        print(f"\nSuggestions ({len(review_result['suggestions'])}):")
        for suggestion in review_result['suggestions']:
            print(f"  - {suggestion}")

        if review_result['feedback']:
            print(f"\nFeedback:")
            print(f"  {review_result['feedback']}")

        # Verificar que detectó problemas (debería tener NEEDS_IMPROVEMENT)
        if review_result['status'] == 'NEEDS_IMPROVEMENT':
            print(f"\n✓ Revisor detectó problemas correctamente")
            return True
        else:
            print(f"\n⚠️ Revisor aprobó una respuesta con formato incorrecto (esperábamos NEEDS_IMPROVEMENT)")
            return False

    except Exception as e:
        print(f"❌ Error en revisión: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_good_response():
    """Test 3: Verificar que una respuesta bien formateada se aprueba"""
    print("\n" + "="*80)
    print("TEST 3: Revisión de una respuesta CORRECTA")
    print("="*80)

    try:
        # Obtener usuario
        user = User.objects.filter(llm_api_key__isnull=False, llm_provider='google').first()

        if not user:
            print("❌ No hay usuarios con Gemini configurado")
            return False

        # Crear LLM
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model='gemini-2.0-flash-exp',
            google_api_key=user.llm_api_key,
            temperature=0.3
        )

        # Crear reviewer
        reviewer = ResponseReviewer(llm)

        # Respuesta de prueba (BIEN FORMATEADA)
        good_response = """Basándome en tu perfil y las licitaciones disponibles, te recomiendo:

## Servicios informáticos para SAP - ID: 00668461-2025

**Por qué es la más adecuada:**
- El presupuesto de 500.000 EUR es ideal para empresas de tu tamaño
- Tu experiencia en desarrollo de software coincide con el CPV 72267100
- Plazo de 45 días, lo que te da tiempo suficiente para preparar una propuesta sólida

**Análisis de fit:**
- **Presupuesto:** 500.000 EUR - Adecuado para tu capacidad financiera actual
- **Plazo:** 15/03/2025 - Holgado, permite preparación detallada
- **Coincidencia con perfil:** 95% (CPV match + sector tecnología)

**Datos clave:**
- **Organismo:** Ministerio de Economía
- **CPV:** 72267100 - Servicios de software empresarial
- **Presupuesto:** 500.000 EUR
- **Plazo límite:** 15 de marzo de 2025
- **Tipo contrato:** Servicios

[ID: 00668461-2025 | title]"""

        # Metadata de prueba
        metadata = {
            'documents_used': [
                {'id': '00668461-2025', 'section': 'title'}
            ],
            'tools_used': ['get_company_info', 'search_by_cpv'],
            'route': 'vectorstore'
        }

        # Ejecutar revisión
        print("\n[REVIEWER] Llamando a review_response()...")
        review_result = reviewer.review_response(
            user_question="Dame la mejor licitación para mi empresa",
            conversation_history=[],
            initial_response=good_response,
            metadata=metadata
        )

        print(f"\n[RESULTADO]")
        print(f"Status: {review_result['status']}")
        print(f"Score: {review_result['score']}/100")

        # Verificar que aprobó la respuesta
        if review_result['status'] == 'APPROVED':
            print(f"\n✓ Revisor aprobó respuesta bien formateada correctamente")
            return True
        else:
            print(f"\n⚠️ Revisor rechazó una respuesta correcta (esperábamos APPROVED)")
            print(f"Issues: {review_result['issues']}")
            return False

    except Exception as e:
        print(f"❌ Error en revisión: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*80)
    print("TESTING SISTEMA DE REVISIÓN LLM")
    print("="*80)

    results = []

    # Test 1: Inicialización
    results.append(("Inicialización", test_reviewer_initialization()))

    # Test 2: Revisión de respuesta mala
    results.append(("Revisión respuesta mala", test_review_response()))

    # Test 3: Revisión de respuesta buena
    results.append(("Revisión respuesta buena", test_good_response()))

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests pasados")

    if passed == total:
        print("\n🎉 TODOS LOS TESTS PASARON!")
    else:
        print(f"\n⚠️ {total - passed} tests fallaron")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
