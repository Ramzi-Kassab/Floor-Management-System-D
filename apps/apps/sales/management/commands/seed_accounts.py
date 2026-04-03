"""
Seed the 11 ARDT Work Order accounts with correct WO formats and configuration.

Usage:
    python manage.py seed_accounts --confirm
"""
from django.core.management.base import BaseCommand
from apps.sales.models import Account


ACCOUNTS = [
    {
        'code': 'LSTK',
        'name': 'LSTK (Halliburton Consignment)',
        'wo_prefix': '',
        'wo_format': Account.WOFormat.NUMERIC,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYYNNNN (e.g. 20251001)',
        'contract_number': '960031408',
        'pricing_mode': Account.PricingMode.LSTK,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 1,
        'description': 'Halliburton consignment stock. Largest account (~2100 WOs). Bits owned by Halliburton, repaired by ARDT.',
    },
    {
        'code': 'UR',
        'name': 'Used & Reconditioned',
        'wo_prefix': 'UR',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYY-UR-NNNN (e.g. 2024-UR-1001)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 2,
        'description': 'Used & Reconditioned bits. Special cutter replacement rules for specific MAT numbers.',
    },
    {
        'code': 'L3',
        'name': 'Level 3 (New Build)',
        'wo_prefix': 'ARDT-LV3',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 3,
        'wo_seq_start': 1,
        'legacy_wo_format': 'YYYY-ARDT-LV3-NNN (e.g. 2019-ARDT-LV3-01)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 3,
        'description': 'Level 3 new bit manufacturing from components. No incoming bit — built from scratch.',
    },
    {
        'code': 'L4',
        'name': 'Level 4 (New Build with Pockets)',
        'wo_prefix': 'ARDT-LV4',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 3,
        'wo_seq_start': 1,
        'legacy_wo_format': 'YYYY-ARDT-LV4-NNN (e.g. 2020-ARDT-LV4-01)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 4,
        'description': 'Level 4 new bit manufacturing with pocket assignments defined.',
    },
    {
        'code': 'ARDT',
        'name': 'ARDT (Own Stock)',
        'wo_prefix': 'ARDT',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 3,
        'wo_seq_start': 1,
        'legacy_wo_format': 'YYYY-ARDT-NNN (e.g. 2019-ARDT-084)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.BOTH,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 5,
        'description': 'ARDT-owned bits. Standard repair, modifications, trial test bits.',
    },
    {
        'code': 'WFD',
        'name': 'Wait For Disposition',
        'wo_prefix': 'WFD',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYY-WFD-NNNN (e.g. 2023-WFD-1001)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 6,
        'description': 'Bits waiting for disposition decision (repair, scrap, or return).',
    },
    {
        'code': 'ARAMCO',
        'name': 'Saudi Aramco',
        'wo_prefix': 'AR',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 3,
        'wo_seq_start': 1,
        'legacy_wo_format': 'YYYY-AR-NNN (e.g. 2018-AR-001)',
        'contract_number': '6600048646',
        'pricing_mode': Account.PricingMode.ARAMCO,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': 2,
        'repair_suffix_format': 'R{n}',
        'delivery_location': 'ARAMCO Warehouse',
        'reviewer_label': 'DTD/TSSD:',
        'sort_order': 7,
        'description': 'Saudi Aramco direct contract. Max 2 repairs (R, R2 then scrap). 8-digit serials. Separate pricing and evaluation.',
    },
    {
        'code': 'RC-LSTK',
        'name': 'Roller Cone LSTK',
        'wo_prefix': 'RC',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 3,
        'wo_seq_start': 1,
        'legacy_wo_format': 'YYYY-RC-NNN (e.g. 2024-RC-003)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.LSTK,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 8,
        'description': 'Roller Cone bits under LSTK consignment. Separate inspection workflow.',
    },
    {
        'code': 'HALLIBURTON',
        'name': 'Halliburton Direct',
        'wo_prefix': '',
        'wo_format': Account.WOFormat.SUFFIX,
        'wo_suffix': 'HDBSC',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYYNNNN-HDBSC (e.g. 20181001-HDBSC)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.ZERO,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 9,
        'description': 'Direct Halliburton work. Pricing zeroed out (partner).',
    },
    {
        'code': 'HAL_REGIONAL',
        'name': 'Halliburton Regional',
        'wo_prefix': '',
        'wo_format': Account.WOFormat.SUFFIX,
        'wo_suffix': 'REG',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYYNNNN-REG (e.g. 20181001-REG)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.ZERO,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 10,
        'description': 'Halliburton regional work. Pricing zeroed out (partner).',
    },
    {
        'code': 'SUB',
        'name': 'Sub (Drill String Component)',
        'wo_prefix': 'SUB',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 3,
        'wo_seq_start': 1,
        'legacy_wo_format': 'YYYY-SUB-NNN (e.g. 2021-SUB-001)',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 11,
        'description': 'Drill string subs — short pipe sections with sensors, serialized like bits.',
    },
]


class Command(BaseCommand):
    help = 'Seed the 11 ARDT Work Order accounts'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create/update accounts')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to create/update accounts.')
            for a in ACCOUNTS:
                self.stdout.write(f"  {a['code']:15s} {a['wo_format']:10s} prefix={a['wo_prefix']!r:15s} suffix={a['wo_suffix']!r:10s} max_repairs={a['max_repairs']}")
            return

        created_count = 0
        updated_count = 0
        for data in ACCOUNTS:
            code = data.pop('code')
            name = data.pop('name')
            obj, created = Account.objects.update_or_create(
                code=code,
                defaults={'name': name, **data}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {code} - {name}'))
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {code} - {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created: {created_count}, Updated: {updated_count}, Total: {len(ACCOUNTS)}'
        ))
