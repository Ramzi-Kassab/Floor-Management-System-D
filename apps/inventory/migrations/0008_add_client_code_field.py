"""
Migration to add client_code field to VariantCase.
Safe migration - checks if column exists before adding.
"""
from django.db import migrations, models, connection


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_client_code_if_missing(apps, schema_editor):
    """Add client_code column only if it doesn't exist."""
    if not column_exists('variant_cases', 'client_code'):
        cursor = connection.cursor()
        cursor.execute("ALTER TABLE variant_cases ADD COLUMN client_code varchar(50) DEFAULT '';")


def reverse_migration(apps, schema_editor):
    """No-op for reverse - don't drop the column."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_variantcase_itemvariant_with_client_code'),
    ]

    operations = [
        migrations.RunPython(add_client_code_if_missing, reverse_migration),
    ]
