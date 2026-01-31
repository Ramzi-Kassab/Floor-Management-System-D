"""
Merge duplicate BitSize records.

Identifies BitSize records with the same size_decimal, keeps the one with the
lowest PK, and reassigns all FK/M2M references from duplicates to the keeper.
Then deletes the duplicate records.

Usage:
    python manage.py merge_duplicate_sizes              # Dry run
    python manage.py merge_duplicate_sizes --confirm    # Actually merge
"""
from django.core.management.base import BaseCommand
from django.db.models import Count


class Command(BaseCommand):
    help = "Merge duplicate BitSize records (same size_decimal) and reassign all references"

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually perform the merge (default is dry run)',
        )

    def handle(self, *args, **options):
        from apps.technology.models import (
            BitSize, HDBSType, SMIType, BitType, BreakerSlot, Design
        )
        from apps.workorders.models import DrillBit

        confirm = options['confirm']
        if not confirm:
            self.stdout.write(self.style.WARNING("DRY RUN — pass --confirm to actually merge\n"))

        # Find duplicate size_decimal values
        dupes = (
            BitSize.objects.values('size_decimal')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
            .order_by('size_decimal')
        )

        if not dupes:
            self.stdout.write(self.style.SUCCESS("No duplicate BitSize records found."))
            return

        total_merged = 0
        total_deleted = 0

        for dupe in dupes:
            dec = dupe['size_decimal']
            records = list(BitSize.objects.filter(size_decimal=dec).order_by('pk'))
            keeper = records[0]
            to_remove = records[1:]

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(
                f"  Size {dec} ({keeper.size_display}): "
                f"{len(records)} records — keeping PK={keeper.pk}, "
                f"removing PKs={[r.pk for r in to_remove]}"
            )

            for old in to_remove:
                # 1. Design.size FK (PROTECT)
                designs = Design.objects.filter(size=old)
                cnt = designs.count()
                if cnt:
                    self.stdout.write(f"    Design.size: {cnt} records → PK {keeper.pk}")
                    if confirm:
                        designs.update(size=keeper)

                # 2. SMIType.size FK (CASCADE)
                smis = SMIType.objects.filter(size=old)
                cnt = smis.count()
                if cnt:
                    self.stdout.write(f"    SMIType.size: {cnt} records → PK {keeper.pk}")
                    if confirm:
                        # Check for duplicate SMI (same smi_name + hdbs_type + new size)
                        for smi in smis:
                            existing = SMIType.objects.filter(
                                smi_name=smi.smi_name,
                                hdbs_type=smi.hdbs_type,
                                size=keeper,
                            ).first()
                            if existing:
                                self.stdout.write(
                                    f"      SMI '{smi.smi_name}' already exists for keeper size, "
                                    f"deleting duplicate PK={smi.pk}"
                                )
                                smi.delete()
                            else:
                                smi.size = keeper
                                smi.save(update_fields=['size'])

                # 3. BitType.size FK (PROTECT)
                bts = BitType.objects.filter(size=old)
                cnt = bts.count()
                if cnt:
                    self.stdout.write(f"    BitType.size: {cnt} records → PK {keeper.pk}")
                    if confirm:
                        bts.update(size=keeper)

                # 4. DrillBit.bit_size_ref FK (PROTECT)
                dbs = DrillBit.objects.filter(bit_size_ref=old)
                cnt = dbs.count()
                if cnt:
                    self.stdout.write(f"    DrillBit.bit_size_ref: {cnt} records → PK {keeper.pk}")
                    if confirm:
                        dbs.update(bit_size_ref=keeper)

                # 5. HDBSType.sizes M2M
                hdbs_with_old = HDBSType.objects.filter(sizes=old)
                cnt = hdbs_with_old.count()
                if cnt:
                    self.stdout.write(f"    HDBSType.sizes M2M: {cnt} records → add PK {keeper.pk}")
                    if confirm:
                        for h in hdbs_with_old:
                            h.sizes.add(keeper)
                            h.sizes.remove(old)

                # 6. BreakerSlot.compatible_sizes M2M
                bs_with_old = BreakerSlot.objects.filter(compatible_sizes=old)
                cnt = bs_with_old.count()
                if cnt:
                    self.stdout.write(f"    BreakerSlot.compatible_sizes M2M: {cnt} records → add PK {keeper.pk}")
                    if confirm:
                        for bs in bs_with_old:
                            bs.compatible_sizes.add(keeper)
                            bs.compatible_sizes.remove(old)

                # Delete the duplicate
                if confirm:
                    old_pk = old.pk
                    old.delete()
                    self.stdout.write(self.style.SUCCESS(f"    Deleted BitSize PK={old_pk}"))
                    total_deleted += 1

                total_merged += 1

        self.stdout.write(f"\n{'='*60}")
        if confirm:
            self.stdout.write(self.style.SUCCESS(
                f"Done. Merged {total_merged} duplicate(s), deleted {total_deleted} BitSize record(s)."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"Would merge {total_merged} duplicate(s). Run with --confirm to apply."
            ))

        # Post-merge: check for duplicate SMIType records (same name+hdbs+size)
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("Checking for duplicate SMIType records...")
        from django.db.models import Min
        smi_dupes = (
            SMIType.objects.values('smi_name', 'hdbs_type', 'size')
            .annotate(cnt=Count('id'), min_id=Min('id'))
            .filter(cnt__gt=1)
        )
        smi_deleted = 0
        for sd in smi_dupes:
            extras = SMIType.objects.filter(
                smi_name=sd['smi_name'],
                hdbs_type_id=sd['hdbs_type'],
                size_id=sd['size'],
            ).exclude(pk=sd['min_id'])
            self.stdout.write(
                f"  Duplicate SMI '{sd['smi_name']}' HDBS={sd['hdbs_type']} Size={sd['size']}: "
                f"keeping PK={sd['min_id']}, removing {extras.count()}"
            )
            if confirm:
                # Update any BOM.smi_type FKs pointing to duplicates
                from apps.technology.models import BOM
                for extra in extras:
                    BOM.objects.filter(smi_type=extra).update(smi_type_id=sd['min_id'])
                    extra.delete()
                    smi_deleted += 1

        if smi_dupes:
            if confirm:
                self.stdout.write(self.style.SUCCESS(f"  Deleted {smi_deleted} duplicate SMIType records."))
            else:
                self.stdout.write(self.style.WARNING(f"  Would delete {sum(d['cnt']-1 for d in smi_dupes)} duplicate SMIType records."))
        else:
            self.stdout.write(self.style.SUCCESS("  No duplicate SMIType records found."))
