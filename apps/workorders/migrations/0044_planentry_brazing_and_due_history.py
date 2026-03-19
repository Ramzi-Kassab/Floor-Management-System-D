"""Add planned_brazing_date and due_date_history to ProductionPlanEntry."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorders', '0043_add_rejected_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='productionplanentry',
            name='planned_brazing_date',
            field=models.DateField(blank=True, null=True, help_text='Estimated brazing date'),
        ),
        migrations.AddField(
            model_name='productionplanentry',
            name='due_date_history',
            field=models.JSONField(blank=True, default=list, help_text='History of due date changes'),
        ),
    ]
