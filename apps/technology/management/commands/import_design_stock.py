"""
Import design (RM) stock quantities from ERP On-hand Excel file.

This command reads stock quantities for Raw Material (RM) items from the ERP
On-hand.xlsx file and updates the Design model with current quantities.

The command automatically detects the header row by searching for "Item number"
column, making it flexible for files with varying metadata rows.

On-hand.xlsx Column Mapping for RM Items:
- Item number: ERP Item Number (e.g., RM-FC-MB-0002)
- Color: MAT Number - used to match Design.mat_no
- Style: HDBS Type - used to verify match
- Size: Bit size (e.g., "5 7/8")
- Available physical: Quantity

Item Number Prefix → Category Mapping:
- RM-FC-*  → Fixed Cutter (FC)
- RM-RC-*  → Roller Cone (RC) - includes MT and TCI

Usage:
    python manage.py import_design_stock                    # Preview mode
    python manage.py import_design_stock --confirm          # Apply changes
    python manage.py import_design_stock --file path/to.xlsx --confirm
"""

import os
from decimal import Decimal
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class Command(BaseCommand):
    help = 'Import design (RM) stock quantities from ERP On-hand Excel file'

    # Expected header names (exact ERP names, case-insensitive)
    HEADER_PATTERNS = {
        'item_number': ['item number'],
        'item_group': ['item group'],
        'configuration': ['configuration'],
        'size': ['size'],
        'color': ['color'],  # This is the MAT number
        'style': ['style'],  # This is the HDBS type
        'site': ['site'],
        'warehouse': ['warehouse'],
        'location': ['location'],
        'qty': ['available physical'],
    }

    # Warehouses to include (filter out Transit, etc.)
    INCLUDE_WAREHOUSES = ['Store', 'Shopfloor', 'R Warehous', 'FG Warehou']

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='docs/On-hand.xlsx',
            help='Path to ERP On-hand Excel file (default: docs/On-hand.xlsx)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually apply changes (default is preview mode)'
        )
        parser.add_argument(
            '--include-transit',
            action='store_true',
            help='Include Transit warehouse quantities (default: exclude)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed per-item import info'
        )
        parser.add_argument(
            '--update-erp-item',
            action='store_true',
            help='Also update ardt_item_no field with ERP item number'
        )

    def find_header_row(self, ws):
        """
        Auto-detect the header row by searching for 'Item number' column.
        Returns (header_row, column_map) or (None, None) if not found.
        """
        max_search_rows = 20  # Search first 20 rows for headers

        for row_idx in range(1, min(max_search_rows + 1, ws.max_row + 1)):
            for col_idx in range(1, min(20, ws.max_column + 1)):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value:
                    cell_str = str(cell_value).strip().lower()
                    if cell_str in self.HEADER_PATTERNS['item_number']:
                        column_map = self._map_columns(ws, row_idx)
                        return row_idx, column_map

        return None, None

    def _map_columns(self, ws, header_row):
        """Map column names to their positions based on header row."""
        column_map = {}

        for col_idx in range(1, ws.max_column + 1):
            cell_value = ws.cell(row=header_row, column=col_idx).value
            if not cell_value:
                continue

            cell_str = str(cell_value).strip().lower()

            for field_name, patterns in self.HEADER_PATTERNS.items():
                if cell_str in patterns or any(p in cell_str for p in patterns):
                    if field_name not in column_map:
                        column_map[field_name] = col_idx
                        break

        return column_map

    def handle(self, *args, **options):
        if not HAS_OPENPYXL:
            self.stderr.write(self.style.ERROR('openpyxl is required. Install with: pip install openpyxl'))
            return

        file_path = options['file']
        confirm = options['confirm']
        include_transit = options['include_transit']
        verbose = options['verbose']
        update_erp_item = options['update_erp_item']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(f'Loading Excel file: {file_path}')

        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        sheet_name = ws.title

        self.stdout.write(f'Processing sheet: {sheet_name}')

        header_row, column_map = self.find_header_row(ws)

        if header_row is None:
            self.stderr.write(self.style.ERROR(
                'Could not find header row. Looking for "Item number" column in first 20 rows.'
            ))
            return

        self.stdout.write(self.style.SUCCESS(f'Found headers at row {header_row}'))
        self.stdout.write(f'Column mapping: {column_map}')

        required_columns = ['item_number', 'color', 'qty']
        missing = [c for c in required_columns if c not in column_map]
        if missing:
            self.stderr.write(self.style.ERROR(f'Missing required columns: {missing}'))
            self.stderr.write('Expected columns: Item number, Color, Available physical')
            return

        data_start_row = header_row + 1
        self.stdout.write(f'Data starts at row: {data_start_row}')

        from apps.technology.models import Design

        warehouses_to_include = set(self.INCLUDE_WAREHOUSES)
        if include_transit:
            warehouses_to_include.add('Transit')
        self.stdout.write(f'Including warehouses: {warehouses_to_include}')

        # Aggregate quantities by MAT number (Color column)
        # Multiple rows can exist for same item in different warehouses/locations
        aggregated = defaultdict(lambda: {
            'qty': 0,
            'erp_items': set(),
            'warehouses': set(),
            'styles': set(),  # HDBS types found
        })

        skipped = {
            'no_item_number': 0,
            'not_rm': 0,
            'no_mat_no': 0,
            'excluded_warehouse': 0,
            'zero_qty': 0,
        }

        self.stdout.write(f'Reading data rows...')
        for row_idx in range(data_start_row, ws.max_row + 1):
            item_number = ws.cell(row=row_idx, column=column_map['item_number']).value
            if not item_number:
                skipped['no_item_number'] += 1
                continue

            item_number = str(item_number).strip()

            # Only process RM (Raw Material) items
            if not item_number.upper().startswith('RM'):
                skipped['not_rm'] += 1
                continue

            # Get MAT number from Color column
            mat_no = ws.cell(row=row_idx, column=column_map['color']).value
            if not mat_no:
                skipped['no_mat_no'] += 1
                continue
            mat_no = str(mat_no).strip()

            # Get warehouse (optional)
            warehouse = ''
            if 'warehouse' in column_map:
                warehouse = ws.cell(row=row_idx, column=column_map['warehouse']).value or ''
                warehouse = str(warehouse).strip()

            if warehouse and warehouse not in warehouses_to_include:
                skipped['excluded_warehouse'] += 1
                continue

            # Get HDBS type from Style column (optional, for verification)
            style = ''
            if 'style' in column_map:
                style = ws.cell(row=row_idx, column=column_map['style']).value or ''
                style = str(style).strip()

            # Get quantity
            qty_raw = ws.cell(row=row_idx, column=column_map['qty']).value
            try:
                qty = int(float(str(qty_raw or 0)))
            except (ValueError, TypeError):
                qty = 0

            if qty <= 0:
                skipped['zero_qty'] += 1
                continue

            # Aggregate by MAT number
            aggregated[mat_no]['qty'] += qty
            aggregated[mat_no]['erp_items'].add(item_number)
            aggregated[mat_no]['warehouses'].add(warehouse)
            if style:
                aggregated[mat_no]['styles'].add(style)

        self.stdout.write(f'Aggregated {len(aggregated)} unique MAT numbers')
        self.stdout.write(f'Skipped rows:')
        for reason, count in skipped.items():
            if count > 0:
                self.stdout.write(f'  - {reason}: {count}')

        # Build MAT -> Design mapping
        mat_to_design = {}
        for design in Design.objects.all():
            if design.mat_no:
                mat_to_design[str(design.mat_no).strip()] = design

        self.stdout.write(f'Found {len(mat_to_design)} designs with MAT numbers')

        # Statistics
        stats = {
            'mats_processed': 0,
            'designs_matched': 0,
            'designs_not_found': 0,
            'designs_updated': 0,
            'total_quantity': 0,
        }
        not_found_items = []
        matched_items = []

        if confirm:
            self.stdout.write(self.style.WARNING('CONFIRM mode - Changes will be applied'))
        else:
            self.stdout.write(self.style.NOTICE('PREVIEW mode - No changes will be made'))

        self.stdout.write(f'\nProcessing {len(aggregated)} aggregated MAT numbers...\n')

        with transaction.atomic():
            for mat_no, data in aggregated.items():
                stats['mats_processed'] += 1
                qty = data['qty']
                erp_items = data['erp_items']
                styles = data['styles']

                design = mat_to_design.get(mat_no)
                if not design:
                    stats['designs_not_found'] += 1
                    not_found_items.append({
                        'mat_no': mat_no,
                        'erp_items': list(erp_items),
                        'styles': list(styles),
                        'qty': qty,
                    })
                    continue

                stats['designs_matched'] += 1
                stats['total_quantity'] += qty

                # Verify HDBS type matches (warning only)
                if styles and design.hdbs_type:
                    if design.hdbs_type not in styles:
                        if verbose:
                            self.stdout.write(self.style.WARNING(
                                f'  HDBS mismatch for {mat_no}: Design has {design.hdbs_type}, On-hand has {styles}'
                            ))

                matched_items.append({
                    'mat_no': mat_no,
                    'hdbs_type': design.hdbs_type,
                    'erp_items': list(erp_items),
                    'qty': qty,
                    'old_qty': design.quantity_on_hand,
                })

                if confirm:
                    design.quantity_on_hand = qty
                    design.stock_last_updated = timezone.now()

                    # Optionally update ERP item number
                    if update_erp_item and erp_items:
                        design.ardt_item_no = sorted(erp_items)[0]  # Use first item number

                    design.save(update_fields=['quantity_on_hand', 'stock_last_updated', 'ardt_item_no'])
                    stats['designs_updated'] += 1

                    if verbose:
                        self.stdout.write(f'  {design.mat_no} ({design.hdbs_type}): {qty}')
                else:
                    stats['designs_updated'] += 1

            if not confirm:
                transaction.set_rollback(True)

        # Print summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('IMPORT SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"MAT numbers processed: {stats['mats_processed']}")
        self.stdout.write(f"Designs matched:       {stats['designs_matched']}")
        self.stdout.write(self.style.WARNING(f"Designs not found:     {stats['designs_not_found']}"))

        if confirm:
            self.stdout.write(f"Designs updated:       {stats['designs_updated']}")

        self.stdout.write(self.style.SUCCESS(f"Total quantity:        {stats['total_quantity']}"))

        # Show matched items summary
        if matched_items:
            self.stdout.write('')
            self.stdout.write('Matched designs (sample):')
            for item in matched_items[:10]:
                change = f" (was {item['old_qty']})" if item['old_qty'] != item['qty'] else ""
                self.stdout.write(f"  {item['mat_no']} ({item['hdbs_type']}): {item['qty']}{change}")
            if len(matched_items) > 10:
                self.stdout.write(f"  ... and {len(matched_items) - 10} more")

        # Show not found items
        if not_found_items:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'Designs not found in system ({len(not_found_items)} items):'))
            for item in not_found_items[:20]:
                styles_str = ', '.join(item['styles']) if item['styles'] else 'N/A'
                erp_str = ', '.join(list(item['erp_items'])[:2])
                self.stdout.write(f"  MAT {item['mat_no']} ({styles_str}): {item['qty']} ({erp_str})")
            if len(not_found_items) > 20:
                self.stdout.write(f"  ... and {len(not_found_items) - 20} more")

        if not confirm:
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('This was a PREVIEW. Run with --confirm to apply changes.'))
