from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workorders', '0032_receiving_inspection_attachments'),
    ]

    operations = [
        migrations.CreateModel(
            name='DrillBitPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('context_type', models.CharField(blank=True, choices=[('RECEIVING', 'Receiving Inspection'), ('EVALUATION', 'Cutter Evaluation'), ('WO', 'Work Order'), ('GENERAL', 'General')], default='GENERAL', max_length=20)),
                ('context_id', models.PositiveIntegerField(blank=True, help_text='PK of the related document (ReceivingInspection, etc.)', null=True)),
                ('category', models.CharField(choices=[('BLADE', 'Blade'), ('TOP', 'Top View'), ('SIDE', 'Side View'), ('DETAIL', 'Detail / Close-up'), ('EXTRA', 'Extra')], default='BLADE', max_length=10)),
                ('blade_number', models.PositiveSmallIntegerField(blank=True, help_text='Blade number (1-based) for BLADE category photos', null=True)),
                ('photo_number', models.PositiveSmallIntegerField(default=1, help_text='Sequence within the blade/category')),
                ('display_name', models.CharField(blank=True, help_text='Human label: B1-Ph1, Top, Side, Extra-1, etc.', max_length=50)),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('file', models.ImageField(upload_to='drill_bit_photos/%Y/%m/')),
                ('edited_file', models.ImageField(blank=True, null=True, upload_to='drill_bit_photos/edited/%Y/%m/')),
                ('capture_mode', models.CharField(choices=[('ADG', 'ADG Guided'), ('CAMERA', 'Camera'), ('FREE', 'Free Upload')], default='FREE', max_length=10)),
                ('sort_order', models.PositiveIntegerField(db_index=True, default=0)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('drill_bit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bit_photos', to='workorders.drillbit')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_bit_photos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Drill Bit Photo',
                'verbose_name_plural': 'Drill Bit Photos',
                'db_table': 'drill_bit_photos',
                'ordering': ['drill_bit', 'sort_order', 'uploaded_at'],
            },
        ),
    ]
