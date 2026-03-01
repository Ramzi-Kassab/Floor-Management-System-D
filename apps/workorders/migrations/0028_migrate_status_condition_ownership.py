"""
Data migration: Convert existing DrillBit records from old Status+Lifecycle model
to new Status+Condition+Ownership model.

Mapping logic:
- OLD Status + Lifecycle → NEW Status + Condition
- Account → Ownership (via ACCOUNT_OWNERSHIP_MAP)

OLD Status values:     UNREGISTERED, NEW, IN_STOCK, ASSIGNED, IN_PRODUCTION,
                       QC_PENDING, READY, DISPATCHED, IN_FIELD, RETURNED, SCRAPPED

OLD Lifecycle values:  NEW, DEPLOYED, BACKLOADED, EVALUATION, HOLD, IN_REPAIR,
                       REPAIRED, USA_REPAIR, RERUN, SCRAP, SAVED_BODY
"""
from django.db import migrations


# Account code → Ownership mapping
ACCOUNT_OWNERSHIP = {
    'UR': 'RENTAL',
    'WFD': 'RENTAL',
    'ARAMCO': 'CUSTOMER',
    'LSTK': 'CUSTOMER',
    'RC-LSTK': 'CUSTOMER',
    'HALLIBURTON': 'CUSTOMER',
    'HAL_REGIONAL': 'CUSTOMER',
    'SUB': 'CUSTOMER',
    'L3': 'MANUFACTURE',
    'L4': 'MANUFACTURE',
    'ARDT': 'ARDT',
}


def migrate_forward(apps, schema_editor):
    DrillBit = apps.get_model('workorders', 'DrillBit')
    Account = apps.get_model('sales', 'Account')

    # Build account code lookup
    account_codes = {}
    for acct in Account.objects.all():
        account_codes[acct.pk] = acct.code

    bits = DrillBit.objects.all().select_related()
    updated = 0

    for bit in bits:
        old_status = bit.status
        old_lifecycle = bit.lifecycle_status or ''
        old_physical = bit.physical_status or ''
        account_code = account_codes.get(bit.account_id, '')

        # ── Derive new STATUS ──
        # Priority: old_lifecycle overrides old_status where they diverge
        new_status = _map_status(old_status, old_lifecycle, old_physical)

        # ── Derive new CONDITION ──
        new_condition = _map_condition(old_status, old_lifecycle, bit.run_count, bit.repair_count)

        # ── Derive OWNERSHIP from account ──
        new_ownership = ACCOUNT_OWNERSHIP.get(account_code, 'ARDT')

        bit.status = new_status
        bit.condition = new_condition
        bit.ownership = new_ownership
        bit.save(update_fields=['status', 'condition', 'ownership'])
        updated += 1

    print(f"  Migrated {updated} drill bits to new status/condition/ownership model")


def _map_status(old_status, old_lifecycle, old_physical):
    """Map old Status+Lifecycle to new Status."""

    # Terminal states first
    if old_status == 'SCRAPPED' or old_lifecycle == 'SCRAP':
        return 'SCRAPPED'
    if old_lifecycle == 'SAVED_BODY':
        return 'SAVED_BODY'
    if old_lifecycle == 'USA_REPAIR':
        return 'USA_REPAIR'

    # Process states from lifecycle
    if old_lifecycle == 'HOLD':
        return 'HOLD'
    if old_lifecycle == 'IN_REPAIR':
        return 'IN_REPAIR'
    if old_lifecycle == 'EVALUATION':
        return 'IN_EVALUATION'
    if old_lifecycle == 'BACKLOADED':
        return 'BACKLOADED'
    if old_lifecycle == 'DEPLOYED':
        # Deployed bits could be dispatched or in field
        if old_status == 'DISPATCHED':
            return 'DISPATCHED'
        if old_status == 'IN_FIELD':
            return 'IN_FIELD'
        return 'DISPATCHED'  # fallback

    # Map remaining old_status values
    status_map = {
        'UNREGISTERED': 'UNREGISTERED',
        'NEW': 'RECEIVING',        # NEW → receiving/inspection phase
        'IN_STOCK': 'IN_STOCK',
        'ASSIGNED': 'IN_STOCK',    # Assigned to WO but still in stock
        'IN_PRODUCTION': 'IN_PRODUCTION',
        'QC_PENDING': 'IN_PRODUCTION',  # QC is part of production
        'READY': 'IN_STOCK',       # Ready for dispatch = in stock
        'DISPATCHED': 'DISPATCHED',
        'IN_FIELD': 'IN_FIELD',
        'RETURNED': 'BACKLOADED',  # Returned = backloaded
    }
    return status_map.get(old_status, 'UNREGISTERED')


