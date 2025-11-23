"""
Management command para re-parsear información de contacto de licitaciones existentes.

Uso:
    python manage.py reparse_contacts

Este comando:
1. Lee cada licitación de la base de datos
2. Re-parsea el XML original usando EFormsXMLParser
3. Actualiza los campos de contacto (email, phone, url, fax)
4. Establece indexed_at con la fecha actual
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

# Add agent_ia_core to path
agent_ia_path = os.path.join(settings.BASE_DIR, 'agent_ia_core')
if agent_ia_path not in sys.path:
    sys.path.insert(0, agent_ia_path)

from apps.tenders.models import Tender
from xml_parser import parse_eforms_xml


class Command(BaseCommand):
    help = 'Re-parsea información de contacto de licitaciones existentes usando EFormsXMLParser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué cambios se harían sin aplicarlos',
        )
        parser.add_argument(
            '--tender-id',
            type=str,
            help='Re-parsear solo una licitación específica (ej: 715887-2025)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_tender_id = options.get('tender_id')

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('RE-PARSEO DE INFORMACIÓN DE CONTACTO'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se guardarán cambios'))

        # Obtener licitaciones a procesar
        if specific_tender_id:
            tenders = Tender.objects.filter(ojs_notice_id=specific_tender_id)
            if not tenders.exists():
                self.stdout.write(self.style.ERROR(f'ERROR Licitacion {specific_tender_id} no encontrada'))
                return
        else:
            tenders = Tender.objects.all()

        total = tenders.count()
        self.stdout.write(f'\nTotal de licitaciones a procesar: {total}\n')

        # Contadores
        updated = 0
        no_changes = 0
        errors = 0
        no_xml = 0

        for tender in tenders:
            tender_id = tender.ojs_notice_id

            try:
                # Verificar que existe el archivo XML
                if not tender.source_path:
                    self.stdout.write(self.style.WARNING(f'WARNING {tender_id}: Sin source_path, buscando en data/xml/'))
                    # Intentar construir la ruta
                    xml_path = Path(settings.BASE_DIR) / 'data' / 'xml' / f'{tender_id}.xml'
                    if not xml_path.exists():
                        self.stdout.write(self.style.ERROR(f'ERROR {tender_id}: XML no encontrado'))
                        no_xml += 1
                        continue
                else:
                    xml_path = Path(tender.source_path)
                    if not xml_path.exists():
                        self.stdout.write(self.style.ERROR(f'ERROR {tender_id}: XML no encontrado en {xml_path}'))
                        no_xml += 1
                        continue

                # Parsear XML usando EFormsXMLParser
                self.stdout.write(f'Procesando {tender_id}...')
                parsed_data = parse_eforms_xml(xml_path)

                # Extraer campos de contacto desde OPTIONAL
                optional = parsed_data.get('OPTIONAL', {})
                contact_email = optional.get('contact_email', '')
                contact_phone = optional.get('contact_phone', '')
                contact_url = optional.get('contact_url', '')
                contact_fax = optional.get('contact_fax', '')

                # Verificar si hay cambios
                has_changes = False
                changes = []

                if contact_email and contact_email != tender.contact_email:
                    changes.append(f'email: "{tender.contact_email}" -> "{contact_email}"')
                    has_changes = True

                if contact_phone and contact_phone != tender.contact_phone:
                    changes.append(f'phone: "{tender.contact_phone}" -> "{contact_phone}"')
                    has_changes = True

                if contact_url and contact_url != tender.contact_url:
                    changes.append(f'url: "{tender.contact_url}" -> "{contact_url}"')
                    has_changes = True

                if contact_fax and contact_fax != tender.contact_fax:
                    changes.append(f'fax: "{tender.contact_fax}" -> "{contact_fax}"')
                    has_changes = True

                if has_changes:
                    self.stdout.write(self.style.SUCCESS(f'  OK {tender_id}: Cambios detectados'))
                    for change in changes:
                        self.stdout.write(f'    - {change}')

                    if not dry_run:
                        # Actualizar campos
                        tender.contact_email = contact_email or tender.contact_email
                        tender.contact_phone = contact_phone or tender.contact_phone
                        tender.contact_url = contact_url or tender.contact_url
                        tender.contact_fax = contact_fax or tender.contact_fax
                        tender.indexed_at = timezone.now()
                        tender.save(update_fields=[
                            'contact_email',
                            'contact_phone',
                            'contact_url',
                            'contact_fax',
                            'indexed_at'
                        ])
                        self.stdout.write(self.style.SUCCESS(f'  OK {tender_id}: Guardado'))

                    updated += 1
                else:
                    self.stdout.write(f'  - {tender_id}: Sin cambios (ya tiene la info o XML sin contactos)')
                    no_changes += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR {tender_id}: Error - {str(e)}'))
                errors += 1
                # Imprimir traceback completo en modo verbose
                import traceback
                traceback.print_exc()

        # Resumen
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE RE-PARSEO'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total procesadas:    {total}')
        self.stdout.write(self.style.SUCCESS(f'Actualizadas:        {updated}'))
        self.stdout.write(f'Sin cambios:         {no_changes}')
        self.stdout.write(self.style.ERROR(f'Errores:             {errors}'))
        self.stdout.write(self.style.WARNING(f'Sin XML:             {no_xml}'))
        self.stdout.write('=' * 80)

        if dry_run:
            self.stdout.write(self.style.WARNING('\nMODO DRY-RUN: Ejecuta sin --dry-run para aplicar cambios'))
