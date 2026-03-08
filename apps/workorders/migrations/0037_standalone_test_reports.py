"""
Add standalone test report models: DieCheckReport, StandaloneLPTReport, StandaloneThreadReport.
These are linked to WO or DrillBit and auto-fill evaluation checklist items.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("workorders", "0036_add_evaluation_sections_lpt_thread_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="DieCheckReport",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_number", models.CharField(blank=True, max_length=30)),
                ("grid_data", models.JSONField(blank=True, help_text="Die check grid: blade \u2192 position \u2192 result", null=True)),
                ("result", models.CharField(blank=True, choices=[("PASS", "Pass"), ("FAIL", "Fail"), ("PARTIAL", "Partial")], max_length=10)),
                ("remarks", models.TextField(blank=True)),
                ("performed_at", models.DateTimeField(blank=True, null=True)),
                ("is_complete", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("drill_bit", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="die_check_reports", to="workorders.drillbit")),
                ("evaluation", models.ForeignKey(blank=True, help_text="Linked evaluation (auto-fills checklist item when completed)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="die_check_reports", to="workorders.cutterevaluationmatrix")),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="die_checks_performed", to=settings.AUTH_USER_MODEL)),
                ("work_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="die_check_reports", to="workorders.workorder")),
            ],
            options={
                "db_table": "die_check_reports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="StandaloneLPTReport",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_number", models.CharField(blank=True, max_length=30)),
                ("test_data", models.JSONField(blank=True, help_text="LPT test parameters and results per QAS/1004-1", null=True)),
                ("result", models.CharField(blank=True, choices=[("PASS", "Pass"), ("FAIL", "Fail"), ("INCONCLUSIVE", "Inconclusive")], max_length=15)),
                ("remarks", models.TextField(blank=True)),
                ("performed_at", models.DateTimeField(blank=True, null=True)),
                ("is_complete", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("drill_bit", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="standalone_lpt_reports", to="workorders.drillbit")),
                ("evaluation", models.ForeignKey(blank=True, help_text="Linked evaluation (auto-fills checklist item when completed)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="standalone_lpt_reports", to="workorders.cutterevaluationmatrix")),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="standalone_lpt_tests_performed", to=settings.AUTH_USER_MODEL)),
                ("work_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="standalone_lpt_reports", to="workorders.workorder")),
            ],
            options={
                "db_table": "standalone_lpt_reports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="StandaloneThreadReport",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_number", models.CharField(blank=True, max_length=30)),
                ("inspection_data", models.JSONField(blank=True, help_text="API Thread checkpoints and measurements", null=True)),
                ("result", models.CharField(blank=True, choices=[("PASS", "Pass"), ("FAIL", "Fail")], max_length=10)),
                ("remarks", models.TextField(blank=True)),
                ("performed_at", models.DateTimeField(blank=True, null=True)),
                ("is_complete", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("drill_bit", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="standalone_thread_reports", to="workorders.drillbit")),
                ("evaluation", models.ForeignKey(blank=True, help_text="Linked evaluation (auto-fills checklist item when completed)", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="standalone_thread_reports", to="workorders.cutterevaluationmatrix")),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="standalone_thread_inspections_performed", to=settings.AUTH_USER_MODEL)),
                ("work_order", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="standalone_thread_reports", to="workorders.workorder")),
            ],
            options={
                "db_table": "standalone_thread_reports",
                "ordering": ["-created_at"],
            },
        ),
    ]
