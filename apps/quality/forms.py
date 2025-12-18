"""
ARDT FMS - Quality Forms
Version: 5.4 - Sprint 3

Forms for Inspection and NCR management.
"""

from django import forms
from django.utils import timezone

from .models import NCR, Inspection, NCRPhoto

# Tailwind CSS classes
TAILWIND_INPUT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_SELECT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"


class InspectionForm(forms.ModelForm):
    """
    Form for creating and editing inspections.
    """

    class Meta:
        model = Inspection
        fields = [
            "inspection_type",
            "work_order",
            "drill_bit",
            "procedure",
            "scheduled_date",
            "status",
            "inspected_by",
            "findings",
            "notes",
        ]
        widgets = {
            "inspection_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "work_order": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "drill_bit": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "procedure": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "scheduled_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "inspected_by": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "findings": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 4, "placeholder": "Enter inspection findings..."}
            ),
            "notes": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Additional notes..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["drill_bit"].required = False
        self.fields["procedure"].required = False
        self.fields["scheduled_date"].required = False
        self.fields["inspected_by"].required = False
        self.fields["findings"].required = False
        self.fields["notes"].required = False


class InspectionResultForm(forms.ModelForm):
    """
    Form for recording inspection results.
    """

    class Meta:
        model = Inspection
        fields = ["status", "findings", "pass_count", "fail_count", "notes"]
        widgets = {
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "findings": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 4, "placeholder": "Enter inspection findings..."}
            ),
            "pass_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "fail_count": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "min": 0}),
            "notes": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Additional notes..."}
            ),
        }


class NCRForm(forms.ModelForm):
    """
    Form for creating and editing NCRs.
    """

    class Meta:
        model = NCR
        fields = [
            "title",
            "description",
            "severity",
            "work_order",
            "inspection",
            "drill_bit",
            "detection_stage",
            "root_cause",
            "disposition",
            "disposition_notes",
            "estimated_cost",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "Brief description of the non-conformance"}
            ),
            "description": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 4, "placeholder": "Detailed description of the issue..."}
            ),
            "severity": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "work_order": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "inspection": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "drill_bit": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "detection_stage": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., Final Inspection, Assembly"}
            ),
            "root_cause": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Root cause analysis..."}
            ),
            "disposition": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "disposition_notes": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Disposition details..."}
            ),
            "estimated_cost": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "Estimated cost (SAR)"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["work_order"].required = False
        self.fields["inspection"].required = False
        self.fields["drill_bit"].required = False
        self.fields["detection_stage"].required = False
        self.fields["root_cause"].required = False
        self.fields["disposition"].required = False
        self.fields["disposition_notes"].required = False
        self.fields["estimated_cost"].required = False


class NCRDispositionForm(forms.ModelForm):
    """
    Form for updating NCR disposition and closure.
    """

    class Meta:
        model = NCR
        fields = ["status", "disposition", "disposition_notes", "root_cause", "actual_cost", "closure_notes"]
        widgets = {
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "disposition": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "disposition_notes": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Disposition details..."}
            ),
            "root_cause": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Root cause analysis..."}
            ),
            "actual_cost": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01", "placeholder": "Actual cost (SAR)"}
            ),
            "closure_notes": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Closure notes..."}
            ),
        }


class NCRPhotoForm(forms.ModelForm):
    """
    Form for uploading NCR photos.
    """

    class Meta:
        model = NCRPhoto
        fields = ["photo", "caption"]
        widgets = {
            "photo": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-blue-900 dark:file:text-blue-200",
                    "accept": "image/*",
                }
            ),
            "caption": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "Photo description..."}
            ),
        }
