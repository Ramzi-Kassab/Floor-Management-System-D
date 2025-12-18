"""
Management command to seed IADC codes, connection types, formation types, and applications.

Based on:
- IADC (International Association of Drilling Contractors) standards
- Halliburton/Security DBS product classifications
- API specifications for connections
- Aramco operational data (42,000 records analyzed)

Usage:
    python manage.py seed_reference_data
    python manage.py seed_reference_data --iadc-only
    python manage.py seed_reference_data --connections-only
"""

from django.core.management.base import BaseCommand
from apps.workorders.models import (
    IADCCode, ConnectionType, ConnectionSize, FormationType, Application
)


class Command(BaseCommand):
    help = 'Seed IADC codes and other reference data for drill bit classification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iadc-only',
            action='store_true',
            help='Only seed IADC codes',
        )
        parser.add_argument(
            '--connections-only',
            action='store_true',
            help='Only seed connection types and sizes',
        )
        parser.add_argument(
            '--formations-only',
            action='store_true',
            help='Only seed formation types',
        )
        parser.add_argument(
            '--applications-only',
            action='store_true',
            help='Only seed applications',
        )

    def handle(self, *args, **options):
        if options['iadc_only']:
            self.seed_iadc_codes()
        elif options['connections_only']:
            self.seed_connection_types()
            self.seed_connection_sizes()
        elif options['formations_only']:
            self.seed_formation_types()
        elif options['applications_only']:
            self.seed_applications()
        else:
            # Seed all
            self.seed_iadc_codes()
            self.seed_connection_types()
            self.seed_connection_sizes()
            self.seed_formation_types()
            self.seed_applications()

        self.stdout.write(self.style.SUCCESS('Reference data seeding complete!'))

    def seed_iadc_codes(self):
        """
        Seed IADC codes based on Aramco data analysis and IADC standards.

        PDC Code Format: [Body][Formation][Cutter][Profile]
        - Body: M=Matrix, S=Steel, D=Diamond
        - Formation: 1-4 (1=Soft to 4=Hard), 6-8 for Diamond
        - Cutter Size: 1=Large (>25mm), 2=Medium-Large (19mm), 3=Medium (13-16mm), 4=Small (8-10mm)
        - Profile: 1=Fishtail, 2=Short, 3=Medium, 4=Long

        Roller Cone Format: [Series][Type][Bearing][Feature]
        - Series: 1-3=Milled Tooth, 4-8=TCI
        - Type: 1-4 (subtype within series)
        - Bearing: 1-7 (bearing/gauge design)
        - Feature: Optional letter (A, C, D, E, G, J, L, R, S, X, Y, etc.)
        """
        self.stdout.write('Seeding IADC codes...')

        # PDC codes from Aramco data - Matrix body
        pdc_matrix_codes = [
            # M1xx - Soft formations
            ('M115', 'PDC', 'M', 'Soft', 'Large (>25mm)', 'Long', 'Matrix PDC for soft formations, large cutters, long profile'),
            ('M122', 'PDC', 'M', 'Soft', 'Medium-Large (19mm)', 'Short', 'Matrix PDC for soft formations, 19mm cutters, short profile'),
            ('M127', 'PDC', 'M', 'Soft', 'Medium-Large (19mm)', 'N/A', 'Matrix PDC for soft formations, 19mm cutters'),
            # M2xx - Soft to Medium formations
            ('M211', 'PDC', 'M', 'Soft-Medium', 'Large (>25mm)', 'Fishtail', 'Matrix PDC for soft-medium formations, large cutters, fishtail'),
            ('M222', 'PDC', 'M', 'Soft-Medium', 'Medium-Large (19mm)', 'Short', 'Matrix PDC for soft-medium formations, 19mm cutters'),
            ('M223', 'PDC', 'M', 'Soft-Medium', 'Medium-Large (19mm)', 'Medium', 'Matrix PDC for soft-medium formations'),
            ('M232', 'PDC', 'M', 'Soft-Medium', 'Medium (13-16mm)', 'Short', 'Matrix PDC for soft-medium formations, 13mm cutters'),
            ('M233', 'PDC', 'M', 'Soft-Medium', 'Medium (13-16mm)', 'Medium', 'Matrix PDC for soft-medium formations'),
            ('M236', 'PDC', 'M', 'Soft-Medium', 'Medium (13-16mm)', 'N/A', 'Matrix PDC for soft-medium formations'),
            ('M243', 'PDC', 'M', 'Soft-Medium', 'Small (8-10mm)', 'Medium', 'Matrix PDC for soft-medium formations, small cutters'),
            # M3xx - Medium formations
            ('M322', 'PDC', 'M', 'Medium', 'Medium-Large (19mm)', 'Short', 'Matrix PDC for medium formations'),
            ('M323', 'PDC', 'M', 'Medium', 'Medium-Large (19mm)', 'Medium', 'Matrix PDC for medium formations'),
            ('M324', 'PDC', 'M', 'Medium', 'Medium-Large (19mm)', 'Long', 'Matrix PDC for medium formations, long profile'),
            ('M332', 'PDC', 'M', 'Medium', 'Medium (13-16mm)', 'Short', 'Matrix PDC for medium formations, 13mm cutters'),
            ('M333', 'PDC', 'M', 'Medium', 'Medium (13-16mm)', 'Medium', 'Matrix PDC for medium formations'),
            ('M334', 'PDC', 'M', 'Medium', 'Medium (13-16mm)', 'Long', 'Matrix PDC for medium formations'),
            ('M343', 'PDC', 'M', 'Medium', 'Small (8-10mm)', 'Medium', 'Matrix PDC for medium formations, small cutters'),
            ('M344', 'PDC', 'M', 'Medium', 'Small (8-10mm)', 'Long', 'Matrix PDC for medium formations'),
            # M4xx - Medium to Hard formations
            ('M422', 'PDC', 'M', 'Medium-Hard', 'Medium-Large (19mm)', 'Short', 'Matrix PDC for medium-hard formations'),
            ('M423', 'PDC', 'M', 'Medium-Hard', 'Medium-Large (19mm)', 'Medium', 'Matrix PDC for medium-hard formations'),
            ('M432', 'PDC', 'M', 'Medium-Hard', 'Medium (13-16mm)', 'Short', 'Matrix PDC for medium-hard formations'),
            ('M433', 'PDC', 'M', 'Medium-Hard', 'Medium (13-16mm)', 'Medium', 'Matrix PDC for medium-hard formations'),
            ('M434', 'PDC', 'M', 'Medium-Hard', 'Medium (13-16mm)', 'Long', 'Matrix PDC for medium-hard formations'),
            ('M435', 'PDC', 'M', 'Medium-Hard', 'Medium (13-16mm)', 'N/A', 'Matrix PDC for medium-hard formations'),
            ('M442', 'PDC', 'M', 'Medium-Hard', 'Small (8-10mm)', 'Short', 'Matrix PDC for medium-hard formations'),
            ('M443', 'PDC', 'M', 'Medium-Hard', 'Small (8-10mm)', 'Medium', 'Matrix PDC for medium-hard formations'),
            ('M445', 'PDC', 'M', 'Medium-Hard', 'Small (8-10mm)', 'N/A', 'Matrix PDC for medium-hard formations'),
            ('M453', 'PDC', 'M', 'Medium-Hard', 'N/A', 'Medium', 'Matrix PDC for medium-hard formations'),
            ('M462', 'PDC', 'M', 'Medium-Hard', 'N/A', 'Short', 'Matrix PDC for medium-hard formations'),
            # M6xx - Hard formations (Diamond style)
            ('M613', 'PDC', 'M', 'Hard', 'Large (>25mm)', 'Medium', 'Matrix PDC for hard formations'),
            ('M615', 'PDC', 'M', 'Hard', 'Large (>25mm)', 'N/A', 'Matrix PDC for hard formations'),
            ('M617', 'PDC', 'M', 'Hard', 'Large (>25mm)', 'N/A', 'Matrix PDC for hard formations'),
            ('M622', 'PDC', 'M', 'Hard', 'Medium-Large (19mm)', 'Short', 'Matrix PDC for hard formations'),
            ('M623', 'PDC', 'M', 'Hard', 'Medium-Large (19mm)', 'Medium', 'Matrix PDC for hard formations'),
            ('M627', 'PDC', 'M', 'Hard', 'Medium-Large (19mm)', 'N/A', 'Matrix PDC for hard formations'),
            # M7xx - Very Hard formations
            ('M712', 'PDC', 'M', 'Very Hard', 'Large (>25mm)', 'Short', 'Matrix PDC for very hard formations'),
            ('M713', 'PDC', 'M', 'Very Hard', 'Large (>25mm)', 'Medium', 'Matrix PDC for very hard formations'),
            ('M737', 'PDC', 'M', 'Very Hard', 'Medium (13-16mm)', 'N/A', 'Matrix PDC for very hard formations'),
        ]

        # PDC codes - Steel body
        pdc_steel_codes = [
            ('S122', 'PDC', 'S', 'Soft', 'Medium-Large (19mm)', 'Short', 'Steel PDC for soft formations'),
            ('S211', 'PDC', 'S', 'Soft-Medium', 'Large (>25mm)', 'Fishtail', 'Steel PDC for soft-medium formations'),
            ('S222', 'PDC', 'S', 'Soft-Medium', 'Medium-Large (19mm)', 'Short', 'Steel PDC for soft-medium formations'),
            ('S223', 'PDC', 'S', 'Soft-Medium', 'Medium-Large (19mm)', 'Medium', 'Steel PDC for soft-medium formations'),
            ('S232', 'PDC', 'S', 'Soft-Medium', 'Medium (13-16mm)', 'Short', 'Steel PDC for soft-medium formations'),
            ('S233', 'PDC', 'S', 'Soft-Medium', 'Medium (13-16mm)', 'Medium', 'Steel PDC for soft-medium formations'),
            ('S322', 'PDC', 'S', 'Medium', 'Medium-Large (19mm)', 'Short', 'Steel PDC for medium formations'),
            ('S323', 'PDC', 'S', 'Medium', 'Medium-Large (19mm)', 'Medium', 'Steel PDC for medium formations'),
            ('S332', 'PDC', 'S', 'Medium', 'Medium (13-16mm)', 'Short', 'Steel PDC for medium formations'),
            ('S333', 'PDC', 'S', 'Medium', 'Medium (13-16mm)', 'Medium', 'Steel PDC for medium formations'),
            ('S343', 'PDC', 'S', 'Medium', 'Small (8-10mm)', 'Medium', 'Steel PDC for medium formations'),
            ('S422', 'PDC', 'S', 'Medium-Hard', 'Medium-Large (19mm)', 'Short', 'Steel PDC for medium-hard formations'),
            ('S423', 'PDC', 'S', 'Medium-Hard', 'Medium-Large (19mm)', 'Medium', 'Steel PDC for medium-hard formations'),
            ('S432', 'PDC', 'S', 'Medium-Hard', 'Medium (13-16mm)', 'Short', 'Steel PDC for medium-hard formations'),
            ('S433', 'PDC', 'S', 'Medium-Hard', 'Medium (13-16mm)', 'Medium', 'Steel PDC for medium-hard formations'),
            ('S434', 'PDC', 'S', 'Medium-Hard', 'Medium (13-16mm)', 'Long', 'Steel PDC for medium-hard formations'),
            ('S435', 'PDC', 'S', 'Medium-Hard', 'Medium (13-16mm)', 'N/A', 'Steel PDC for medium-hard formations'),
            ('S437', 'PDC', 'S', 'Medium-Hard', 'Medium (13-16mm)', 'N/A', 'Steel PDC for medium-hard formations'),
            ('S442', 'PDC', 'S', 'Medium-Hard', 'Small (8-10mm)', 'Short', 'Steel PDC for medium-hard formations'),
            ('S443', 'PDC', 'S', 'Medium-Hard', 'Small (8-10mm)', 'Medium', 'Steel PDC for medium-hard formations'),
            ('S445', 'PDC', 'S', 'Medium-Hard', 'Small (8-10mm)', 'N/A', 'Steel PDC for medium-hard formations'),
            ('S517', 'PDC', 'S', 'Hard', 'Large (>25mm)', 'N/A', 'Steel PDC for hard formations'),
        ]

        # PDC codes - Diamond body
        pdc_diamond_codes = [
            ('D433', 'PDC', 'D', 'Medium-Hard', 'Medium (13-16mm)', 'Medium', 'Diamond PDC for medium-hard formations'),
            ('D443', 'PDC', 'D', 'Medium-Hard', 'Small (8-10mm)', 'Medium', 'Diamond PDC for medium-hard formations'),
        ]

        # Roller Cone codes from Aramco data
        roller_cone_codes = [
            # Series 1 - Milled Tooth Soft
            ('115', 'RC', '', 'Soft', '', '', '1', '1', '5', '', 'Milled Tooth for soft formations'),
            ('115M', 'RC', '', 'Soft', '', '', '1', '1', '5', 'M', 'Milled Tooth for soft formations with feature M'),
            ('117', 'RC', '', 'Soft', '', '', '1', '1', '7', '', 'Milled Tooth for soft formations'),
            ('127', 'RC', '', 'Soft', '', '', '1', '2', '7', '', 'Milled Tooth for soft formations'),
            ('127M', 'RC', '', 'Soft', '', '', '1', '2', '7', 'M', 'Milled Tooth for soft formations with feature M'),
            ('136', 'RC', '', 'Soft', '', '', '1', '3', '6', '', 'Milled Tooth for soft formations'),
            ('137', 'RC', '', 'Soft', '', '', '1', '3', '7', '', 'Milled Tooth for soft formations'),
            # Series 2 - Milled Tooth Medium
            ('211', 'RC', '', 'Medium', '', '', '2', '1', '1', '', 'Milled Tooth for medium formations'),
            ('214', 'RC', '', 'Medium', '', '', '2', '1', '4', '', 'Milled Tooth for medium formations'),
            ('217', 'RC', '', 'Medium', '', '', '2', '1', '7', '', 'Milled Tooth for medium formations'),
            # Series 3 - Milled Tooth Hard
            ('311', 'RC', '', 'Hard', '', '', '3', '1', '1', '', 'Milled Tooth for hard formations'),
            ('317', 'RC', '', 'Hard', '', '', '3', '1', '7', '', 'Milled Tooth for hard formations'),
            ('322', 'RC', '', 'Hard', '', '', '3', '2', '2', '', 'Milled Tooth for hard formations'),
            # Series 4 - TCI Soft
            ('415', 'RC', '', 'Soft', '', '', '4', '1', '5', '', 'TCI for soft formations'),
            ('417', 'RC', '', 'Soft', '', '', '4', '1', '7', '', 'TCI for soft formations'),
            ('425', 'RC', '', 'Soft', '', '', '4', '2', '5', '', 'TCI for soft formations'),
            ('435', 'RC', '', 'Soft', '', '', '4', '3', '5', '', 'TCI for soft formations'),
            ('437', 'RC', '', 'Soft', '', '', '4', '3', '7', '', 'TCI for soft formations'),
            ('445', 'RC', '', 'Soft', '', '', '4', '4', '5', '', 'TCI for soft formations'),
            ('447', 'RC', '', 'Soft', '', '', '4', '4', '7', '', 'TCI for soft formations'),
            # Series 5 - TCI Medium
            ('511', 'RC', '', 'Medium', '', '', '5', '1', '1', '', 'TCI for medium formations'),
            ('515', 'RC', '', 'Medium', '', '', '5', '1', '5', '', 'TCI for medium formations'),
            ('517', 'RC', '', 'Medium', '', '', '5', '1', '7', '', 'TCI for medium formations'),
            ('517X', 'RC', '', 'Medium', '', '', '5', '1', '7', 'X', 'TCI for medium formations with enhanced gauge protection'),
            ('525', 'RC', '', 'Medium', '', '', '5', '2', '5', '', 'TCI for medium formations'),
            ('527', 'RC', '', 'Medium', '', '', '5', '2', '7', '', 'TCI for medium formations'),
            ('535', 'RC', '', 'Medium', '', '', '5', '3', '5', '', 'TCI for medium formations'),
            ('537', 'RC', '', 'Medium', '', '', '5', '3', '7', '', 'TCI for medium formations'),
            ('537X', 'RC', '', 'Medium', '', '', '5', '3', '7', 'X', 'TCI for medium formations with enhanced gauge protection'),
            ('545', 'RC', '', 'Medium', '', '', '5', '4', '5', '', 'TCI for medium formations'),
            ('547', 'RC', '', 'Medium', '', '', '5', '4', '7', '', 'TCI for medium formations'),
            # Series 6 - TCI Medium-Hard
            ('615', 'RC', '', 'Medium-Hard', '', '', '6', '1', '5', '', 'TCI for medium-hard formations'),
            ('617', 'RC', '', 'Medium-Hard', '', '', '6', '1', '7', '', 'TCI for medium-hard formations'),
            ('617X', 'RC', '', 'Medium-Hard', '', '', '6', '1', '7', 'X', 'TCI for medium-hard with enhanced gauge'),
            ('625', 'RC', '', 'Medium-Hard', '', '', '6', '2', '5', '', 'TCI for medium-hard formations'),
            ('627', 'RC', '', 'Medium-Hard', '', '', '6', '2', '7', '', 'TCI for medium-hard formations'),
            ('627Y', 'RC', '', 'Medium-Hard', '', '', '6', '2', '7', 'Y', 'TCI for medium-hard with conical inserts'),
            ('635', 'RC', '', 'Medium-Hard', '', '', '6', '3', '5', '', 'TCI for medium-hard formations'),
            ('637', 'RC', '', 'Medium-Hard', '', '', '6', '3', '7', '', 'TCI for medium-hard formations'),
            ('645', 'RC', '', 'Medium-Hard', '', '', '6', '4', '5', '', 'TCI for medium-hard formations'),
            ('647', 'RC', '', 'Medium-Hard', '', '', '6', '4', '7', '', 'TCI for medium-hard formations'),
            # Series 7 - TCI Hard
            ('715', 'RC', '', 'Hard', '', '', '7', '1', '5', '', 'TCI for hard formations'),
            ('717', 'RC', '', 'Hard', '', '', '7', '1', '7', '', 'TCI for hard formations'),
            ('725', 'RC', '', 'Hard', '', '', '7', '2', '5', '', 'TCI for hard formations'),
            ('727', 'RC', '', 'Hard', '', '', '7', '2', '7', '', 'TCI for hard formations'),
            ('735', 'RC', '', 'Hard', '', '', '7', '3', '5', '', 'TCI for hard formations'),
            ('737', 'RC', '', 'Hard', '', '', '7', '3', '7', '', 'TCI for hard formations'),
            ('745', 'RC', '', 'Hard', '', '', '7', '4', '5', '', 'TCI for hard formations'),
            ('747', 'RC', '', 'Hard', '', '', '7', '4', '7', '', 'TCI for hard formations'),
            # Series 8 - TCI Extremely Hard
            ('817', 'RC', '', 'Extremely Hard', '', '', '8', '1', '7', '', 'TCI for extremely hard formations'),
            ('827', 'RC', '', 'Extremely Hard', '', '', '8', '2', '7', '', 'TCI for extremely hard formations'),
            ('837', 'RC', '', 'Extremely Hard', '', '', '8', '3', '7', '', 'TCI for extremely hard formations'),
            ('847', 'RC', '', 'Extremely Hard', '', '', '8', '4', '7', '', 'TCI for extremely hard formations'),
        ]

        # Special/Other codes
        special_codes = [
            ('HYB', 'HYB', '', '', '', '', '', '', '', '', 'Hybrid bit combining PDC and roller cone elements'),
            ('BCH', 'PDC', '', '', '', '', '', '', '', '', 'Bi-center hybrid bit'),
            ('CD', 'PDC', '', '', '', '', '', '', '', '', 'Core drill bit'),
        ]

        created_count = 0

        # Insert PDC Matrix codes
        for code_data in pdc_matrix_codes:
            code, category, body, formation, cutter, profile, desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'category': category,
                    'body_type': body,
                    'formation_hardness': formation,
                    'cutter_size_class': cutter,
                    'profile_class': profile,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        # Insert PDC Steel codes
        for code_data in pdc_steel_codes:
            code, category, body, formation, cutter, profile, desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'category': category,
                    'body_type': body,
                    'formation_hardness': formation,
                    'cutter_size_class': cutter,
                    'profile_class': profile,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        # Insert PDC Diamond codes
        for code_data in pdc_diamond_codes:
            code, category, body, formation, cutter, profile, desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'category': category,
                    'body_type': body,
                    'formation_hardness': formation,
                    'cutter_size_class': cutter,
                    'profile_class': profile,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        # Insert Roller Cone codes
        for code_data in roller_cone_codes:
            code, category, body, formation, cutter, profile, series, type_, bearing, feature, desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'category': category,
                    'body_type': body,
                    'formation_hardness': formation,
                    'cutter_size_class': cutter,
                    'profile_class': profile,
                    'rc_series': series,
                    'rc_type': type_,
                    'rc_bearing_gauge': bearing,
                    'rc_feature': feature,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        # Insert Special codes
        for code_data in special_codes:
            code, category, body, formation, cutter, profile, series, type_, bearing, feature, desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'category': category,
                    'body_type': body,
                    'formation_hardness': formation,
                    'cutter_size_class': cutter,
                    'profile_class': profile,
                    'rc_series': series,
                    'rc_type': type_,
                    'rc_bearing_gauge': bearing,
                    'rc_feature': feature,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} IADC codes')

    def seed_connection_types(self):
        """Seed standard connection types based on API specifications."""
        self.stdout.write('Seeding connection types...')

        connection_types = [
            # API Regular connections
            ('REG', 'API Regular', 'API Spec 7-2', 4.0, '2 in/ft', 'Standard API rotary shouldered connection'),
            ('IF', 'API Internal Flush', 'API Spec 7-2', 4.0, '2 in/ft', 'Internal flush connection for smaller OD'),
            ('FH', 'API Full Hole', 'API Spec 7-2', 4.0, '2 in/ft', 'Full hole connection for maximum flow'),
            ('NC', 'API Numbered Connection', 'API Spec 7-2', 4.0, '2 in/ft', 'Numbered connection series'),
            ('HT', 'API Hi-Torque', 'API Spec 7-2', 4.0, '2 in/ft', 'High torque double-shouldered connection'),
            # Halliburton proprietary
            ('XT', 'Halliburton XT', '', None, '', 'Halliburton proprietary high-torque connection'),
            ('GPDS', 'Grant Prideco DS', '', None, '', 'Grant Prideco double-shoulder connection'),
            # Other common
            ('PAC', 'Pin-Assisted Connection', '', None, '', 'Pin-assisted rotary connection'),
            ('BCDS', 'Baker Hughes DS', '', None, '', 'Baker Hughes double-shoulder connection'),
        ]

        created_count = 0
        for i, (code, name, api_spec, tpi, taper, desc) in enumerate(connection_types):
            obj, created = ConnectionType.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'api_spec': api_spec,
                    'threads_per_inch': tpi,
                    'taper_per_foot': taper,
                    'description': desc,
                    'display_order': i * 10,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} connection types')

    def seed_connection_sizes(self):
        """Seed common connection sizes."""
        self.stdout.write('Seeding connection sizes...')

        # Get connection types
        try:
            reg = ConnectionType.objects.get(code='REG')
            if_ = ConnectionType.objects.get(code='IF')
            fh = ConnectionType.objects.get(code='FH')
            nc = ConnectionType.objects.get(code='NC')
            ht = ConnectionType.objects.get(code='HT')
        except ConnectionType.DoesNotExist:
            self.stdout.write(self.style.WARNING('  Connection types not found. Run seed_connection_types first.'))
            return

        connection_sizes = [
            # API REG sizes
            ('2-3/8 REG', reg, '2-3/8', 2.375, 'Small size API Regular'),
            ('2-7/8 REG', reg, '2-7/8', 2.875, 'API Regular for smaller strings'),
            ('3-1/2 REG', reg, '3-1/2', 3.5, 'Common API Regular size'),
            ('4-1/2 REG', reg, '4-1/2', 4.5, 'Standard API Regular'),
            ('6-5/8 REG', reg, '6-5/8', 6.625, 'Large API Regular'),
            ('7-5/8 REG', reg, '7-5/8', 7.625, 'Large API Regular'),
            # API IF sizes
            ('2-3/8 IF', if_, '2-3/8', 2.375, 'Small Internal Flush'),
            ('2-7/8 IF', if_, '2-7/8', 2.875, 'Internal Flush'),
            ('3-1/2 IF', if_, '3-1/2', 3.5, 'Common Internal Flush'),
            ('4-1/2 IF', if_, '4-1/2', 4.5, 'Standard Internal Flush'),
            # API FH sizes
            ('3-1/2 FH', fh, '3-1/2', 3.5, 'Full Hole'),
            ('4 FH', fh, '4', 4.0, 'Full Hole'),
            ('4-1/2 FH', fh, '4-1/2', 4.5, 'Full Hole'),
            # NC sizes (Numbered Connection)
            ('NC26', nc, '', 2.625, 'NC26 connection'),
            ('NC31', nc, '', 3.125, 'NC31 connection'),
            ('NC38', nc, '', 3.875, 'NC38 connection'),
            ('NC40', nc, '', 4.0, 'NC40 connection'),
            ('NC44', nc, '', 4.375, 'NC44 connection'),
            ('NC46', nc, '', 4.625, 'NC46 connection'),
            ('NC50', nc, '', 5.0, 'NC50 connection'),
            ('NC56', nc, '', 5.625, 'NC56 connection'),
            ('NC61', nc, '', 6.125, 'NC61 connection'),
            ('NC70', nc, '', 7.0, 'NC70 connection'),
            # HT sizes
            ('4-1/2 HT', ht, '4-1/2', 4.5, 'High Torque connection'),
            ('5-1/2 HT', ht, '5-1/2', 5.5, 'High Torque connection'),
            ('6-5/8 HT', ht, '6-5/8', 6.625, 'High Torque connection'),
        ]

        created_count = 0
        for i, (code, conn_type, size_in, size_dec, desc) in enumerate(connection_sizes):
            obj, created = ConnectionSize.objects.update_or_create(
                code=code,
                defaults={
                    'connection_type': conn_type,
                    'size_inches': size_in,
                    'size_decimal': size_dec,
                    'description': desc,
                    'display_order': i * 10,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} connection sizes')

    def seed_formation_types(self):
        """Seed geological formation types."""
        self.stdout.write('Seeding formation types...')

        formation_types = [
            # (code, name, hardness, ucs_min, ucs_max, rocks, pdc_codes, rc_codes, wob, rpm, desc)
            ('UNCONSOLIDATED', 'Unconsolidated', 'VERY_SOFT', 0, 2000,
             'Clay, Gumbo, Unconsolidated Sand, Marl',
             'M1xx, S1xx', '1xx, 4xx', '2-4', '100-250',
             'Highly drillable unconsolidated formations'),
            ('SOFT', 'Soft', 'SOFT', 2000, 8000,
             'Soft Shale, Salt, Chalk, Soft Limestone',
             'M2xx, S2xx', '1xx, 2xx, 4xx, 5xx', '3-5', '80-200',
             'Soft consolidated formations'),
            ('SOFT_MEDIUM', 'Soft to Medium', 'SOFT_MEDIUM', 8000, 15000,
             'Firm Shale, Gypsum, Sandy Shale, Soft Sandstone',
             'M2xx, M3xx, S2xx, S3xx', '2xx, 5xx', '4-6', '60-150',
             'Soft to medium consolidated formations'),
            ('MEDIUM', 'Medium', 'MEDIUM', 15000, 25000,
             'Medium Shale, Anhydrite, Medium Sandstone, Limestone',
             'M3xx, S3xx', '5xx, 6xx', '5-8', '50-120',
             'Medium hardness formations'),
            ('MEDIUM_HARD', 'Medium to Hard', 'MEDIUM_HARD', 25000, 35000,
             'Hard Shale, Hard Limestone, Dolomite, Quartzitic Sand',
             'M4xx, S4xx', '6xx, 7xx', '6-10', '40-100',
             'Medium to hard formations'),
            ('HARD', 'Hard', 'HARD', 35000, 50000,
             'Hard Limestone, Hard Dolomite, Hard Sandstone, Chert',
             'M6xx, D4xx', '7xx', '8-12', '30-80',
             'Hard abrasive formations'),
            ('VERY_HARD', 'Very Hard', 'VERY_HARD', 50000, 80000,
             'Quartzite, Granite, Basalt, Very Hard Dolomite',
             'M7xx, D4xx', '8xx', '10-15', '20-60',
             'Very hard and abrasive formations'),
            ('ABRASIVE', 'Abrasive', 'ABRASIVE', 30000, 60000,
             'Abrasive Sandstone, Quartzitic Sand, Volcanic Rock',
             'M4xx, M6xx', '6xx, 7xx, 8xx', '6-12', '30-80',
             'Highly abrasive formations requiring wear-resistant bits'),
        ]

        created_count = 0
        for i, data in enumerate(formation_types):
            code, name, hardness, ucs_min, ucs_max, rocks, pdc, rc, wob, rpm, desc = data
            obj, created = FormationType.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'hardness_category': hardness,
                    'ucs_min': ucs_min,
                    'ucs_max': ucs_max,
                    'typical_rocks': rocks,
                    'recommended_pdc_codes': pdc,
                    'recommended_rc_codes': rc,
                    'typical_wob_range': wob,
                    'typical_rpm_range': rpm,
                    'description': desc,
                    'display_order': i * 10,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} formation types')

    def seed_applications(self):
        """Seed drilling application types."""
        self.stdout.write('Seeding applications...')

        applications = [
            # (code, name, vertical, directional, horizontal, curve, lateral, motor, rss, turbine,
            #  steerability, rop, durability, desc)
            ('VERTICAL', 'Vertical Drilling', True, False, False, False, False, False, False, False,
             False, True, True, 'Standard vertical well drilling'),
            ('DIRECTIONAL', 'Directional Drilling', False, True, False, False, False, False, False, False,
             True, True, True, 'Controlled directional drilling'),
            ('HORIZONTAL', 'Horizontal Drilling', False, False, True, False, True, False, False, False,
             True, True, True, 'Horizontal well drilling'),
            ('CURVE', 'Curve/Build Section', False, True, False, True, False, False, False, False,
             True, False, True, 'Building angle in curve section'),
            ('LATERAL', 'Lateral Section', False, False, True, False, True, False, False, False,
             True, True, True, 'Horizontal lateral drilling'),
            ('MOTOR', 'Motor Drilling', False, True, True, True, True, True, False, False,
             True, True, False, 'Downhole motor drilling operations'),
            ('RSS', 'Rotary Steerable System', False, True, True, True, True, False, True, False,
             True, True, True, 'RSS directional drilling'),
            ('TURBINE', 'Turbine Drilling', False, True, True, False, False, False, False, True,
             False, True, True, 'Turbine drilling for high RPM'),
            ('TANGENT', 'Tangent Section', False, True, False, False, False, False, False, False,
             False, True, True, 'Hold angle tangent section'),
            ('KICKOFF', 'Kickoff Point', False, True, False, True, False, True, False, False,
             True, False, True, 'Initial kickoff from vertical'),
            ('SURFACE', 'Surface Hole', True, False, False, False, False, False, False, False,
             False, True, False, 'Surface casing hole section'),
            ('INTERMEDIATE', 'Intermediate Hole', True, True, False, False, False, False, False, False,
             False, True, True, 'Intermediate casing hole section'),
            ('PRODUCTION', 'Production Hole', True, True, True, False, True, False, True, False,
             True, True, True, 'Production casing/reservoir section'),
        ]

        created_count = 0
        for i, data in enumerate(applications):
            (code, name, vertical, directional, horizontal, curve, lateral, motor, rss, turbine,
             steerability, rop, durability, desc) = data
            obj, created = Application.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'is_vertical': vertical,
                    'is_directional': directional,
                    'is_horizontal': horizontal,
                    'is_curve': curve,
                    'is_lateral': lateral,
                    'is_motor': motor,
                    'is_rss': rss,
                    'is_turbine': turbine,
                    'requires_high_steerability': steerability,
                    'requires_high_rop': rop,
                    'requires_durability': durability,
                    'description': desc,
                    'display_order': i * 10,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} applications')
