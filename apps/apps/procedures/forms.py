"""
ARDT FMS - Procedures Forms
Version: 5.4 - Sprint 3

Forms for Procedure and Step management.
"""

from django import forms

from .models import Procedure, ProcedureStep, StepCheckpoint

# Tailwind CSS classes
TAILWIND_INPUT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_SELECT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"


class ProcedureForm(forms.ModelForm):
    """Form for creating and editing procedures."""

    class Meta:
        model = Procedure
        fields = [
            "code",
            "name",
            "revision",
            "category",
            "applies_to",
            "scope",
            "purpose",
            "safety_notes",
            "responsible_role",
            "effective_date",
            "status",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., SA-PP-104"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Procedure name"}),
            "revision": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Rev A"}),
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "applies_to": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "scope": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Scope and applicability"}),
            "purpose": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Purpose and objectives"}),
            "safety_notes": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Safety precautions"}),
            "responsible_role": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "effective_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ["revision", "scope", "purpose", "safety_notes", "responsible_role", "effective_date"]
        for field in optional:
            self.fields[field].required = False


class ProcedureStepForm(forms.ModelForm):
    """Form for creating and editing procedure steps."""

    class Meta:
        model = ProcedureStep
        fields = [
            "step_number",
            "step_code",
            "name",
            "description",
            "step_type",
            "responsible_role",
            "estimated_duration_minutes",
            "is_mandatory",
            "can_skip",
            "requires_photo",
            "requires_signature",
        ]
        widgets = {
            "step_number": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 1, "placeholder": "10, 20, 30..."}),
            "step_code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Step code"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Step name"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "step_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "responsible_role": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "estimated_duration_minutes": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "is_mandatory": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600"}),
            "can_skip": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600"}),
            "requires_photo": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600"}),
            "requires_signature": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ["step_code", "description", "step_type", "responsible_role", "estimated_duration_minutes"]
        for field in optional:
            self.fields[field].required = False


class StepCheckpointForm(forms.ModelForm):
    """Form for creating step checkpoints."""

    class Meta:
        model = StepCheckpoint
        fields = [
            "sequence",
            "checkpoint_code",
            "name",
            "check_type",
            "expected_value",
            "tolerance_min",
            "tolerance_max",
            "unit",
            "is_critical",
            "failure_action",
            "photo_required",
            "help_text",
        ]
        widgets = {
            "sequence": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "checkpoint_code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Checkpoint name"}),
            "check_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "expected_value": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Expected value"}),
            "tolerance_min": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "tolerance_max": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.0001"}),
            "unit": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "mm, inch, PSI"}),
            "is_critical": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600"}),
            "failure_action": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "photo_required": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600"}),
            "help_text": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional = ["checkpoint_code", "check_type", "expected_value", "tolerance_min", "tolerance_max", "unit", "failure_notify_role", "help_text"]
        for field in optional:
            if field in self.fields:
                self.fields[field].required = False
