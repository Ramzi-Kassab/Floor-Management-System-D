"""
Auto-populate verify fields on active workflow steps.

Two strategies:
  1. fill/type_text steps -> verify_type=value_match (verify the field has the expected value)
  2. All other steps with a locator -> verify_type=element_visible using NEXT step's locator
     (proves the current step completed and the page is ready for the next action)

Usage:
  python manage.py populate_step_verification          # dry-run
  python manage.py populate_step_verification --confirm # apply changes
  python manage.py populate_step_verification --clear   # remove all verify configs
"""

from django.core.management.base import BaseCommand
from apps.erp_automation.models import (
    WorkflowStep, Workflow, WorkflowStatus,
    WorkflowChain, WorkflowChainLink,
)


class Command(BaseCommand):
    help = "Auto-populate verify fields on active workflow steps"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Apply changes (dry-run without)")
        parser.add_argument("--clear", action="store_true", help="Clear all verify configs")
        parser.add_argument("--workflow", type=int, help="Only process a specific workflow PK")

    def handle(self, *args, **options):
        confirm = options["confirm"]
        clear = options["clear"]
        wf_pk = options.get("workflow")

        if clear:
            return self._clear(confirm)

        workflows = Workflow.objects.filter(status=WorkflowStatus.ACTIVE)
        if wf_pk:
            workflows = workflows.filter(pk=wf_pk)

        total_value = 0
        total_visible = 0
        total_skipped = 0

        for wf in workflows.order_by("pk"):
            steps = list(
                wf.steps.filter(is_active=True)
                .order_by("order")
                .select_related("locator")
            )
            if not steps:
                continue

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"WF-{wf.pk} {wf.name} ({len(steps)} steps)")
            self.stdout.write(f"{'='*60}")

            for i, step in enumerate(steps):
                next_step = steps[i + 1] if i + 1 < len(steps) else None

                # Skip steps that already have verify configured
                if step.verify_type:
                    self.stdout.write(f"  #{step.order:3d} {step.name[:40]:40s} SKIP (already has {step.verify_type})")
                    total_skipped += 1
                    continue

                # Strategy 1: fill/type_text -> value_match
                if step.action_type in ("fill", "type_text") and step.locator:
                    verify_value = self._get_step_value_template(step)
                    if verify_value:
                        self.stdout.write(
                            f"  #{step.order:3d} {step.name[:40]:40s} -> value_match"
                            f"  verify_value={verify_value[:30]}"
                        )
                        if confirm:
                            step.verify_type = "value_match"
                            step.verify_value = verify_value
                            # verify_locator=None means use action locator
                            step.verify_locator = None
                            step.verify_timeout = 3000
                            step.save(update_fields=[
                                "verify_type", "verify_value",
                                "verify_locator", "verify_timeout",
                            ])
                        total_value += 1
                        continue

                # Strategy 2: any step -> element_visible on NEXT step's locator
                if next_step and next_step.locator:
                    # Skip if next step has no meaningful locator
                    # Skip for press_key/wait_time/navigate (no page transition to verify)
                    if step.action_type in ("press_key", "wait_time", "wait", "navigate",
                                            "goto_url", "screenshot"):
                        self.stdout.write(
                            f"  #{step.order:3d} {step.name[:40]:40s} SKIP ({step.action_type})"
                        )
                        total_skipped += 1
                        continue

                    # Skip if next step is in a repeat group (locator may not exist yet)
                    if next_step.repeat_group and not step.repeat_group:
                        self.stdout.write(
                            f"  #{step.order:3d} {step.name[:40]:40s} SKIP (next is repeat group start)"
                        )
                        total_skipped += 1
                        continue

                    self.stdout.write(
                        f"  #{step.order:3d} {step.name[:40]:40s} -> element_visible"
                        f"  next_locator={next_step.locator.name[:30]}"
                    )
                    if confirm:
                        step.verify_type = "element_visible"
                        step.verify_locator = next_step.locator
                        step.verify_value = ""
                        step.verify_timeout = 5000
                        step.save(update_fields=[
                            "verify_type", "verify_value",
                            "verify_locator", "verify_timeout",
                        ])
                    total_visible += 1
                    continue

                # No verification possible
                reason = "no next locator" if not next_step else "next has no locator"
                if not step.locator and step.action_type in ("fill", "type_text"):
                    reason = "no action locator"
                self.stdout.write(
                    f"  #{step.order:3d} {step.name[:40]:40s} SKIP ({reason})"
                )
                total_skipped += 1

        # ── Pass 2: Cross-workflow gaps (chain-aware) ──────────────
        # For the last step of each workflow in a chain, verify using
        # the first locator of the next workflow in the chain.
        total_cross = 0
        for chain in WorkflowChain.objects.filter(status="active").order_by("pk"):
            links = list(
                chain.links.filter(is_active=True)
                .select_related("workflow")
                .order_by("order")
            )
            if len(links) < 2:
                continue

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Chain {chain.pk}: {chain.name} (cross-workflow gaps)")
            self.stdout.write(f"{'='*60}")

            for i, link in enumerate(links[:-1]):
                next_link = links[i + 1]

                # Find last step of current workflow (that has no verify)
                last_step = (
                    link.workflow.steps
                    .filter(is_active=True, verify_type="")
                    .order_by("-order")
                    .select_related("locator")
                    .first()
                )
                if not last_step:
                    continue

                # Find first step with a locator in next workflow
                next_first = (
                    next_link.workflow.steps
                    .filter(is_active=True, locator__isnull=False)
                    .order_by("order")
                    .select_related("locator")
                    .first()
                )
                if not next_first or not next_first.locator:
                    self.stdout.write(
                        f"  Link {link.order:3d} WF-{link.workflow.pk} "
                        f"last=#{last_step.order} SKIP (next WF has no first locator)"
                    )
                    continue

                # Skip non-verifiable action types
                if last_step.action_type in ("navigate", "wait_time", "wait",
                                             "goto_url", "screenshot"):
                    self.stdout.write(
                        f"  Link {link.order:3d} WF-{link.workflow.pk} "
                        f"last=#{last_step.order} SKIP ({last_step.action_type})"
                    )
                    continue

                self.stdout.write(
                    f"  Link {link.order:3d} WF-{link.workflow.pk} "
                    f"last=#{last_step.order} \"{last_step.name[:25]}\" "
                    f"-> element_visible  "
                    f"next_wf_locator={next_first.locator.name[:30]}"
                )
                if confirm:
                    last_step.verify_type = "element_visible"
                    last_step.verify_locator = next_first.locator
                    last_step.verify_value = ""
                    last_step.verify_timeout = 8000  # longer for cross-workflow
                    last_step.save(update_fields=[
                        "verify_type", "verify_value",
                        "verify_locator", "verify_timeout",
                    ])
                total_cross += 1

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Summary:")
        self.stdout.write(f"  value_match (fill verified):    {total_value}")
        self.stdout.write(f"  element_visible (next locator): {total_visible}")
        self.stdout.write(f"  cross-workflow (chain gaps):    {total_cross}")
        self.stdout.write(f"  skipped:                        {total_skipped}")
        self.stdout.write(f"  total:                          {total_value + total_visible + total_cross + total_skipped}")
        if not confirm:
            self.stdout.write(f"\n  DRY RUN — re-run with --confirm to apply")
        else:
            self.stdout.write(f"\n  APPLIED — {total_value + total_visible + total_cross} steps updated")

    def _get_step_value_template(self, step):
        """Get the value expression for a fill step (template or static)."""
        if step.value_template:
            return step.value_template
        if step.value_static:
            return step.value_static
        if step.value_field:
            return "{{" + step.value_field + "}}"
        return ""

    def _clear(self, confirm):
        """Clear all verify configs."""
        qs = WorkflowStep.objects.exclude(verify_type="")
        count = qs.count()
        self.stdout.write(f"Found {count} steps with verify configs")
        if confirm:
            qs.update(verify_type="", verify_value="", verify_locator=None, verify_timeout=3000)
            self.stdout.write(f"Cleared {count} steps")
        else:
            self.stdout.write("DRY RUN — re-run with --confirm --clear to apply")
