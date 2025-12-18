"""
ARDT FMS - Planning Forms
Version: 5.4
"""

from django import forms

from .models import (
    PlanningBoard,
    PlanningColumn,
    PlanningItem,
    PlanningLabel,
    Sprint,
    WikiPage,
    WikiSpace,
)

# Tailwind CSS classes for consistent styling
TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_CHECKBOX = "w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"


class SprintForm(forms.ModelForm):
    """Form for Sprint CRUD."""

    class Meta:
        model = Sprint
        fields = [
            "code",
            "name",
            "goal",
            "start_date",
            "end_date",
            "status",
            "capacity_points",
            "owner",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "SPRINT-01"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "goal": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "start_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "capacity_points": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "owner": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data


class PlanningBoardForm(forms.ModelForm):
    """Form for Planning Board CRUD."""

    class Meta:
        model = PlanningBoard
        fields = [
            "code",
            "name",
            "description",
            "sprint",
            "icon",
            "color",
            "default_wip_limit",
            "is_active",
            "owner",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "sprint": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "icon": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., kanban"}),
            "color": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "#3b82f6"}),
            "default_wip_limit": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_active": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "owner": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class PlanningColumnForm(forms.ModelForm):
    """Form for Planning Column CRUD."""

    class Meta:
        model = PlanningColumn
        fields = [
            "board",
            "code",
            "name",
            "sequence",
            "wip_limit",
            "color",
            "is_done_column",
            "is_backlog_column",
        ]
        widgets = {
            "board": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "sequence": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "wip_limit": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "color": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "#3b82f6"}),
            "is_done_column": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "is_backlog_column": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }


class PlanningLabelForm(forms.ModelForm):
    """Form for Planning Label CRUD."""

    class Meta:
        model = PlanningLabel
        fields = ["name", "color", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "color": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "#6b7280"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 2}),
        }


class PlanningItemForm(forms.ModelForm):
    """Form for Planning Item CRUD."""

    class Meta:
        model = PlanningItem
        fields = [
            "code",
            "title",
            "description",
            "item_type",
            "priority",
            "board",
            "column",
            "sprint",
            "parent",
            "story_points",
            "estimated_hours",
            "due_date",
            "start_date",
            "assignee",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "ARDT-123"}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 4}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "priority": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "board": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "column": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "sprint": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "story_points": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "estimated_hours": forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.5"}),
            "due_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "start_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "assignee": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class PlanningItemQuickCreateForm(forms.ModelForm):
    """Quick form for creating planning items on board."""

    class Meta:
        model = PlanningItem
        fields = ["title", "item_type", "priority", "assignee"]
        widgets = {
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "What needs to be done?"}),
            "item_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "priority": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "assignee": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class WikiSpaceForm(forms.ModelForm):
    """Form for Wiki Space CRUD."""

    class Meta:
        model = WikiSpace
        fields = ["code", "name", "description", "icon", "is_public", "owner"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3}),
            "icon": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., book-open"}),
            "is_public": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
            "owner": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class WikiPageForm(forms.ModelForm):
    """Form for Wiki Page CRUD."""

    class Meta:
        model = WikiPage
        fields = [
            "space",
            "title",
            "slug",
            "icon",
            "content",
            "parent",
            "sequence",
            "is_published",
        ]
        widgets = {
            "space": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "slug": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "icon": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "e.g., file-text"}),
            "content": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 20, "id": "wiki-content"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "sequence": forms.NumberInput(attrs={"class": TAILWIND_INPUT}),
            "is_published": forms.CheckboxInput(attrs={"class": TAILWIND_CHECKBOX}),
        }
