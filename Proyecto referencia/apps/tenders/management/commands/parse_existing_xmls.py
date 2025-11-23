# -*- coding: utf-8 -*-
"""
Management command para parsear XMLs de licitaciones existentes y guardar parsed_summary
"""
from django.core.management.base import BaseCommand
from apps.tenders.models import Tender
from lxml import etree
import io
from pathlib import Path
import sys
import os
from django.conf import settings

# Add agent_ia_core to Python path
agent_ia_path = os.path.join(settings.BASE_DIR, 'agent_ia_core')
if agent_ia_path not in sys.path:
    sys.path.insert(0, agent_ia_path)


class Command(BaseCommand):
    help = 'Parsea los XMLs de licitaciones existentes y guarda el parsed_summary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limitar número de licitaciones a procesar'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar reprocesamiento de licitaciones que ya tienen parsed_summary'
        )

    def handle(self, *args, **options):
        from agent_ia_core.parser.xml_parser import EFormsXMLParser

        limit = options.get('limit')
        force = options.get('force')

        # Obtener licitaciones con XML
        tenders_query = Tender.objects.exclude(xml_content='').exclude(xml_content__isnull=True)

        if not force:
            # Solo procesar las que no tienen parsed_summary
            tenders_query = tenders_query.filter(parsed_summary={})

        if limit:
            tenders = tenders_query[:limit]
        else:
            tenders = tenders_query

        total = tenders.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay licitaciones para procesar'))
            return

        self.stdout.write(self.style.SUCCESS(f'Procesando {total} licitaciones...'))

        parser_instance = EFormsXMLParser()
        success_count = 0
        error_count = 0

        for idx, tender in enumerate(tenders, 1):
            try:
                # Parse XML
                tree = etree.parse(io.BytesIO(tender.xml_content.encode('utf-8')))
                root = tree.getroot()

                # Extract fields
                parsed_data = {
                    "REQUIRED": parser_instance._extract_required_fields(root, Path(f"{tender.ojs_notice_id}.xml")),
                    "OPTIONAL": parser_instance._extract_optional_fields(root),
                    "META": parser_instance._extract_meta_fields()
                }

                # Save to database
                tender.parsed_summary = parsed_data
                tender.save(update_fields=['parsed_summary'])

                success_count += 1
                self.stdout.write(f'  [{idx}/{total}] OK {tender.ojs_notice_id}')

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  [{idx}/{total}] ERROR {tender.ojs_notice_id}: {str(e)}'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Completado: {success_count} exitosos, {error_count} errores'))
