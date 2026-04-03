"""
DEPRECATED — Use seed_workflow_capabilities instead.
This command used the old WorkflowRole enum which has been removed.
Kept for reference only.
"""
from django.core.management.base import BaseCommand
from apps.notifications.models import WorkflowRule, WorkflowEvent, ActionType


DEFAULT_RULES = [
    # ── Receiving ──
    {
        'name': 'Bit received — schedule inspection',
        'trigger_event': WorkflowEvent.BIT_RECEIVED,
        'rule_type': 'BOTH',
        'action_type': ActionType.INSPECT_BIT,
        'assign_to_role': WorkflowRole.RECEIVING_INSPECTOR,
        'is_queue_action': True,
        'notif_title_template': 'New bit received: {serial}',
        'notif_message_template': 'S/N {serial} backloaded. Receiving inspection required.',
        'notif_recipients_role': WorkflowRole.RECEIVING_INSPECTOR,
        'notif_priority': 'HIGH',
        'deadline_hours': 8,
        'action_url_pattern': '/work-orders/drill-bits/enhanced/{bit_id}/',
        'action_description_template': 'Start receiving inspection for S/N {serial}',
    },
    {
        'name': 'Inspection accepted — add to planner',
        'trigger_event': WorkflowEvent.INSPECTION_ACCEPTED,
        'rule_type': 'BOTH',
        'action_type': ActionType.ADD_TO_PLAN,
        'assign_to_role': WorkflowRole.PLANNER,
        'notif_title_template': 'Inspection passed: {serial} ready for planning',
        'notif_message_template': 'S/N {serial} accepted. Add to production planner.',
        'notif_recipients_role': WorkflowRole.PLANNER,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/drill-bits/enhanced/{bit_id}/',
        'action_description_template': 'Add S/N {serial} to production planner',
    },
    {
        'name': 'Inspection rejected — technical decision',
        'trigger_event': WorkflowEvent.INSPECTION_REJECTED,
        'rule_type': 'BOTH',
        'action_type': ActionType.MAKE_DECISION,
        'assign_to_role': WorkflowRole.TECHNICAL_LEAD,
        'notif_title_template': 'Inspection REJECTED: {serial}',
        'notif_message_template': 'S/N {serial} rejected during receiving inspection. Decision needed: repair, scrap, or return.',
        'notif_recipients_role': WorkflowRole.TECHNICAL_LEAD,
        'notif_priority': 'URGENT',
        'action_url_pattern': '/work-orders/drill-bits/enhanced/{bit_id}/',
        'action_description_template': 'Review rejection of S/N {serial} and decide next action',
    },
    {
        'name': 'Cerebro device detected — remove before processing',
        'trigger_event': WorkflowEvent.CEREBRO_DETECTED,
        'rule_type': 'BOTH',
        'action_type': ActionType.REMOVE_DEVICE,
        'assign_to_role': WorkflowRole.TECHNICAL_LEAD,
        'notif_title_template': 'Cerebro device on {serial} — must remove',
        'notif_message_template': 'S/N {serial} has Cerebro installed. Technical team must remove before processing.',
        'notif_recipients_role': WorkflowRole.TECHNICAL_LEAD,
        'notif_priority': 'URGENT',
        'action_url_pattern': '/work-orders/drill-bits/enhanced/{bit_id}/',
    },
    # ── Planning & Release ──
    {
        'name': 'WO released — operator transfer',
        'trigger_event': WorkflowEvent.WO_RELEASED,
        'rule_type': 'BOTH',
        'action_type': ActionType.TRANSFER_BIT,
        'assign_to_role': WorkflowRole.OPERATOR,
        'is_queue_action': True,
        'notif_title_template': 'Transfer bit {serial} for WO {wo_number}',
        'notif_message_template': 'WO {wo_number} released for S/N {serial}. Transfer bit to production area.',
        'notif_recipients_role': WorkflowRole.OPERATOR,
        'notif_priority': 'HIGH',
        'deadline_hours': 4,
        'escalate_after_hours': 4,
        'escalate_to_role': WorkflowRole.PRODUCTION_LEAD,
        'action_url_pattern': '/work-orders/location-transfers/?serial={serial}',
        'action_description_template': 'Transfer S/N {serial} to production area',
        'order': 1,
    },
    {
        'name': 'WO released — manager approval',
        'trigger_event': WorkflowEvent.WO_RELEASED,
        'rule_type': 'BOTH',
        'action_type': ActionType.APPROVE_WO,
        'assign_to_role': WorkflowRole.PRODUCTION_MANAGER,
        'notif_title_template': 'WO {wo_number} needs your approval',
        'notif_message_template': 'WO {wo_number} for S/N {serial} released. Review and approve to start production.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_MANAGER,
        'notif_priority': 'HIGH',
        'deadline_hours': 8,
        'escalate_after_hours': 8,
        'escalate_to_role': WorkflowRole.MANAGEMENT,
        'action_url_pattern': '/work-orders/enhanced/{wo_id}/',
        'action_description_template': 'Review and approve WO {wo_number}',
        'order': 2,
    },
    {
        'name': 'Transfer confirmed — notify planner',
        'trigger_event': WorkflowEvent.TRANSFER_CONFIRMED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': 'Transfer confirmed: {serial}',
        'notif_message_template': 'S/N {serial} transferred. {actor_name} confirmed the move.',
        'notif_recipients_role': WorkflowRole.PLANNER,
        'notif_priority': 'NORMAL',
    },
    # ── Approval ──
    {
        'name': 'WO approved — start production',
        'trigger_event': WorkflowEvent.WO_APPROVED,
        'rule_type': 'BOTH',
        'action_type': ActionType.START_STEP,
        'assign_to_role': WorkflowRole.OPERATOR,
        'is_queue_action': True,
        'notif_title_template': 'WO {wo_number} approved — production can start',
        'notif_message_template': 'WO {wo_number} for S/N {serial} approved by {actor_name}. Start first router step.',
        'notif_recipients_role': WorkflowRole.OPERATOR,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/{wo_id}/router-sheet/',
        'action_description_template': 'Start production on WO {wo_number}',
    },
    {
        'name': 'WO deleted — return to planner',
        'trigger_event': WorkflowEvent.WO_DELETED,
        'rule_type': 'BOTH',
        'action_type': ActionType.REPLAN,
        'assign_to_role': WorkflowRole.PLANNER,
        'notif_title_template': 'WO {wo_number} deleted — re-plan {serial}',
        'notif_message_template': 'WO {wo_number} for S/N {serial} has been deleted by {actor_name}. Bit returned to planner.',
        'notif_recipients_role': WorkflowRole.PLANNER,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/production-planner/',
        'action_description_template': 'Re-plan S/N {serial} in production planner',
    },
    # ── Production ──
    {
        'name': 'Step on hold — supervisor review',
        'trigger_event': WorkflowEvent.STEP_ON_HOLD,
        'rule_type': 'BOTH',
        'action_type': ActionType.REVIEW_HOLD,
        'assign_to_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_title_template': 'Step on hold: {step_name} — WO {wo_number}',
        'notif_message_template': '{actor_name} put "{step_name}" on hold ({hold_reason}). S/N {serial}.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/{wo_id}/router/{step_number}/',
        'action_description_template': 'Review hold on "{step_name}" and decide next action',
    },
    {
        'name': 'Step waiting QC — inspector review',
        'trigger_event': WorkflowEvent.STEP_WAITING_QC,
        'rule_type': 'BOTH',
        'action_type': ActionType.QC_CHECK,
        'assign_to_role': WorkflowRole.QC_INSPECTOR,
        'is_queue_action': True,
        'notif_title_template': 'QC needed: {step_name} — WO {wo_number}',
        'notif_message_template': '{step_name} on WO {wo_number} (S/N {serial}) waiting for QC review.',
        'notif_recipients_role': WorkflowRole.QC_INSPECTOR,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/{wo_id}/router/{step_number}/',
    },
    {
        'name': 'Step waiting approval — manager review',
        'trigger_event': WorkflowEvent.STEP_WAITING_APPROVAL,
        'rule_type': 'BOTH',
        'action_type': ActionType.APPROVE_WO,
        'assign_to_role': WorkflowRole.PRODUCTION_MANAGER,
        'notif_title_template': 'Approval needed: {step_name} — WO {wo_number}',
        'notif_message_template': '{step_name} on WO {wo_number} (S/N {serial}) waiting for approval.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_MANAGER,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/{wo_id}/router/{step_number}/',
    },
    {
        'name': 'Step waiting tech — technical review',
        'trigger_event': WorkflowEvent.STEP_WAITING_TECH,
        'rule_type': 'BOTH',
        'action_type': ActionType.TECH_REVIEW,
        'assign_to_role': WorkflowRole.TECHNICAL_LEAD,
        'notif_title_template': 'Tech review needed: {step_name} — WO {wo_number}',
        'notif_message_template': '{step_name} on WO {wo_number} (S/N {serial}) waiting for technical review.',
        'notif_recipients_role': WorkflowRole.TECHNICAL_LEAD,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/{wo_id}/router/{step_number}/',
    },
    {
        'name': 'Step resumed — notify operator',
        'trigger_event': WorkflowEvent.STEP_RESUMED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': 'Step resumed: {step_name} — WO {wo_number}',
        'notif_message_template': '{actor_name} resumed "{step_name}" on WO {wo_number}.',
        'notif_recipients_role': WorkflowRole.OPERATOR,
        'notif_priority': 'NORMAL',
    },
    {
        'name': 'All steps done — confirm transfer',
        'trigger_event': WorkflowEvent.ALL_STEPS_DONE,
        'rule_type': 'BOTH',
        'action_type': ActionType.CONFIRM_TRANSFER,
        'assign_to_role': WorkflowRole.OPERATOR,
        'is_queue_action': True,
        'notif_title_template': 'All steps done — WO {wo_number}',
        'notif_message_template': 'All router steps completed for S/N {serial}. Transfer bit to QC/FG area.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/location-transfers/?serial={serial}',
        'action_description_template': 'Transfer S/N {serial} to finished goods',
    },
    {
        'name': 'Die check — quality decision needed',
        'trigger_event': WorkflowEvent.DIE_CHECK_DECISION,
        'rule_type': 'BOTH',
        'action_type': ActionType.QUALITY_DECISION,
        'assign_to_role': WorkflowRole.QC_INSPECTOR,
        'notif_title_template': 'Quality decision needed — WO {wo_number}',
        'notif_message_template': 'Die check on WO {wo_number} (S/N {serial}) has cutters waiting for quality decision.',
        'notif_recipients_role': WorkflowRole.QC_INSPECTOR,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/enhanced/{wo_id}/',
    },
    # ── QC & Completion ──
    {
        'name': 'WO sent to QC',
        'trigger_event': WorkflowEvent.WO_SENT_TO_QC,
        'rule_type': 'BOTH',
        'action_type': ActionType.QC_CHECK,
        'assign_to_role': WorkflowRole.QC_INSPECTOR,
        'is_queue_action': True,
        'notif_title_template': 'WO {wo_number} sent to QC',
        'notif_message_template': 'WO {wo_number} for S/N {serial} sent to QC by {actor_name}.',
        'notif_recipients_role': WorkflowRole.QC_INSPECTOR,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/enhanced/{wo_id}/',
    },
    {
        'name': 'QC passed — prepare dispatch',
        'trigger_event': WorkflowEvent.QC_PASSED,
        'rule_type': 'BOTH',
        'action_type': ActionType.PREPARE_DISPATCH,
        'assign_to_role': WorkflowRole.DISPATCH,
        'notif_title_template': 'QC passed — {serial} ready for dispatch',
        'notif_message_template': 'WO {wo_number} for S/N {serial} passed QC. Prepare for shipping.',
        'notif_recipients_role': WorkflowRole.DISPATCH,
        'notif_priority': 'HIGH',
        'action_url_pattern': '/work-orders/enhanced/{wo_id}/',
    },
    {
        'name': 'QC failed — rework needed',
        'trigger_event': WorkflowEvent.QC_FAILED,
        'rule_type': 'BOTH',
        'action_type': ActionType.REWORK,
        'assign_to_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_title_template': 'QC FAILED — rework needed for {serial}',
        'notif_message_template': 'WO {wo_number} for S/N {serial} failed QC. Rework required.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_priority': 'URGENT',
        'action_url_pattern': '/work-orders/enhanced/{wo_id}/',
    },
    {
        'name': 'WO completed — info',
        'trigger_event': WorkflowEvent.WO_COMPLETED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': 'WO {wo_number} completed',
        'notif_message_template': 'WO {wo_number} for S/N {serial} has been completed.',
        'notif_recipients_role': WorkflowRole.MANAGEMENT,
        'notif_priority': 'HIGH',
    },
    # ── Evaluations & Inventory ──
    {
        'name': 'Evaluation completed — info',
        'trigger_event': WorkflowEvent.EVALUATION_COMPLETED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': '{eval_type} evaluation completed — WO {wo_number}',
        'notif_message_template': '{eval_type} evaluation completed for S/N {serial} on WO {wo_number}.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_MANAGER,
        'notif_priority': 'HIGH',
    },
    {
        'name': 'Route auto-updated — info',
        'trigger_event': WorkflowEvent.ROUTE_UPDATED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': 'Route updated for WO {wo_number}',
        'notif_message_template': 'Router route auto-updated after evaluation. {steps_added} steps added.',
        'notif_recipients_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_priority': 'NORMAL',
    },
    {
        'name': 'GRN posted — info',
        'trigger_event': WorkflowEvent.GRN_POSTED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': 'GRN {grn_number} posted',
        'notif_message_template': 'GRN {grn_number} posted with {line_count} lines by {actor_name}.',
        'notif_recipients_role': WorkflowRole.MANAGEMENT,
        'notif_priority': 'URGENT',
    },
    {
        'name': 'WO started — info',
        'trigger_event': WorkflowEvent.WO_STARTED,
        'rule_type': 'NOTIFICATION',
        'notif_title_template': 'Work started on WO {wo_number}',
        'notif_message_template': '{actor_name} started work on WO {wo_number} (S/N {serial}).',
        'notif_recipients_role': WorkflowRole.PRODUCTION_LEAD,
        'notif_priority': 'NORMAL',
    },
]


