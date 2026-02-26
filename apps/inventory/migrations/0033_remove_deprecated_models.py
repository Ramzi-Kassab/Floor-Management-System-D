"""
Remove deprecated models: InventoryStock, InventoryTransaction, BillOfMaterial, BOMLine.

These models have been replaced by:
- InventoryStock → StockBalance (multi-dimensional) + VariantStock (variant-level)
- InventoryTransaction → StockLedger (immutable ledger with qty_delta)
- BillOfMaterial/BOMLine → technology.BOM/BOMLine (active BOM system)
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0032_add_shape_image_base64'),
    ]

    operations = [
        # Remove BOMLine first (FK to BillOfMaterial)
        migrations.DeleteModel(
            name='BOMLine',
        ),
        migrations.DeleteModel(
            name='BillOfMaterial',
        ),
        migrations.DeleteModel(
            name='InventoryTransaction',
        ),
        migrations.DeleteModel(
            name='InventoryStock',
        ),
    ]
