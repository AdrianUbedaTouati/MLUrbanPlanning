# -*- coding: utf-8 -*-
"""
Comando de Django para exportar XMLs desde la BD a archivos físicos.
Uso: python manage.py export_xmls
"""

from django.core.management.base import BaseCommand
from apps.tenders.models import Tender
from pathlib import Path
from agent_ia_core.config import XML_DIR


class Command(BaseCommand):
    help = 'Exporta los XMLs guardados en la BD a archivos en data/xml/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Sobrescribir archivos existentes',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']

        # Obtener licitaciones con XML
        tenders = Tender.objects.exclude(xml_content='').exclude(xml_content__isnull=True)
        total = tenders.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No hay licitaciones con XML para exportar.'))
            return

        self.stdout.write(f'Encontradas {total} licitaciones con XML')
        self.stdout.write(f'Directorio destino: {XML_DIR}')

        # Crear directorio si no existe
        XML_DIR.mkdir(parents=True, exist_ok=True)

        exported = 0
        skipped = 0
        errors = 0

        for tender in tenders:
            try:
                # Nombre del archivo
                filename = f"{tender.ojs_notice_id}.xml"
                filepath = XML_DIR / filename

                # Verificar si ya existe
                if filepath.exists() and not overwrite:
                    self.stdout.write(
                        self.style.WARNING(f'OMITIDO (ya existe): {filename}')
                    )
                    skipped += 1
                    continue

                # Guardar XML
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(tender.xml_content)

                # Actualizar source_path en la BD
                tender.source_path = str(filepath)
                tender.save(update_fields=['source_path'])

                self.stdout.write(
                    self.style.SUCCESS(f'OK Exportado: {filename} ({len(tender.xml_content)} bytes)')
                )
                exported += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'ERROR en {tender.ojs_notice_id}: {str(e)}')
                )
                errors += 1

        # Resumen
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(f'EXPORTACION COMPLETADA')
        self.stdout.write(f'   - Exportados: {exported}')
        if skipped > 0:
            self.stdout.write(f'   - Omitidos: {skipped}')
        if errors > 0:
            self.stdout.write(f'   - Errores: {errors}')
        self.stdout.write('=' * 60)
