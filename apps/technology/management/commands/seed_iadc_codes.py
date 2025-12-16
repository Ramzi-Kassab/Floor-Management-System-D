"""
Seed IADC classification codes reference data.
"""
from django.core.management.base import BaseCommand
from apps.technology.models import IADCCode


class Command(BaseCommand):
    help = 'Seed IADC classification codes reference data'

    def handle(self, *args, **options):
        # PDC Bits (Fixed Cutter)
        # code, bit_type, body_material, formation_hardness, cutter_type, profile, description
        pdc_data = [
            ('M122', 'FC', 'M', '1', '2', '2', 'Matrix, soft formation, 13mm cutters, short profile'),
            ('M222', 'FC', 'M', '2', '2', '2', 'Matrix, soft-medium formation'),
            ('M323', 'FC', 'M', '3', '2', '3', 'Matrix, medium formation, medium profile'),
            ('M423', 'FC', 'M', '4', '2', '3', 'Matrix, medium-hard formation'),
            ('M433', 'FC', 'M', '4', '3', '3', 'Matrix, medium-hard, 16mm cutters'),
            ('M443', 'FC', 'M', '4', '4', '3', 'Matrix, medium-hard, 19mm cutters'),
            ('M523', 'FC', 'M', '5', '2', '3', 'Matrix, hard formation'),
            ('M533', 'FC', 'M', '5', '3', '3', 'Matrix, hard, 16mm cutters'),
            ('M623', 'FC', 'M', '6', '2', '3', 'Matrix, very hard formation'),
            ('S323', 'FC', 'S', '3', '2', '3', 'Steel body, medium formation'),
            ('S423', 'FC', 'S', '4', '2', '3', 'Steel body, medium-hard formation'),
            ('S433', 'FC', 'S', '4', '3', '3', 'Steel body, medium-hard, 16mm cutters'),
            ('S523', 'FC', 'S', '5', '2', '3', 'Steel body, hard formation'),
        ]

        # Mill Tooth Bits (Series 1-3)
        # code, bit_type, series, type_code, bearing, feature, description
        mt_data = [
            ('111', 'MT', '1', '1', '1', '', 'Soft, standard roller bearing'),
            ('115', 'MT', '1', '1', '5', '', 'Soft, sealed roller + gauge'),
            ('117', 'MT', '1', '1', '7', '', 'Soft, sealed journal + gauge'),
            ('121', 'MT', '1', '2', '1', '', 'Soft-medium, standard roller'),
            ('211', 'MT', '2', '1', '1', '', 'Medium, standard roller'),
            ('217', 'MT', '2', '1', '7', '', 'Medium, sealed journal + gauge'),
            ('311', 'MT', '3', '1', '1', '', 'Hard, standard roller'),
            ('317', 'MT', '3', '1', '7', '', 'Hard, sealed journal + gauge'),
        ]

        # TCI Bits (Series 4-8)
        tci_data = [
            ('417', 'TCI', '4', '1', '7', '', 'Soft, TCI, sealed journal + gauge'),
            ('437', 'TCI', '4', '3', '7', '', 'Soft-medium, TCI'),
            ('517', 'TCI', '5', '1', '7', '', 'Medium, TCI'),
            ('517X', 'TCI', '5', '1', '7', 'X', 'Medium, TCI, chisel inserts'),
            ('537', 'TCI', '5', '3', '7', '', 'Medium-hard, TCI'),
            ('617', 'TCI', '6', '1', '7', '', 'Hard, TCI'),
            ('637', 'TCI', '6', '3', '7', '', 'Very hard, TCI'),
            ('717', 'TCI', '7', '1', '7', '', 'Extremely hard, TCI'),
            ('817', 'TCI', '8', '1', '7', '', 'Abrasive, TCI'),
        ]

        created = 0

        # Create PDC codes
        for code, bit_type, body, form_hard, cutter, profile, desc in pdc_data:
            obj, was_created = IADCCode.objects.get_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'body_material': body,
                    'formation_hardness': form_hard,
                    'cutter_type': cutter,
                    'profile': profile,
                    'description': desc,
                }
            )
            if was_created:
                created += 1

        # Create Mill Tooth codes
        for code, bit_type, series, type_c, bearing, feature, desc in mt_data:
            obj, was_created = IADCCode.objects.get_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'series': series,
                    'type_code': type_c,
                    'bearing': bearing,
                    'feature': feature,
                    'description': desc,
                }
            )
            if was_created:
                created += 1

        # Create TCI codes
        for code, bit_type, series, type_c, bearing, feature, desc in tci_data:
            obj, was_created = IADCCode.objects.get_or_create(
                code=code,
                defaults={
                    'bit_type': bit_type,
                    'series': series,
                    'type_code': type_c,
                    'bearing': bearing,
                    'feature': feature,
                    'description': desc,
                }
            )
            if was_created:
                created += 1

        total = len(pdc_data) + len(mt_data) + len(tci_data)
        self.stdout.write(self.style.SUCCESS(f'IADCCode: {created} created, {total - created} already exist'))
