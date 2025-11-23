# -*- coding: utf-8 -*-
"""
Tool para análisis de CV con IA.
Extrae información estructurada del curriculum del usuario.
"""

import json
import logging
from typing import Any
from ..core.base import BaseTool

logger = logging.getLogger(__name__)


class CVAnalyzerTool(BaseTool):
    """Analiza un CV y extrae información estructurada."""

    name = "analyze_cv"
    description = """Analiza el texto de un CV y extrae información estructurada.
    Extrae: habilidades, experiencia laboral, formación, idiomas y genera un resumen profesional.
    Usar cuando el usuario sube o pega su CV para crear su perfil."""

    def __init__(self, llm=None):
        self.llm = llm
        super().__init__()

    def get_schema(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'cv_text': {
                        'type': 'string',
                        'description': 'Texto completo del CV a analizar'
                    }
                },
                'required': ['cv_text']
            }
        }

    def run(self, cv_text: str) -> dict:
        """Analiza el CV y extrae datos estructurados."""
        if not cv_text or len(cv_text.strip()) < 50:
            return {
                'success': False,
                'error': 'El texto del CV es demasiado corto. Por favor proporciona más información.'
            }

        prompt = f"""Analiza el siguiente CV y extrae la información en formato JSON estructurado.

CV:
{cv_text}

Extrae la siguiente información en formato JSON:
{{
    "skills": ["lista de habilidades técnicas y blandas"],
    "experience": [
        {{
            "company": "nombre empresa",
            "position": "puesto",
            "duration": "período (ej: 2020-2023)",
            "description": "breve descripción de responsabilidades"
        }}
    ],
    "education": [
        {{
            "institution": "nombre institución",
            "degree": "título obtenido",
            "year": "año de finalización"
        }}
    ],
    "languages": [
        {{
            "language": "idioma",
            "level": "nivel (Nativo, Avanzado, Intermedio, Básico)"
        }}
    ],
    "professional_summary": "Resumen profesional de 2-3 frases destacando fortalezas y experiencia",
    "preferred_sectors": ["sectores donde encaja mejor el perfil"],
    "suggested_job_titles": ["posibles títulos de trabajo a buscar"]
}}

IMPORTANTE:
- Si no encuentras información para algún campo, usa una lista vacía []
- Los skills deben ser específicos y concretos
- El resumen debe ser en primera persona y profesional
- Responde SOLO con el JSON, sin texto adicional"""

        try:
            if self.llm:
                response = self.llm.invoke(prompt)
                result_text = response.content if hasattr(response, 'content') else str(response)

                # Limpiar respuesta para obtener solo JSON
                result_text = result_text.strip()
                if result_text.startswith("```"):
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]

                # Validar que es JSON válido
                parsed = json.loads(result_text)
                return {
                    'success': True,
                    'data': parsed
                }
            else:
                return {
                    'success': False,
                    'error': 'LLM no configurado para análisis de CV'
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta JSON del CV: {e}")
            return {
                'success': False,
                'error': f'Error al procesar la respuesta del análisis: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error analizando CV: {e}")
            return {
                'success': False,
                'error': f'Error analizando CV: {str(e)}'
            }
