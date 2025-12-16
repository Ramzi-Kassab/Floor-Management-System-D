"""
Migration to add client_code field to VariantCase.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_variantcase_itemvariant_with_client_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='variantcase',
            name='client_code',
            field=models.CharField(
                blank=True,
                help_text='Client code for CLIENT ownership cases (e.g., LSTK, Halliburton)',
                max_length=50,
            ),
        ),
    ]
