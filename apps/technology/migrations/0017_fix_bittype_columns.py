# Generated manually to fix missing BitType columns in existing databases
# The migration 0014 was state-only and didn't create actual columns

from django.db import migrations


def add_missing_columns(apps, schema_editor):
    """Add missing columns to bit_types table if they don't exist."""
    from django.db import connection

    cursor = connection.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(bit_types)")
    existing_columns = {col[1] for col in cursor.fetchall()}

    # Columns that should exist based on the model
    required_columns = {
        'category': "ALTER TABLE bit_types ADD COLUMN category varchar(10) DEFAULT 'FC'",
        'smi_name': "ALTER TABLE bit_types ADD COLUMN smi_name varchar(50) DEFAULT ''",
        'hdbs_name': "ALTER TABLE bit_types ADD COLUMN hdbs_name varchar(50) DEFAULT ''",
        'hdbs_mn': "ALTER TABLE bit_types ADD COLUMN hdbs_mn varchar(20) DEFAULT ''",
        'ref_hdbs_mn': "ALTER TABLE bit_types ADD COLUMN ref_hdbs_mn varchar(20) DEFAULT ''",
        'ardt_item_number': "ALTER TABLE bit_types ADD COLUMN ardt_item_number varchar(20) DEFAULT ''",
        'body_material': "ALTER TABLE bit_types ADD COLUMN body_material varchar(1) DEFAULT ''",
        'no_of_blades': "ALTER TABLE bit_types ADD COLUMN no_of_blades integer NULL",
        'cutter_size': "ALTER TABLE bit_types ADD COLUMN cutter_size integer NULL",
        'gage_length': "ALTER TABLE bit_types ADD COLUMN gage_length decimal(4,1) NULL",
        'order_level': "ALTER TABLE bit_types ADD COLUMN order_level varchar(5) DEFAULT ''",
        'size_id': "ALTER TABLE bit_types ADD COLUMN size_id bigint NULL REFERENCES bit_sizes(id)",
    }

    # Add missing columns
    for column, sql in required_columns.items():
        if column not in existing_columns:
            print(f"  Adding missing column: {column}")
            cursor.execute(sql)


def reverse_noop(apps, schema_editor):
    """No reverse operation - columns will remain."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("technology", "0016_add_size_to_smitype"),
    ]

    operations = [
        migrations.RunPython(add_missing_columns, reverse_noop),
    ]