class Command(BaseCommand):
    help = 'Seed default WorkflowRule records (replicates current notify() behavior)'

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Actually create records')

    def handle(self, *args, **options):
        confirm = options.get('confirm', False)

        created = 0
        skipped = 0

        for rule_data in DEFAULT_RULES:
            name = rule_data['name']
            event = rule_data['trigger_event']

            exists = WorkflowRule.objects.filter(
                trigger_event=event, name=name
            ).exists()

            if exists:
                skipped += 1
                self.stdout.write(f'  SKIP (exists): [{event}] {name}')
                continue

            if not confirm:
                self.stdout.write(f'  WOULD CREATE: [{event}] {name}')
                created += 1
                continue

            # Build kwargs, handling FK fields
            kwargs = {}
            for k, v in rule_data.items():
                if k in ('assign_to_user', 'escalate_to_user'):
                    continue  # Skip FK fields for now
                kwargs[k] = v

            WorkflowRule.objects.create(**kwargs)
            created += 1
            self.stdout.write(self.style.SUCCESS(f'  CREATED: [{event}] {name}'))

        if confirm:
            self.stdout.write(self.style.SUCCESS(f'\nDone: {created} created, {skipped} skipped'))
        else:
            self.stdout.write(f'\nDry run: {created} would be created, {skipped} already exist')
            self.stdout.write('Run with --confirm to create records')
