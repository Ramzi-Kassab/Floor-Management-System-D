"""
Management command to import Designs from Excel file.

Reads the Items Excel file and imports RM (Raw Material) entries as Designs.
Only imports designs where the MAT number is in the provided L3 or L4 list.

Usage:
    python manage.py import_designs_excel --confirm
    python manage.py import_designs_excel --dry-run
"""

import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.technology.models import Design, BitSize


class Command(BaseCommand):
    help = "Import designs from Items Excel file (RM entries only)"

    # L3 MAT numbers - designs without cutters, upper section separate
    L3_MATS = {
        '1112857', '1134878', '1140080', '1141517', '1141549', '1141552',
        '1145822', '1145823', '1145824', '1145825', '1145826', '1145877',
        '1146009', '1153090', '1158490', '1160847', '1186940', '1187881',
        '1188084', '1188149', '1188197', '1191006', '1192557', '1197910',
        '1220553', '1221158', '1223029', '1223749', '1227237', '1228690',
        '1228723', '1228748', '1228782', '1228848', '1228896', '1229187',
        '1231398', '1234376', '1245350', '1245357', '1245431', '1246680',
        '1248668', '1251085', '1270578', '1284241', '2013684', '2016137',
        '2016920', '1146317'
    }

    # L4 MAT numbers - designs without cutters, upper section welded/machined
    L4_MATS = {
        '1145821', '1149944', '1150007', '1158011', '1192119', '1198387',
        '1198515', '1201053', '1208569', '1212881', '1217589', '1224225',
        '1228739', '1229062', '1231285', '1238258', '1239176', '1239239',
        '1239257', '1239258', '1240803', '1246020', '1255267', '1255451',
        '1257458', '1258119', '1259957', '1261236', '1262047', '1267027',
        '1267122', '1267809', '1269498', '1270617', '1270865', '1272920',
        '1281273', '1282368', '1283567', '1290130', '2000401', '2001502',
        '2009096', '2013542', '2017993', '2019988', '2022318', '2022350',
        '2025595', '2027359', '2028159', '2028515'
    }

    # Size mapping: normalize various formats to standard display and decimal
    SIZE_MAP = {
        # Fractional sizes
        '3 5/8': ('3 5/8"', Decimal('3.625')),
        '3 7/8': ('3 7/8"', Decimal('3.875')),
        '3 3/4': ('3 3/4"', Decimal('3.750')),
        '5 1/4': ('5 1/4"', Decimal('5.250')),
        '5 7/8': ('5 7/8"', Decimal('5.875')),
        '6 1/8': ('6 1/8"', Decimal('6.125')),
        '8 1/2': ('8 1/2"', Decimal('8.500')),
        '8 3/8': ('8 3/8"', Decimal('8.375')),
        '12 1/4': ('12 1/4"', Decimal('12.250')),
        # Whole numbers
        '3': ('3"', Decimal('3.000')),
        '5': ('5"', Decimal('5.000')),
        '6': ('6"', Decimal('6.000')),
        '8': ('8"', Decimal('8.000')),
        '12': ('12"', Decimal('12.000')),
        '16': ('16"', Decimal('16.000')),
        '17': ('17"', Decimal('17.000')),
        '22': ('22"', Decimal('22.000')),
        # Decimal formats
        '3.625': ('3 5/8"', Decimal('3.625')),
        '3.875': ('3 7/8"', Decimal('3.875')),
        '5.875': ('5 7/8"', Decimal('5.875')),
        '6.125': ('6 1/8"', Decimal('6.125')),
        '8.375': ('8 3/8"', Decimal('8.375')),
        '8.5': ('8 1/2"', Decimal('8.500')),
        '8.500': ('8 1/2"', Decimal('8.500')),
        '12.25': ('12 1/4"', Decimal('12.250')),
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually import the data (without this, it\'s a dry run)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )
        parser.add_argument(
            '--file',
            type=str,
            default='docs/Items_639021531472517099.xlsx',
            help='Path to Excel file'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean and trim all existing design records (removes extra spaces/hidden chars)'
        )

    def normalize_size(self, size_str):
        """Normalize size string to standard format."""
        # Remove quotes and extra spaces
        size_str = size_str.strip().replace('"', '').replace("'", '').strip()

        # Direct lookup
        if size_str in self.SIZE_MAP:
            return self.SIZE_MAP[size_str]

        # Try to parse decimal
        try:
            decimal_val = Decimal(size_str)
            # Round to 3 decimal places
            decimal_val = decimal_val.quantize(Decimal('0.001'))
            str_val = str(decimal_val)
            if str_val in self.SIZE_MAP:
                return self.SIZE_MAP[str_val]
            # Create a new entry
            return (f'{decimal_val}"', decimal_val)
        except:
            pass

        return None

    def parse_product_name(self, product_name):
        """
        Parse Product name to extract Size, HDBS Type, and MAT number.
        Primary format uses ':' as separator: 'Size : HDBS Type : MAT Number'

        Formats:
        - '3 5/8:MMD53DH:1145821' (colon separated)
        - '6 1/8: GTD54HF: 1217589' (with spaces around colons)
        - '8 3/8"GT55WUH 1134878' (legacy: no colons)
        - '16" MMD85DHF-1 1238258' (legacy: with suffix)
        """
        normalized = product_name.strip()

        # Primary method: split by colon (with optional surrounding spaces)
        if ':' in normalized:
            parts = [p.strip() for p in normalized.split(':')]
            if len(parts) >= 3:
                size_str = parts[0].replace('"', '').replace("'", '').strip()
                hdbs_type = re.sub(r'-\d+$', '', parts[1].strip())  # Remove suffix like -1
                mat_no = parts[2].strip()
                if mat_no.isdigit() and len(mat_no) >= 6:
                    return size_str, hdbs_type, mat_no
            elif len(parts) == 2:
                # Might be 'Size : HDBS MAT' format
                size_str = parts[0].replace('"', '').replace("'", '').strip()
                # Split second part by space to get HDBS and MAT
                rest = parts[1].strip().split()
                if len(rest) >= 2:
                    mat_no = rest[-1]
                    hdbs_type = re.sub(r'-\d+$', '', rest[-2])
                    if mat_no.isdigit() and len(mat_no) >= 6:
                        return size_str, hdbs_type, mat_no

        # Fallback: handle legacy format without colons (space separated)
        # Handle format like '8 3/8"GT55WUH' - add space after inch mark if followed by letter
        normalized = re.sub(r'(["\'])\s*([A-Za-z])', r'\1 \2', normalized)

        # Split by whitespace
        parts = normalized.split()

        if len(parts) < 2:
            return None, None, None

        # Find the MAT number (last numeric part, 6-7 digits)
        mat_no = None
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].isdigit() and len(parts[i]) >= 6:
                mat_no = parts[i]
                parts = parts[:i]
                break

        if not mat_no:
            return None, None, None

        # Find HDBS type (alphanumeric, before the MAT number)
        hdbs_type = None
        for i in range(len(parts) - 1, -1, -1):
            part = parts[i]
            clean_part = re.sub(r'-\d+$', '', part)  # Remove suffix like -1
            if re.match(r'^[A-Za-z]{2}[A-Za-z0-9]+$', clean_part):
                hdbs_type = clean_part
                parts = parts[:i]
                break

        if not hdbs_type:
            return None, None, mat_no

        # Remaining parts are the size - clean up quotes
        size_str = ' '.join(parts)
        size_str = size_str.replace('"', '').replace("'", '').strip()

        return size_str, hdbs_type, mat_no

    def get_category_and_body(self, item_number):
        """
        Determine category and body material from item number.
        Format: RM-{FC|RC}-{IB|MB|SB|IT|MT}-NNNN

        Returns: (category, body_material)
        """
        parts = item_number.split('-')
        if len(parts) < 3:
            return None, None

        bit_type = parts[1]  # FC or RC
        body_type = parts[2]  # IB, MB, SB, IT, MT

        if bit_type == 'FC':
            category = 'FC'  # Fixed Cutter
            if body_type == 'MB':
                body_material = 'M'  # Matrix
            elif body_type == 'SB':
                body_material = 'S'  # Steel
            elif body_type == 'IB':
                body_material = 'M'  # Impreg = Matrix body
            else:
                body_material = ''
        elif bit_type == 'RC':
            if body_type == 'IT':
                category = 'TCI'  # Tri Cone Inserts
            elif body_type == 'MT':
                category = 'MT'  # Mill Tooth
            else:
                category = 'TCI'  # Default for RC
            body_material = ''  # N/A for roller cone
        else:
            category = 'FC'
            body_material = ''

        return category, body_material

    def get_or_create_size(self, size_str, dry_run=False):
        """Get or create BitSize record."""
        normalized = self.normalize_size(size_str)
        if not normalized:
            return None

        size_display, size_decimal = normalized
        code = str(size_decimal)

        if dry_run:
            existing = BitSize.objects.filter(code=code).first()
            if existing:
                return existing
            return None

        size, created = BitSize.objects.get_or_create(
            code=code,
            defaults={
                'size_decimal': size_decimal,
                'size_display': size_display,
                'size_inches': size_display,
            }
        )
        if created:
            self.stdout.write(f"  Created BitSize: {size_display}")
        return size

    def clean_records(self, dry_run=False):
        """Clean and trim all existing design records."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("Cleaning existing design records...")
        self.stdout.write("=" * 50)

        designs = Design.objects.all()
        cleaned_count = 0
        fields_cleaned = 0

        for design in designs:
            changed = False

            # Check and clean each text field
            if design.mat_no and design.mat_no != design.mat_no.strip():
                if not dry_run:
                    design.mat_no = design.mat_no.strip()
                changed = True
                fields_cleaned += 1

            if design.hdbs_type and design.hdbs_type != design.hdbs_type.strip():
                if not dry_run:
                    design.hdbs_type = design.hdbs_type.strip()
                changed = True
                fields_cleaned += 1

            if design.smi_type and design.smi_type != design.smi_type.strip():
                if not dry_run:
                    design.smi_type = design.smi_type.strip()
                changed = True
                fields_cleaned += 1

            if design.category and design.category != design.category.strip():
                if not dry_run:
                    design.category = design.category.strip()
                changed = True
                fields_cleaned += 1

            if design.body_material and design.body_material != design.body_material.strip():
                if not dry_run:
                    design.body_material = design.body_material.strip()
                changed = True
                fields_cleaned += 1

            if design.series and design.series != design.series.strip():
                if not dry_run:
                    design.series = design.series.strip()
                changed = True
                fields_cleaned += 1

            if design.order_level and design.order_level != design.order_level.strip():
                if not dry_run:
                    design.order_level = design.order_level.strip()
                changed = True
                fields_cleaned += 1

            if design.description and design.description != design.description.strip():
                if not dry_run:
                    design.description = design.description.strip()
                changed = True
                fields_cleaned += 1

            if design.ref_mat_no and design.ref_mat_no != design.ref_mat_no.strip():
                if not dry_run:
                    design.ref_mat_no = design.ref_mat_no.strip()
                changed = True
                fields_cleaned += 1

            if changed:
                cleaned_count += 1
                if not dry_run:
                    design.save()
                self.stdout.write(f"  Cleaned: {design.mat_no}")

        self.stdout.write(f"\nCleaned {cleaned_count} designs ({fields_cleaned} fields)")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS("Records cleaned successfully"))

        return cleaned_count

    def handle(self, *args, **options):
        import pandas as pd

        confirm = options['confirm']
        dry_run = options['dry_run'] or not confirm
        clean_only = options.get('clean', False)
        excel_file = options['file']

        # Handle --clean option
        if clean_only:
            self.clean_records(dry_run=dry_run)
            if not confirm:
                self.stdout.write(self.style.WARNING("\nUse --confirm to actually clean records"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        # Read Excel file
        try:
            df = pd.read_excel(excel_file)
            self.stdout.write(f"Loaded {len(df)} rows from {excel_file}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading Excel file: {e}"))
            return

        # Filter RM rows
        rm_rows = df[df['Item number'].str.startswith('RM-', na=False)]
        self.stdout.write(f"Found {len(rm_rows)} RM (Raw Material) rows")

        # Get all valid MAT numbers
        all_mats = self.L3_MATS | self.L4_MATS
        self.stdout.write(f"L3 MATs: {len(self.L3_MATS)}, L4 MATs: {len(self.L4_MATS)}")

        # Filter by MAT numbers in the provided list
        rm_filtered = rm_rows[rm_rows['Search name'].astype(str).isin(all_mats)]
        self.stdout.write(f"Matching designs to import: {len(rm_filtered)}")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for idx, row in rm_filtered.iterrows():
            item_number = row['Item number']
            product_name = str(row['Product name'])
            search_name = str(row['Search name'])

            # Parse product name
            size_str, hdbs_type, mat_no = self.parse_product_name(product_name)

            if not mat_no:
                mat_no = search_name  # Fallback to search name

            if not mat_no:
                self.stdout.write(self.style.WARNING(f"  Skipping {item_number}: Could not extract MAT number"))
                error_count += 1
                continue

            # Determine order level
            if mat_no in self.L3_MATS:
                order_level = '3'
            elif mat_no in self.L4_MATS:
                order_level = '4'
            else:
                order_level = ''

            # Get category and body material
            category, body_material = self.get_category_and_body(item_number)

            # Get or create size
            size_obj = None
            if size_str:
                size_obj = self.get_or_create_size(size_str, dry_run=dry_run)

            # Extract series from HDBS type (first 2-3 letters)
            series = ''
            if hdbs_type:
                match = re.match(r'^([A-Za-z]{2,3})', hdbs_type)
                if match:
                    series = match.group(1).upper()

            self.stdout.write(
                f"  {item_number}: MAT={mat_no}, Size={size_str}, HDBS={hdbs_type}, "
                f"Level=L{order_level}, Cat={category}, Body={body_material}"
            )

            if dry_run:
                created_count += 1
                continue

            # Clean/trim all values before import
            mat_no = mat_no.strip() if mat_no else ''
            hdbs_type = hdbs_type.strip() if hdbs_type else ''
            category = category.strip() if category else ''
            body_material = body_material.strip() if body_material else ''
            order_level = order_level.strip() if order_level else ''
            series = series.strip() if series else ''

            # Check if design already exists
            existing = Design.objects.filter(mat_no=mat_no).first()
            if existing:
                # Update existing design with trimmed values
                existing.hdbs_type = hdbs_type or (existing.hdbs_type or '').strip()
                existing.category = category or (existing.category or '').strip()
                existing.body_material = body_material or (existing.body_material or '').strip()
                existing.order_level = order_level or (existing.order_level or '').strip()
                existing.status = 'ACTIVE'  # Set to active as requested
                if size_obj:
                    existing.size = size_obj
                if series:
                    existing.series = series
                existing.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"    Updated: {mat_no}"))
            else:
                # Create new design
                try:
                    design = Design.objects.create(
                        mat_no=mat_no,
                        hdbs_type=hdbs_type or '',
                        category=category or 'FC',
                        body_material=body_material or '',
                        order_level=order_level,
                        size=size_obj,
                        series=series,
                        status='ACTIVE',  # Set to active as requested
                        description=f"Imported from {item_number}"
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"    Created: {mat_no}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    Error creating {mat_no}: {e}"))
                    error_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Import Summary:")
        self.stdout.write(f"  Created: {created_count}")
        self.stdout.write(f"  Updated: {updated_count}")
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write(f"  Errors: {error_count}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a DRY RUN. Use --confirm to actually import."))
