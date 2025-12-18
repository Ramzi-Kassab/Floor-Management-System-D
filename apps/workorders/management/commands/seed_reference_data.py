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
from apps.technology.models import (
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
        - Cutter Size: 1=Large, 2=Medium-Large, 3=Medium, 4=Small
        - Profile: 1=Fishtail, 2=Short, 3=Medium, 4=Long

        Roller Cone Format: [Series][Type][Bearing][Feature]
        - Series: 1-3=Milled Tooth, 4-8=TCI
        """
        self.stdout.write('Seeding IADC codes...')

        # PDC codes - (code, bit_type, body_material, formation_hardness, cutter_type, profile, description, formation_desc)
        pdc_codes = [
            # M1xx - Soft formations
            ('M115', 'FC', 'M', '1', '1', '5', 'Matrix PDC for soft formations, large cutters', 'Soft'),
            ('M122', 'FC', 'M', '1', '2', '2', 'Matrix PDC for soft formations, 19mm cutters, short profile', 'Soft'),
            ('M127', 'FC', 'M', '1', '2', '7', 'Matrix PDC for soft formations, 19mm cutters', 'Soft'),
            # M2xx - Soft to Medium formations
            ('M211', 'FC', 'M', '2', '1', '1', 'Matrix PDC for soft-medium formations, large cutters, fishtail', 'Soft-Medium'),
            ('M222', 'FC', 'M', '2', '2', '2', 'Matrix PDC for soft-medium formations, 19mm cutters', 'Soft-Medium'),
            ('M223', 'FC', 'M', '2', '2', '3', 'Matrix PDC for soft-medium formations', 'Soft-Medium'),
            ('M232', 'FC', 'M', '2', '3', '2', 'Matrix PDC for soft-medium formations, 13mm cutters', 'Soft-Medium'),
            ('M233', 'FC', 'M', '2', '3', '3', 'Matrix PDC for soft-medium formations', 'Soft-Medium'),
            ('M243', 'FC', 'M', '2', '4', '3', 'Matrix PDC for soft-medium formations, small cutters', 'Soft-Medium'),
            # M3xx - Medium formations
            ('M322', 'FC', 'M', '3', '2', '2', 'Matrix PDC for medium formations', 'Medium'),
            ('M323', 'FC', 'M', '3', '2', '3', 'Matrix PDC for medium formations', 'Medium'),
            ('M324', 'FC', 'M', '3', '2', '4', 'Matrix PDC for medium formations, long profile', 'Medium'),
            ('M332', 'FC', 'M', '3', '3', '2', 'Matrix PDC for medium formations, 13mm cutters', 'Medium'),
            ('M333', 'FC', 'M', '3', '3', '3', 'Matrix PDC for medium formations', 'Medium'),
            ('M334', 'FC', 'M', '3', '3', '4', 'Matrix PDC for medium formations', 'Medium'),
            ('M343', 'FC', 'M', '3', '4', '3', 'Matrix PDC for medium formations, small cutters', 'Medium'),
            ('M344', 'FC', 'M', '3', '4', '4', 'Matrix PDC for medium formations', 'Medium'),
            # M4xx - Medium to Hard formations
            ('M422', 'FC', 'M', '4', '2', '2', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            ('M423', 'FC', 'M', '4', '2', '3', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            ('M432', 'FC', 'M', '4', '3', '2', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            ('M433', 'FC', 'M', '4', '3', '3', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            ('M434', 'FC', 'M', '4', '3', '4', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            ('M442', 'FC', 'M', '4', '4', '2', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            ('M443', 'FC', 'M', '4', '4', '3', 'Matrix PDC for medium-hard formations', 'Medium-Hard'),
            # M6xx - Hard formations
            ('M613', 'FC', 'M', '6', '1', '3', 'Matrix PDC for hard formations', 'Hard'),
            ('M622', 'FC', 'M', '6', '2', '2', 'Matrix PDC for hard formations', 'Hard'),
            ('M623', 'FC', 'M', '6', '2', '3', 'Matrix PDC for hard formations', 'Hard'),
            # M7xx - Very Hard formations
            ('M712', 'FC', 'M', '7', '1', '2', 'Matrix PDC for very hard formations', 'Very Hard'),
            ('M713', 'FC', 'M', '7', '1', '3', 'Matrix PDC for very hard formations', 'Very Hard'),
            # Steel body PDC
            ('S122', 'FC', 'S', '1', '2', '2', 'Steel PDC for soft formations', 'Soft'),
            ('S211', 'FC', 'S', '2', '1', '1', 'Steel PDC for soft-medium formations', 'Soft-Medium'),
            ('S222', 'FC', 'S', '2', '2', '2', 'Steel PDC for soft-medium formations', 'Soft-Medium'),
            ('S223', 'FC', 'S', '2', '2', '3', 'Steel PDC for soft-medium formations', 'Soft-Medium'),
            ('S232', 'FC', 'S', '2', '3', '2', 'Steel PDC for soft-medium formations', 'Soft-Medium'),
            ('S233', 'FC', 'S', '2', '3', '3', 'Steel PDC for soft-medium formations', 'Soft-Medium'),
            ('S322', 'FC', 'S', '3', '2', '2', 'Steel PDC for medium formations', 'Medium'),
            ('S323', 'FC', 'S', '3', '2', '3', 'Steel PDC for medium formations', 'Medium'),
            ('S332', 'FC', 'S', '3', '3', '2', 'Steel PDC for medium formations', 'Medium'),
            ('S333', 'FC', 'S', '3', '3', '3', 'Steel PDC for medium formations', 'Medium'),
            ('S343', 'FC', 'S', '3', '4', '3', 'Steel PDC for medium formations', 'Medium'),
            ('S422', 'FC', 'S', '4', '2', '2', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            ('S423', 'FC', 'S', '4', '2', '3', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            ('S432', 'FC', 'S', '4', '3', '2', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            ('S433', 'FC', 'S', '4', '3', '3', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            ('S434', 'FC', 'S', '4', '3', '4', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            ('S442', 'FC', 'S', '4', '4', '2', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            ('S443', 'FC', 'S', '4', '4', '3', 'Steel PDC for medium-hard formations', 'Medium-Hard'),
            # Diamond body PDC
            ('D433', 'FC', 'D', '4', '3', '3', 'Diamond PDC for medium-hard formations', 'Medium-Hard'),
            ('D443', 'FC', 'D', '4', '4', '3', 'Diamond PDC for medium-hard formations', 'Medium-Hard'),
        ]

        # Roller Cone codes - (code, bit_type, series, type_code, bearing, feature, description, formation_desc)
        rc_codes = [
            # Series 1 - Milled Tooth Soft
            ('115', 'MT', '1', '1', '5', '', 'Milled Tooth for soft formations', 'Soft'),
            ('117', 'MT', '1', '1', '7', '', 'Milled Tooth for soft formations', 'Soft'),
            ('127', 'MT', '1', '2', '7', '', 'Milled Tooth for soft formations', 'Soft'),
            ('136', 'MT', '1', '3', '6', '', 'Milled Tooth for soft formations', 'Soft'),
            ('137', 'MT', '1', '3', '7', '', 'Milled Tooth for soft formations', 'Soft'),
            # Series 2 - Milled Tooth Medium
            ('211', 'MT', '2', '1', '1', '', 'Milled Tooth for medium formations', 'Medium'),
            ('214', 'MT', '2', '1', '4', '', 'Milled Tooth for medium formations', 'Medium'),
            ('217', 'MT', '2', '1', '7', '', 'Milled Tooth for medium formations', 'Medium'),
            # Series 3 - Milled Tooth Hard
            ('311', 'MT', '3', '1', '1', '', 'Milled Tooth for hard formations', 'Hard'),
            ('317', 'MT', '3', '1', '7', '', 'Milled Tooth for hard formations', 'Hard'),
            ('322', 'MT', '3', '2', '2', '', 'Milled Tooth for hard formations', 'Hard'),
            # Series 4 - TCI Soft
            ('415', 'TCI', '4', '1', '5', '', 'TCI for soft formations', 'Soft'),
            ('417', 'TCI', '4', '1', '7', '', 'TCI for soft formations', 'Soft'),
            ('425', 'TCI', '4', '2', '5', '', 'TCI for soft formations', 'Soft'),
            ('435', 'TCI', '4', '3', '5', '', 'TCI for soft formations', 'Soft'),
            ('437', 'TCI', '4', '3', '7', '', 'TCI for soft formations', 'Soft'),
            ('445', 'TCI', '4', '4', '5', '', 'TCI for soft formations', 'Soft'),
            ('447', 'TCI', '4', '4', '7', '', 'TCI for soft formations', 'Soft'),
            # Series 5 - TCI Medium
            ('511', 'TCI', '5', '1', '1', '', 'TCI for medium formations', 'Medium'),
            ('515', 'TCI', '5', '1', '5', '', 'TCI for medium formations', 'Medium'),
            ('517', 'TCI', '5', '1', '7', '', 'TCI for medium formations', 'Medium'),
            ('517X', 'TCI', '5', '1', '7', 'X', 'TCI for medium formations with enhanced gauge', 'Medium'),
            ('525', 'TCI', '5', '2', '5', '', 'TCI for medium formations', 'Medium'),
            ('527', 'TCI', '5', '2', '7', '', 'TCI for medium formations', 'Medium'),
            ('535', 'TCI', '5', '3', '5', '', 'TCI for medium formations', 'Medium'),
            ('537', 'TCI', '5', '3', '7', '', 'TCI for medium formations', 'Medium'),
            ('537X', 'TCI', '5', '3', '7', 'X', 'TCI for medium formations with enhanced gauge', 'Medium'),
            ('545', 'TCI', '5', '4', '5', '', 'TCI for medium formations', 'Medium'),
            ('547', 'TCI', '5', '4', '7', '', 'TCI for medium formations', 'Medium'),
            # Series 6 - TCI Medium-Hard
            ('615', 'TCI', '6', '1', '5', '', 'TCI for medium-hard formations', 'Medium-Hard'),
            ('617', 'TCI', '6', '1', '7', '', 'TCI for medium-hard formations', 'Medium-Hard'),
            ('617X', 'TCI', '6', '1', '7', 'X', 'TCI for medium-hard with enhanced gauge', 'Medium-Hard'),
            ('625', 'TCI', '6', '2', '5', '', 'TCI for medium-hard formations', 'Medium-Hard'),
            ('627', 'TCI', '6', '2', '7', '', 'TCI for medium-hard formations', 'Medium-Hard'),
            ('627Y', 'TCI', '6', '2', '7', 'Y', 'TCI for medium-hard with conical inserts', 'Medium-Hard'),
            ('635', 'TCI', '6', '3', '5', '', 'TCI for medium-hard formations', 'Medium-Hard'),
            ('637', 'TCI', '6', '3', '7', '', 'TCI for medium-hard formations', 'Medium-Hard'),
            # Series 7 - TCI Hard
            ('715', 'TCI', '7', '1', '5', '', 'TCI for hard formations', 'Hard'),
            ('717', 'TCI', '7', '1', '7', '', 'TCI for hard formations', 'Hard'),
            ('725', 'TCI', '7', '2', '5', '', 'TCI for hard formations', 'Hard'),
            ('727', 'TCI', '7', '2', '7', '', 'TCI for hard formations', 'Hard'),
            ('735', 'TCI', '7', '3', '5', '', 'TCI for hard formations', 'Hard'),
            ('737', 'TCI', '7', '3', '7', '', 'TCI for hard formations', 'Hard'),
            # Series 8 - TCI Extremely Hard
            ('815', 'TCI', '8', '1', '5', '', 'TCI for extremely hard formations', 'Extremely Hard'),
            ('817', 'TCI', '8', '1', '7', '', 'TCI for extremely hard formations', 'Extremely Hard'),
            ('827', 'TCI', '8', '2', '7', '', 'TCI for extremely hard formations', 'Extremely Hard'),
            ('837', 'TCI', '8', '3', '7', '', 'TCI for extremely hard formations', 'Extremely Hard'),
            ('847', 'TCI', '8', '4', '7', '', 'TCI for extremely hard formations', 'Extremely Hard'),
        ]

        created_count = 0

        # Insert PDC codes
        for code_data in pdc_codes:
            code, bit_type, body_mat, formation, cutter, profile, desc, form_desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'body_material': body_mat,
                    'formation_hardness': formation,
                    'cutter_type': cutter,
                    'profile': profile,
                    'description': desc,
                    'formation_description': form_desc,
                }
            )
            if created:
                created_count += 1

        # Insert Roller Cone codes
        for code_data in rc_codes:
            code, bit_type, series, type_code, bearing, feature, desc, form_desc = code_data
            obj, created = IADCCode.objects.update_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'series': series,
                    'type_code': type_code,
                    'bearing': bearing,
                    'feature': feature,
                    'description': desc,
                    'formation_description': form_desc,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} IADC codes')

    def seed_connection_types(self):
        """Seed API connection types."""
        self.stdout.write('Seeding connection types...')

        # (code, name, description)
        connection_types = [
            ('API-REG', 'API Regular', 'API Regular rotary shouldered connection'),
            ('API-IF', 'API Internal Flush', 'API Internal Flush connection'),
            ('API-FH', 'API Full Hole', 'API Full Hole connection'),
            ('NC', 'Numbered Connection', 'API Numbered Connection series'),
            ('HT', 'Hi-Torque', 'High torque connection for demanding applications'),
            ('XT', 'Extreme Torque', 'Extreme torque connection'),
            ('PAC', 'PAC Connection', 'PAC proprietary connection'),
            ('DS', 'Double Shoulder', 'Double shoulder connection for high torque'),
            ('GPDS', 'Grant Prideco DS', 'Grant Prideco Double Shoulder'),
        ]

        created_count = 0
        for code, name, desc in connection_types:
            obj, created = ConnectionType.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} connection types')

    def seed_connection_sizes(self):
        """Seed connection sizes."""
        self.stdout.write('Seeding connection sizes...')

        # (code, size_inches, size_decimal, description)
        connection_sizes = [
            ('2-3/8 REG', '2-3/8"', 2.375, 'API Regular 2-3/8 inch'),
            ('2-7/8 REG', '2-7/8"', 2.875, 'API Regular 2-7/8 inch'),
            ('3-1/2 REG', '3-1/2"', 3.500, 'API Regular 3-1/2 inch'),
            ('4-1/2 REG', '4-1/2"', 4.500, 'API Regular 4-1/2 inch'),
            ('6-5/8 REG', '6-5/8"', 6.625, 'API Regular 6-5/8 inch'),
            ('7-5/8 REG', '7-5/8"', 7.625, 'API Regular 7-5/8 inch'),
            ('2-3/8 IF', '2-3/8"', 2.375, 'API IF 2-3/8 inch'),
            ('2-7/8 IF', '2-7/8"', 2.875, 'API IF 2-7/8 inch'),
            ('3-1/2 IF', '3-1/2"', 3.500, 'API IF 3-1/2 inch'),
            ('4-1/2 IF', '4-1/2"', 4.500, 'API IF 4-1/2 inch'),
            ('NC26', 'NC26', 2.625, 'API NC26'),
            ('NC31', 'NC31', 3.125, 'API NC31'),
            ('NC38', 'NC38', 3.750, 'API NC38'),
            ('NC40', 'NC40', 4.000, 'API NC40'),
            ('NC46', 'NC46', 4.625, 'API NC46'),
            ('NC50', 'NC50', 5.000, 'API NC50'),
            ('NC56', 'NC56', 5.625, 'API NC56'),
            ('5-1/2 FH', '5-1/2"', 5.500, 'API FH 5-1/2 inch'),
            ('6-5/8 FH', '6-5/8"', 6.625, 'API FH 6-5/8 inch'),
            ('HT31', 'HT31', 3.125, 'Hi-Torque 31'),
            ('HT38', 'HT38', 3.750, 'Hi-Torque 38'),
            ('HT55', 'HT55', 5.500, 'Hi-Torque 55'),
        ]

        created_count = 0
        for code, size_inches, size_decimal, desc in connection_sizes:
            obj, created = ConnectionSize.objects.update_or_create(
                code=code,
                defaults={
                    'size_inches': size_inches,
                    'size_decimal': size_decimal,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} connection sizes')

    def seed_formation_types(self):
        """Seed Saudi Arabia formation types."""
        self.stdout.write('Seeding formation types...')

        # (code, name, age, rock_type, hardness, description)
        formation_types = [
            ('ARAB-D', 'Arab-D', 'Jurassic', 'Carbonate', 'Medium', 'Main oil reservoir in Ghawar field'),
            ('ARAB-C', 'Arab-C', 'Jurassic', 'Carbonate', 'Medium', 'Secondary reservoir'),
            ('ARAB-B', 'Arab-B', 'Jurassic', 'Carbonate', 'Medium-Hard', 'Anhydrite cap rock'),
            ('ARAB-A', 'Arab-A', 'Jurassic', 'Carbonate', 'Hard', 'Dense limestone'),
            ('KHUFF', 'Khuff', 'Permian', 'Carbonate', 'Hard', 'Deep gas reservoir, high H2S'),
            ('UNAYZAH', 'Unayzah', 'Permian', 'Sandstone', 'Medium', 'Clastic reservoir'),
            ('JAUF', 'Jauf', 'Devonian', 'Sandstone', 'Medium-Hard', 'Deep clastic'),
            ('QUSAIBA', 'Qusaiba', 'Silurian', 'Shale', 'Soft', 'Hot shale source rock'),
            ('SARAH', 'Sarah', 'Ordovician', 'Sandstone', 'Hard', 'Glacial sandstone'),
            ('SHUAIBA', 'Shuaiba', 'Cretaceous', 'Carbonate', 'Medium', 'Shallow carbonate'),
            ('WASIA', 'Wasia', 'Cretaceous', 'Sandstone', 'Soft-Medium', 'Shallow clastic'),
            ('ARUMA', 'Aruma', 'Cretaceous', 'Carbonate', 'Medium', 'Upper carbonate'),
            ('UMM ER RADHUMA', 'Umm Er Radhuma', 'Paleocene', 'Carbonate', 'Soft', 'Water aquifer'),
            ('DAMMAM', 'Dammam', 'Eocene', 'Carbonate', 'Soft-Medium', 'Shallow formation'),
            ('HADRUKH', 'Hadrukh', 'Miocene', 'Sandstone', 'Soft', 'Surface formation'),
            ('DAM', 'Dam', 'Miocene', 'Carbonate', 'Soft', 'Surface formation'),
        ]

        created_count = 0
        for code, name, age, rock_type, hardness, desc in formation_types:
            obj, created = FormationType.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'age': age,
                    'rock_type': rock_type,
                    'hardness': hardness,
                    'description': desc,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} formation types')

    def seed_applications(self):
        """Seed drilling application types."""
        self.stdout.write('Seeding applications...')

        # (code, name, description)
        applications = [
            ('VERT', 'Vertical', 'Vertical drilling application'),
            ('DIR', 'Directional', 'Directional drilling with motor'),
            ('HORZ', 'Horizontal', 'Horizontal drilling application'),
            ('RSS', 'Rotary Steerable', 'Rotary Steerable System application'),
            ('MOTOR', 'Motor', 'Positive displacement motor drilling'),
            ('TURBINE', 'Turbine', 'Turbine drilling application'),
            ('CURVE', 'Curve/Build', 'Building angle in curve section'),
            ('LATERAL', 'Lateral', 'Horizontal lateral section'),
            ('TANGENT', 'Tangent', 'Tangent/hold section'),
            ('REAMING', 'Reaming', 'Reaming/hole opening application'),
            ('CORING', 'Coring', 'Core drilling application'),
            ('PDM', 'PDM Drilling', 'Positive Displacement Motor drilling'),
        ]

        created_count = 0
        for code, name, desc in applications:
            obj, created = Application.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} applications')
