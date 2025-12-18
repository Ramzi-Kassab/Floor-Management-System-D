"""
ARDT FMS - Notifications App Forms
Version: 5.4
"""

from django import forms

from .models import Comment, Notification, NotificationTemplate, Task

TAILWIND_INPUT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
TAILWIND_SELECT = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA = "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"


class TaskForm(forms.ModelForm):
    """Form for creating/editing tasks."""

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "assigned_to",
            "due_date",
            "reminder_date",
            "priority",
            "entity_type",
            "entity_id",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Task title"}),
            "description": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Description (optional)"}),
            "assigned_to": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "due_date": forms.DateTimeInput(attrs={"class": TAILWIND_INPUT, "type": "datetime-local"}),
            "reminder_date": forms.DateTimeInput(attrs={"class": TAILWIND_INPUT, "type": "datetime-local"}),
            "priority": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "entity_type": forms.HiddenInput(),
            "entity_id": forms.HiddenInput(),
        }


class TaskStatusForm(forms.ModelForm):
    """Form for updating task status."""

    class Meta:
        model = Task
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }


class NotificationTemplateForm(forms.ModelForm):
    """Form for creating/editing notification templates."""

    class Meta:
        model = NotificationTemplate
        fields = [
            "code",
            "name",
            "channel",
            "subject",
            "body_template",
            "is_active",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "TEMPLATE_CODE"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Template Name"}),
            "channel": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "subject": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Notification subject"}),
            "body_template": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 6, "placeholder": "Use {{variable}} for placeholders"}),
            "is_active": forms.CheckboxInput(attrs={"class": "rounded border-gray-300 text-blue-600 focus:ring-blue-500"}),
        }


class CommentForm(forms.ModelForm):
    """Form for adding comments."""

    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Add a comment..."}),
        }
