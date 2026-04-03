# Generated manually — 2026-03-06
# Adds post-step verification fields to WorkflowStep

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("erp_automation", "0019_add_skip_group_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="workflowstep",
            name="verify_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "—"),
                    ("value_match", "Field Has Value"),
                    ("element_visible", "Element Visible"),
                    ("element_hidden", "Element Hidden"),
                    ("text_contains", "Text Contains"),
                    ("element_count", "Element Count ≥"),
                    ("url_contains", "URL Contains"),
                    ("element_enabled", "Element Enabled"),
                    ("no_error", "No D365 Error"),
                    ("attr_match", "Attribute Value"),
                ],
                default="",
                help_text="Verification to run after this step succeeds",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="workflowstep",
            name="verify_locator",
            field=models.ForeignKey(
                blank=True,
                help_text="Element to verify against (separate from action locator)",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verify_steps",
                to="erp_automation.locator",
            ),
        ),
        migrations.AddField(
            model_name="workflowstep",
            name="verify_value",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Expected value (supports {{templates}}). For attr_match use 'attr_name=expected'.",
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name="workflowstep",
            name="verify_timeout",
            field=models.IntegerField(
                default=3000,
                help_text="Verification timeout in milliseconds",
            ),
        ),
    ]
