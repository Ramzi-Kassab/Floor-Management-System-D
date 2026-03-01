from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workorders', '0031_add_pocket_eval_qas005_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='receivinginspection',
            name='date_of_receipt',
            field=models.DateField(blank=True, null=True, verbose_name='Date of Receipt'),
        ),
        migrations.CreateModel(
            name='ReceivingInspectionAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='receiving_inspections/%Y/%m/')),
                ('name', models.CharField(default='Q-Note', help_text='Document name (e.g., Q-Note, Photo, Additional)', max_length=100)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('inspection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='workorders.receivinginspection')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'receiving_inspection_attachments',
                'ordering': ['uploaded_at'],
            },
        ),
    ]
