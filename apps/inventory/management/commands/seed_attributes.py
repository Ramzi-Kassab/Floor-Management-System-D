"""
Seed command for Attributes from comprehensive CSV file.

Usage:
    python manage.py seed_attributes           # Add/update only
    python manage.py seed_attributes --replace # Replace all (delete attrs not in CSV)
"""
import csv
import os
from django.core.management.base import BaseCommand
from apps.inventory.models import Attribute


class Command(BaseCommand):
    help = "Seed attributes from comprehensive CSV file"

    # Map CSV data types to model DataType choices
    DATA_TYPE_MAP = {
        "text": "text",
        "decimal": "decimal",
        "number": "number",
        "boolean": "boolean",
        "date": "date",
        "select": "select",
        "enum": "enum",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace mode: delete attributes not in CSV file',
        )

    def handle(self, *args, **options):
        replace_mode = options.get('replace', False)

        if replace_mode:
            self.stdout.write(self.style.WARNING("Running in REPLACE mode - attributes not in CSV will be deleted"))
        else:
            self.stdout.write("Seeding Attributes from CSV (add/update only)...\n")

        csv_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', '..',
            'docs', 'development', 'attributes_comprehensive.csv'
        )
        csv_path = os.path.normpath(csv_path)

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return

        created_count = 0
        updated_count = 0
        csv_codes = set()
        classification_counts = {}

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                code = row.get('Attribute Code', '').strip()
                if not code:
                    continue  # Skip empty rows

                csv_codes.add(code)
                classification_code = row.get('Classification Code', '').strip()
                name = row.get('Attribute Name', '').strip()
                description = row.get('Description', '').strip()
                data_type = row.get('Data Type', 'text').strip().lower()
                notes = row.get('Notes', '').strip()

                # Map data type
                data_type = self.DATA_TYPE_MAP.get(data_type, "text")

                # Validate classification code
                valid_classifications = [c[0] for c in Attribute.Classification.choices]
                if classification_code not in valid_classifications:
                    classification_code = "GEN"

                # Track counts by classification
                if classification_code not in classification_counts:
                    classification_counts[classification_code] = 0

                # Create or update the attribute
                attr, created = Attribute.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "description": description,
                        "classification": classification_code,
                        "data_type": data_type,
                        "notes": notes,
                        "is_active": True,
                    }
                )

                classification_counts[classification_code] += 1

                if created:
                    created_count += 1
                    self.stdout.write(f"  Created: [{classification_code}] {code} - {name}")
                else:
                    updated_count += 1
                    self.stdout.write(f"  Updated: [{classification_code}] {code} - {name}")

        # In replace mode, delete attributes not in CSV
        deleted_count = 0
        if replace_mode:
            attrs_to_delete = Attribute.objects.exclude(code__in=csv_codes)
            deleted_count = attrs_to_delete.count()
            if deleted_count > 0:
                self.stdout.write(self.style.WARNING(f"\nDeleting {deleted_count} attributes not in CSV:"))
                for attr in attrs_to_delete:
                    self.stdout.write(f"  Deleted: {attr.code} - {attr.name}")
                attrs_to_delete.delete()

        # Print summary by classification
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Attributes by Classification:")
        for classification, count in sorted(classification_counts.items()):
            label = dict(Attribute.Classification.choices).get(classification, classification)
            self.stdout.write(f"  {classification}: {count} ({label})")

        total = Attribute.objects.count()
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created: {created_count}, Updated: {updated_count}, Deleted: {deleted_count}, Total: {total}"
        ))
