#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para ejecutar todos los tests de JobSearchAI Platform.

Uso:
    python run_tests.py           # Ejecutar todos los tests
    python run_tests.py -v        # Modo verbose
    python run_tests.py --quick   # Solo tests rápidos (sin integración)
    python run_tests.py --tools   # Solo tests de tools
    python run_tests.py --models  # Solo tests de modelos
    python run_tests.py --views   # Solo tests de vistas
"""

import os
import sys
import argparse
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test.runner import DiscoverRunner


def print_header():
    """Imprime header del test runner"""
    print("\n" + "="*70)
    print("  JobSearchAI Platform - Test Suite")
    print("="*70)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def print_summary(result, elapsed_time):
    """Imprime resumen de resultados"""
    print("\n" + "="*70)
    print("  RESUMEN DE TESTS")
    print("="*70)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped

    print(f"  Total ejecutados: {total}")
    print(f"  [OK] Pasados: {passed}")
    print(f"  [FAIL] Fallidos: {failures}")
    print(f"  [ERR] Errores: {errors}")
    print(f"  [SKIP] Saltados: {skipped}")
    print(f"  Tiempo: {elapsed_time:.2f}s")

    if failures == 0 and errors == 0:
        print("\n  TODOS LOS TESTS PASARON!")
    else:
        print("\n  ALGUNOS TESTS FALLARON")

    print("="*70 + "\n")

    return failures + errors


def run_tests(test_labels=None, verbosity=1):
    """Ejecuta los tests"""
    import time

    print_header()

    if test_labels is None:
        test_labels = ['tests']

    print(f"Ejecutando tests: {', '.join(test_labels)}\n")

    # Configurar runner
    runner = DiscoverRunner(verbosity=verbosity, interactive=False)

    # Crear suite de tests
    suite = runner.test_loader.loadTestsFromNames(test_labels)

    # Ejecutar
    start_time = time.time()
    result = runner.run_suite(suite)
    elapsed_time = time.time() - start_time

    # Mostrar resultados
    failures = print_summary(result, elapsed_time)

    return failures


def main():
    parser = argparse.ArgumentParser(description='Ejecutar tests de JobSearchAI')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo verbose')
    parser.add_argument('--quick', action='store_true', help='Solo tests rápidos')
    parser.add_argument('--tools', action='store_true', help='Solo tests de tools')
    parser.add_argument('--models', action='store_true', help='Solo tests de modelos')
    parser.add_argument('--views', action='store_true', help='Solo tests de vistas')
    parser.add_argument('--services', action='store_true', help='Solo tests de servicios')

    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1

    # Determinar qué tests ejecutar
    test_labels = []

    if args.tools:
        test_labels.append('tests.test_tools')
    elif args.models:
        test_labels.append('tests.test_models')
    elif args.views:
        test_labels.append('tests.test_views')
    elif args.services:
        test_labels.append('tests.test_services')
    elif args.quick:
        # Tests rápidos: modelos y tools básicos
        test_labels = [
            'tests.test_models',
            'tests.test_tools.CVAnalyzerToolTest',
            'tests.test_tools.ToolRegistryTest',
        ]
    else:
        # Todos los tests
        test_labels = None

    failures = run_tests(test_labels, verbosity)

    # Exit code basado en resultados
    sys.exit(1 if failures > 0 else 0)


if __name__ == '__main__':
    main()
