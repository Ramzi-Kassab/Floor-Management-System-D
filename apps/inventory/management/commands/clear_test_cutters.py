"""
Clear test PDC Cutter data from the inventory.

This command removes:
- All InventoryItem records in the PDC Cutters (CT-PDC) category
- All associated ItemVariant records
- All associated ItemAttributeValue records
- All associated stock records

It does NOT remove:
- The PDC Cutters category itself
- Category attributes configuration
- Variant case definitions
- Other inventory categories/items

Usage:
    python manage.py clear_test_cutters           # Preview what will be deleted
    python manage.py clear_test_cutters --confirm # Actually delete the data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.inventory.models import (
    InventoryItem, InventoryCategory, ItemVariant,
    ItemAttributeValue, VariantStock, ItemStock
)


class Command(BaseCommand):
    help = "Clear test PDC Cutter data (items, variants, attributes, stock)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually delete the data (without this flag, just shows what would be deleted)',
        )
        parser.add_argument(
            '--keep-count',
            type=int,
            default=0,
            help='Keep this many cutter items (default: 0 = delete all)',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        keep_count = options['keep_count']

        self.stdout.write("=" * 60)
        self.stdout.write("Clear Test PDC Cutters")
        self.stdout.write("=" * 60)

        # Find PDC Cutters category
        pdc_category = InventoryCategory.objects.filter(code__in=['CT-PDC', 'CUT-PDC']).first()
        if not pdc_category:
            self.stdout.write(self.style.ERROR("PDC Cutters category not found (CT-PDC or CUT-PDC)"))
            return

        self.stdout.write(f"\nCategory: {pdc_category.code} - {pdc_category.name}")

        # Get all PDC cutter items
        cutter_items = InventoryItem.objects.filter(category=pdc_category).order_by('id')
        total_items = cutter_items.count()

        if total_items == 0:
            self.stdout.write(self.style.WARNING("\nNo PDC Cutter items found. Nothing to delete."))
            return

        # Determine which items to delete
        if keep_count > 0:
            items_to_delete = cutter_items[keep_count:]
            items_to_keep = cutter_items[:keep_count]
            self.stdout.write(f"\nKeeping first {keep_count} items, deleting the rest")
        else:
            items_to_delete = cutter_items
            items_to_keep = InventoryItem.objects.none()

        delete_count = items_to_delete.count()

        if delete_count == 0:
            self.stdout.write(self.style.WARNING(f"\nNo items to delete (keeping all {total_items} items)"))
            return

        # Get item IDs for related queries
        item_ids = list(items_to_delete.values_list('id', flat=True))

        # Count related records
        variant_count = ItemVariant.objects.filter(base_item_id__in=item_ids).count()
        attr_value_count = ItemAttributeValue.objects.filter(item_id__in=item_ids).count()
        item_stock_count = ItemStock.objects.filter(item_id__in=item_ids).count()

        # Get variant IDs for variant stock
        variant_ids = list(ItemVariant.objects.filter(base_item_id__in=item_ids).values_list('id', flat=True))
        variant_stock_count = VariantStock.objects.filter(variant_id__in=variant_ids).count()

        # Summary
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write("Records to be deleted:")
        self.stdout.write(f"  - PDC Cutter Items:     {delete_count}")
        self.stdout.write(f"  - Item Variants:        {variant_count}")
        self.stdout.write(f"  - Attribute Values:     {attr_value_count}")
        self.stdout.write(f"  - Item Stock Records:   {item_stock_count}")
        self.stdout.write(f"  - Variant Stock Records:{variant_stock_count}")
        self.stdout.write("-" * 40)

        # List items to delete
        if delete_count <= 20:
            self.stdout.write("\nItems to delete:")
            for item in items_to_delete:
                variant_count_for_item = item.variants.count()
                self.stdout.write(f"  - {item.code}: {item.name[:50]} ({variant_count_for_item} variants)")
        else:
            self.stdout.write(f"\n(Showing first 10 of {delete_count} items to delete)")
            for item in items_to_delete[:10]:
                variant_count_for_item = item.variants.count()
                self.stdout.write(f"  - {item.code}: {item.name[:50]} ({variant_count_for_item} variants)")
            self.stdout.write("  ...")

        if not confirm:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.WARNING("DRY RUN - No data was deleted"))
            self.stdout.write("Run with --confirm to actually delete the data:")
            self.stdout.write(f"  python manage.py clear_test_cutters --confirm")
            if keep_count == 0:
                self.stdout.write("\nOr keep some items:")
                self.stdout.write(f"  python manage.py clear_test_cutters --keep-count 5 --confirm")
            self.stdout.write("=" * 60)
            return

        # Actually delete
        self.stdout.write("\n" + self.style.WARNING("Deleting data..."))

        with transaction.atomic():
            # Delete in order of dependencies

            # 1. Delete variant stock
            deleted_vstock = VariantStock.objects.filter(variant_id__in=variant_ids).delete()[0]
            self.stdout.write(f"  Deleted {deleted_vstock} variant stock records")

            # 2. Delete item stock
            deleted_istock = ItemStock.objects.filter(item_id__in=item_ids).delete()[0]
            self.stdout.write(f"  Deleted {deleted_istock} item stock records")

            # 3. Delete variants (will cascade delete variant stock if any missed)
            deleted_variants = ItemVariant.objects.filter(base_item_id__in=item_ids).delete()[0]
            self.stdout.write(f"  Deleted {deleted_variants} variants")

            # 4. Delete attribute values
            deleted_attrs = ItemAttributeValue.objects.filter(item_id__in=item_ids).delete()[0]
            self.stdout.write(f"  Deleted {deleted_attrs} attribute values")

            # 5. Delete items
            deleted_items = items_to_delete.delete()[0]
            self.stdout.write(f"  Deleted {deleted_items} items")

        # Final status
        remaining = InventoryItem.objects.filter(category=pdc_category).count()
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Done!"))
        self.stdout.write(f"Remaining PDC Cutter items: {remaining}")
        self.stdout.write("=" * 60)