def _map_condition(old_status, old_lifecycle, run_count, repair_count):
    """Map old Status+Lifecycle to new Condition."""

    # Terminal
    if old_status == 'SCRAPPED' or old_lifecycle == 'SCRAP':
        return 'SCRAPPED'
    if old_lifecycle == 'SAVED_BODY':
        return 'SAVED_BODY'

    # Specific lifecycle conditions
    if old_lifecycle == 'REPAIRED':
        return 'REPAIRED'
    if old_lifecycle == 'RERUN':
        return 'RERUN'

    # Used bits: deployed with runs > 0
    if old_lifecycle in ('DEPLOYED', 'BACKLOADED') and run_count > 0:
        return 'USED'

    # New/fresh bits
    if old_lifecycle == 'NEW' and old_status in ('IN_STOCK', 'READY', 'NEW'):
        if repair_count == 0:
            return 'FINISHED_GOOD'
        return 'REPAIRED'

    # In production or evaluation — condition depends on repair history
    if old_lifecycle in ('IN_REPAIR', 'EVALUATION', 'USA_REPAIR'):
        if run_count > 0:
            return 'USED'
        return 'COMPONENTS'

    # HOLD — keep current condition logic
    if old_lifecycle == 'HOLD':
        if run_count > 0:
            return 'USED'
        if repair_count > 0:
            return 'REPAIRED'
        return 'COMPONENTS'

    # Unregistered / brand new
    if old_status == 'UNREGISTERED':
        return 'COMPONENTS'

    # Default: new bits in production
    if old_status in ('IN_PRODUCTION', 'QC_PENDING', 'ASSIGNED'):
        return 'COMPONENTS'

    # Fallback
    return 'COMPONENTS'


def migrate_backward(apps, schema_editor):
    """Reverse migration — best effort mapping back to old status/lifecycle."""
    DrillBit = apps.get_model('workorders', 'DrillBit')

    STATUS_REVERSE = {
        'ORDERED': ('NEW', 'NEW'),
        'IN_TRANSIT': ('NEW', 'NEW'),
        'UNREGISTERED': ('UNREGISTERED', 'NEW'),
        'RECEIVING': ('NEW', 'NEW'),
        'IN_COMPONENTS': ('NEW', 'NEW'),
        'IN_EVALUATION': ('RETURNED', 'EVALUATION'),
        'IN_PRODUCTION': ('IN_PRODUCTION', 'NEW'),
        'IN_REPAIR': ('IN_PRODUCTION', 'IN_REPAIR'),
        'IN_STOCK': ('IN_STOCK', 'NEW'),
        'DISPATCHED': ('DISPATCHED', 'DEPLOYED'),
        'IN_FIELD': ('IN_FIELD', 'DEPLOYED'),
        'BACKLOADED': ('RETURNED', 'BACKLOADED'),
        'HOLD': ('RETURNED', 'HOLD'),
        'USA_REPAIR': ('IN_PRODUCTION', 'USA_REPAIR'),
        'DE_BRAZED': ('SCRAPPED', 'SCRAP'),
        'SAVED_BODY': ('SCRAPPED', 'SAVED_BODY'),
        'SCRAPPED': ('SCRAPPED', 'SCRAP'),
    }

    for bit in DrillBit.objects.all():
        old_status, old_lifecycle = STATUS_REVERSE.get(bit.status, ('NEW', 'NEW'))
        bit.status = old_status
        bit.lifecycle_status = old_lifecycle
        bit.save(update_fields=['status', 'lifecycle_status'])


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0027_add_condition_ownership_is_trial_and_new_status_choices'),
        ('sales', '0008_alter_account_options_account_contract_number_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
