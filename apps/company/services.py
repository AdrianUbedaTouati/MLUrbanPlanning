"""
Service layer for Company Profile operations
Includes AI-powered auto-completion of profile fields using centralized prompts configuration
"""
import os
from typing import Dict, Any, List
from django.conf import settings


class CompanyProfileAIService:
    """Service to extract company information from free text using LLM"""

    def __init__(self, user):
        """
        Initialize service with user's API key

        Args:
            user: Django User instance with llm_api_key
        """
        self.user = user
        self.api_key = user.llm_api_key

    def extract_company_info(self, company_text: str) -> Dict[str, Any]:
        """
        Extract structured company information from free text using LLM.
        Uses centralized prompts configuration from agent_ia_core/prompts_config.py

        Args:
            company_text: Free text description of the company

        Returns:
            Dict with extracted fields:
                - company_name: str
                - employees: int
                - preferred_cpv_codes: List[str] (códigos CPV de sectores/actividad)
                - preferred_nuts_regions: List[str]
                - budget_min: int
                - budget_max: int
        """
        if not self.api_key:
            raise ValueError("No API key configured for this user")

        if not company_text or company_text.strip() == '':
            raise ValueError("Company text cannot be empty")

        try:
            # Import LangChain components
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain.prompts import ChatPromptTemplate
            from langchain.output_parsers import PydanticOutputParser
            from pydantic import BaseModel, Field

            # Import centralized configuration
            from agent_ia_core.prompts_config import (
                COMPANY_INFO_EXTRACTION_PROMPT,
                EXTRACTION_TEMPERATURE,
                EXTRACTION_MODEL,
                CPV_CODE_KEYWORDS,
                SPAIN_NUTS_MAPPING
            )

            # Define simplified output schema (only essential fields)
            class CompanyInfoExtraction(BaseModel):
                company_name: str = Field(description="Nombre de la empresa")
                employees: int = Field(
                    default=0,
                    description="Número aproximado de empleados"
                )
                preferred_cpv_codes: List[str] = Field(
                    default_factory=list,
                    description="Códigos CPV de 4 dígitos relacionados con los sectores y actividad de la empresa (ej: 7226 para software, 4500 para construcción, 7210 para consultoría). Identifica los sectores de la empresa y devuelve los códigos CPV correspondientes."
                )
                preferred_nuts_regions: List[str] = Field(
                    default_factory=list,
                    description="Códigos NUTS de regiones donde opera (ej: ES30 para Madrid, ES51 para Cataluña)"
                )
                budget_min: int = Field(
                    default=50000,
                    description="Presupuesto mínimo de proyectos en EUR"
                )
                budget_max: int = Field(
                    default=500000,
                    description="Presupuesto máximo de proyectos en EUR"
                )

            # Create parser
            parser = PydanticOutputParser(pydantic_object=CompanyInfoExtraction)

            # Create prompt using centralized template
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", COMPANY_INFO_EXTRACTION_PROMPT + "\n\n{format_instructions}"),
                ("human", "{company_text}")
            ])

            # Create LLM with centralized configuration
            llm = ChatGoogleGenerativeAI(
                model=EXTRACTION_MODEL,
                google_api_key=self.api_key,
                temperature=EXTRACTION_TEMPERATURE
            )

            # Create chain
            chain = prompt_template | llm | parser

            # Execute
            result = chain.invoke({
                "company_text": company_text,
                "format_instructions": parser.get_format_instructions()
            })

            # Convert to dict
            extracted_data = result.dict()

            return extracted_data

        except ImportError as e:
            raise Exception(f"Error importing LangChain components: {e}. "
                          "Make sure langchain and langchain-google-genai are installed.")
        except Exception as e:
            raise Exception(f"Error extracting company information: {e}")

    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data

        Args:
            data: Extracted data dict

        Returns:
            Validated and cleaned data
        """
        # Ensure lists are unique and not empty
        for key in ['preferred_cpv_codes', 'preferred_nuts_regions']:
            if key in data and isinstance(data[key], list):
                # Remove duplicates and empty strings
                data[key] = list(set(filter(None, data[key])))

        # Ensure numeric fields are positive
        if 'employees' in data:
            data['employees'] = max(0, data.get('employees', 0))

        if 'budget_min' in data:
            data['budget_min'] = max(0, data.get('budget_min', 50000))

        if 'budget_max' in data:
            data['budget_max'] = max(0, data.get('budget_max', 500000))

        # Ensure budget_min <= budget_max
        if data.get('budget_min', 0) > data.get('budget_max', 0):
            # Swap if inverted
            data['budget_min'], data['budget_max'] = data['budget_max'], data['budget_min']

        # Ensure CPV codes are 4 digits
        if 'preferred_cpv_codes' in data:
            valid_cpv_codes = []
            for code in data['preferred_cpv_codes']:
                # Extract only digits
                digits = ''.join(filter(str.isdigit, str(code)))
                if digits:
                    # Take first 4 digits
                    valid_cpv_codes.append(digits[:4])
            data['preferred_cpv_codes'] = list(set(valid_cpv_codes))

        return data
