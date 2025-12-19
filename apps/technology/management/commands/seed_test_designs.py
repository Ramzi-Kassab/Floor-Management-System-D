"""
Seed command for test designs data.
Creates sample bit designs for testing pockets layout.
"""
from django.core.management.base import BaseCommand
from apps.technology.models import Design, DesignPocketConfig, PocketSize, PocketShape
from apps.workorders.models import BitSize


class Command(BaseCommand):
    help = 'Seeds test bit designs for development'

    def handle(self, *args, **options):
        # Get or create bit sizes
        sizes = {
            '8.5': BitSize.objects.filter(size_inches__contains='8 1/2').first(),
            '12.25': BitSize.objects.filter(size_inches__contains='12 1/4').first(),
            '6': BitSize.objects.filter(size_inches__contains='6').first(),
        }

        # Get pocket sizes and shapes
        pocket_sizes = list(PocketSize.objects.filter(is_active=True)[:5])
        pocket_shapes = list(PocketShape.objects.filter(is_active=True)[:3])

        if not pocket_sizes or not pocket_shapes:
            self.stdout.write(self.style.WARNING('Run pocket seeds first: seed_pocket_sizes, seed_pocket_shapes'))
            return

        # Sample designs data
        designs_data = [
            {
                'mat_no': '1276939M2',
                'hdbs_type': 'GT65RHs',
                'smi_type': 'GT65RHs',
                'category': 'FC',
                'no_of_blades': 6,
                'total_pockets_count': 48,
                'pocket_rows_count': 2,
                'series': 'GT',
                'body_material': 'S',
                'status': 'DRAFT',
            },
            {
                'mat_no': '1287456M1',
                'hdbs_type': 'HD75MXs',
                'smi_type': 'HD75MX',
                'category': 'FC',
                'no_of_blades': 5,
                'total_pockets_count': 40,
                'pocket_rows_count': 2,
                'series': 'HD',
                'body_material': 'M',
                'status': 'ACTIVE',
            },
            {
                'mat_no': '1298765M3',
                'hdbs_type': 'EM55RSs',
                'smi_type': 'EM55RS',
                'category': 'FC',
                'no_of_blades': 4,
                'total_pockets_count': 32,
                'pocket_rows_count': 1,
                'series': 'EM',
                'body_material': 'S',
                'status': 'DRAFT',
            },
        ]

        created_count = 0
        updated_count = 0

        for i, data in enumerate(designs_data):
            size_key = list(sizes.keys())[i % len(sizes)]
            data['size'] = sizes[size_key]

            design, created = Design.objects.update_or_create(
                mat_no=data['mat_no'],
                defaults=data
            )

            if created:
                created_count += 1
                # Add pocket configs for new designs
                colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
                for j, pocket_size in enumerate(pocket_sizes[:3]):
                    DesignPocketConfig.objects.get_or_create(
                        design=design,
                        order=j + 1,
                        defaults={
                            'pocket_size': pocket_size,
                            'pocket_shape': pocket_shapes[j % len(pocket_shapes)],
                            'length_type': ['L', 'M', 'S'][j % 3],
                            'count': 8 + j * 2,
                            'color_code': colors[j % len(colors)],
                            'row_number': 1 if j < 2 else 2,
                        }
                    )
                self.stdout.write(f'  Created: {design.mat_no} - {design.hdbs_type}')
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {design.mat_no} - {design.hdbs_type}')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Designs: {created_count} created, {updated_count} updated'
        ))
