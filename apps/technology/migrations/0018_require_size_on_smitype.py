# Generated manually - make size required on SMIType

from django.db import migrations, models
import django.db.models.deletion


def delete_smi_with_null_size(apps, schema_editor):
    """Delete any SMIType records with null size before making field required."""
    SMIType = apps.get_model('technology', 'SMIType')
    null_count = SMIType.objects.filter(size__isnull=True).count()
    if null_count > 0:
        print(f"  Deleting {null_count} SMIType records with null size...")
        SMIType.objects.filter(size__isnull=True).delete()


def reverse_noop(apps, schema_editor):
    """No reverse operation needed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('technology', '0017_fix_bittype_columns'),
    ]

    operations = [
        # First, delete any SMIType records with null size
        migrations.RunPython(delete_smi_with_null_size, reverse_noop),

        # Then make size field required (non-nullable)
        migrations.AlterField(
            model_name='smitype',
            name='size',
            field=models.ForeignKey(
                help_text='Specific size for this SMI name (required)',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='smi_types',
                to='technology.bitsize',
                verbose_name='Size',
            ),
        ),
    ]
