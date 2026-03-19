"""
Seed the ARDT Business Unit accounts.

Business Units are the top-level commercial groupings for drill bits.
Each bit belongs to one Business Unit (= Account).

Usage:
    python manage.py seed_accounts --confirm
"""
from django.core.management.base import BaseCommand
from apps.sales.models import Account


ACCOUNTS = [
    {
        'code': 'GAS',
        'name': 'Gas',
        'wo_prefix': 'GAS',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 1,
        'description': 'Gas business unit. New bits (L3/L4).',
    },
    {
        'code': 'UR-SALES',
        'name': 'UR Sales',
        'wo_prefix': 'UR',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 2,
        'description': 'UR Sales business unit. New bits (L3/L4).',
    },
    {
        'code': 'EXP',
        'name': 'Exp',
        'wo_prefix': 'EXP',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 3,
        'description': 'Exp business unit. New bits (L3/L4).',
    },
    {
        'code': 'OFFSHORE',
        'name': 'Offshore',
        'wo_prefix': 'OFF',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 4,
        'description': 'Offshore business unit. New bits (L3/L4).',
    },
    {
        'code': 'OIL',
        'name': 'Oil',
        'wo_prefix': 'OIL',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 5,
        'description': 'Oil business unit. New bits (L3/L4).',
    },
    {
        'code': 'UR-SPERRY',
        'name': 'UR Rental - Sperry',
        'wo_prefix': 'UR',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYY-UR-NNNN',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 6,
        'description': 'UR Rental - Sperry. Repair UR bits.',
    },
    {
        'code': 'UR-OTHER',
        'name': 'UR Rental - Other',
        'wo_prefix': 'UR',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYY-UR-NNNN',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 7,
        'description': 'UR Rental - Other (WFD, TAQA, other rental projects). Repair UR bits.',
    },
    {
        'code': 'LSTK',
        'name': 'LSTK',
        'wo_prefix': '',
        'wo_format': Account.WOFormat.NUMERIC,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': 'YYYYNNNN (e.g. 20251001)',
        'contract_number': '960031408',
        'pricing_mode': Account.PricingMode.LSTK,
        'workflow_type': Account.WorkflowType.BOTH,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 8,
        'description': 'LSTK (Halliburton Consignment). Can be new or repair — determined by bit data.',
    },
    {
        'code': 'ARAMCO',
        'name': 'Aramco Repair',
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
        'sort_order': 9,
        'description': 'Saudi Aramco direct contract. Max 2 repairs (R, R2 then scrap). 8-digit serials.',
    },
    {
        'code': 'TTR',
        'name': 'TTR',
        'wo_prefix': 'TTR',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.BOTH,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 10,
        'description': 'Trial Test Bits. Can be new or repair.',
    },
    {
        'code': 'DEBRAZE',
        'name': 'Debraze',
        'wo_prefix': 'DBZ',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.REPAIR,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 11,
        'description': 'Debraze. Bits 3+ years after production.',
    },
    {
        'code': 'SAFETY-STOCK',
        'name': 'Build up Safety Stock',
        'wo_prefix': 'SS',
        'wo_format': Account.WOFormat.STANDARD,
        'wo_suffix': '',
        'wo_seq_padding': 4,
        'wo_seq_start': 1001,
        'legacy_wo_format': '',
        'contract_number': '',
        'pricing_mode': Account.PricingMode.STANDARD,
        'workflow_type': Account.WorkflowType.MANUFACTURE,
        'max_repairs': None,
        'repair_suffix_format': '',
        'delivery_location': 'HDBS Warehouse',
        'reviewer_label': 'Reviewed by Eng.',
        'sort_order': 12,
        'description': 'Build up Safety Stock. New bits (L3, L4, L5.5).',
    },
]


class Command(BaseCommand):
    help = 'Seed the ARDT Business Unit accounts'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create/update accounts')

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write('Dry run. Pass --confirm to create/update accounts.')
            for a in ACCOUNTS:
                self.stdout.write(f"  {a['code']:15s} {a['name']}")
            return

        # Deactivate old accounts that are not in the new list
        new_codes = {a['code'] for a in ACCOUNTS}
        old_accounts = Account.objects.exclude(code__in=new_codes)
        deactivated = old_accounts.filter(is_active=True).update(is_active=False)
        if deactivated:
            self.stdout.write(self.style.WARNING(f'  Deactivated {deactivated} old account(s)'))

        created_count = 0
        updated_count = 0
        for data in ACCOUNTS:
            code = data.pop('code')
            name = data.pop('name')
            data['is_active'] = True  # Re-activate if previously deactivated
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
            f'\nDone. Created: {created_count}, Updated: {updated_count}, Deactivated: {deactivated}, Total active: {len(ACCOUNTS)}'
        ))
