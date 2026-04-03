"""Drop WorkflowCapability/UserCapability, add Role FKs to WorkflowRule/WorkflowAction."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_add_workflow_fields_to_role_userrole"),
        ("notifications", "0005_iam_redesign_capabilities"),
    ]

    operations = [
        # Step 1: Drop tables via SQL (cleanest for SQLite — avoids index rebuild issues)
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS user_capabilities_account_scope;",
                "DROP TABLE IF EXISTS user_capabilities;",
                "DROP TABLE IF EXISTS workflow_capabilities_positions;",
                "DROP TABLE IF EXISTS workflow_capabilities;",
            ],
            reverse_sql=[],  # No reverse — tables were empty
        ),

        # Step 2: Remove FK fields that pointed to dropped tables
        migrations.RemoveIndex(
            model_name="workflowaction",
            name="idx_wa_cap_status",
        ),
        migrations.RemoveField(model_name="workflowaction", name="assigned_capability"),
        migrations.RemoveField(model_name="workflowrule", name="assign_to_capability"),
        migrations.RemoveField(model_name="workflowrule", name="escalate_to_capability"),
        migrations.RemoveField(model_name="workflowrule", name="notif_recipients_capability"),

        # Step 3: Add new FK fields pointing to accounts.Role
        migrations.AddField(
            model_name="workflowaction",
            name="assigned_role",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="workflow_actions",
                to="accounts.role",
            ),
        ),
        migrations.AddField(
            model_name="workflowrule",
            name="assign_to_role",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="workflow_rules_assigned",
                to="accounts.role",
                help_text="Role that determines who receives this action",
            ),
        ),
        migrations.AddField(
            model_name="workflowrule",
            name="escalate_to_role",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="workflow_rules_escalation",
                to="accounts.role",
            ),
        ),
        migrations.AddField(
            model_name="workflowrule",
            name="notif_recipients_role",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="workflow_rules_notification",
                to="accounts.role",
                help_text="Role that determines who receives this notification",
            ),
        ),

        # Step 4: Add index on new FK
        migrations.AddIndex(
            model_name="workflowaction",
            index=models.Index(
                fields=["assigned_role", "status", "is_blocked"],
                name="idx_wa_role_status",
            ),
        ),

        # Step 5: Remove model definitions from Django state (tables already dropped by RunSQL)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="UserCapability"),
                migrations.DeleteModel(name="WorkflowCapability"),
            ],
            database_operations=[],  # Tables already dropped by RunSQL above
        ),
    ]
