"""
ARDT FMS - Work Orders Forms
Version: 5.4 - Sprint 1

Form definitions for work order and drill bit management.
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import DrillBit, WorkOrder


class WorkOrderForm(forms.ModelForm):
    """
    Form for creating and editing work orders.
    """

    class Meta:
        model = WorkOrder
        fields = [
            "wo_type",
            "drill_bit",
            "design",
            "customer",
            "sales_order",
            "rig",
            "well",
            "priority",
            "planned_start",
            "planned_end",
            "due_date",
            "assigned_to",
            "department",
            "procedure",
            "description",
            "notes",
        ]
        widgets = {
            "wo_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "drill_bit": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "design": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "customer": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "sales_order": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "rig": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "well": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "planned_start": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                }
            ),
            "planned_end": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                }
            ),
            "assigned_to": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "procedure": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                    "placeholder": "Enter work order description...",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                    "placeholder": "Additional notes...",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        planned_start = cleaned_data.get("planned_start")
        planned_end = cleaned_data.get("planned_end")
        due_date = cleaned_data.get("due_date")

        # Validate date logic
        if planned_start and planned_end:
            if planned_end < planned_start:
                raise ValidationError({"planned_end": "Planned end date cannot be before planned start date."})

        if planned_start and due_date:
            if due_date < planned_start:
                raise ValidationError({"due_date": "Due date cannot be before planned start date."})

        return cleaned_data


class WorkOrderStatusForm(forms.Form):
    """
    Form for updating work order status (used with HTMX).
    """

    status = forms.ChoiceField(
        choices=WorkOrder.Status.choices,
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                "hx-post": "",
                "hx-target": "#status-badge",
                "hx-swap": "outerHTML",
            }
        ),
    )


class DrillBitForm(forms.ModelForm):
    """
    Form for creating and editing drill bits.
    """

    class Meta:
        model = DrillBit
        fields = [
            "serial_number",
            "bit_type",
            "design",
            "size",
            "iadc_code",
            "status",
            "current_location",
            "customer",
            "rig",
            "well",
        ]
        widgets = {
            "serial_number": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono",
                    "placeholder": "e.g., FC-2024-0001",
                }
            ),
            "bit_type": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "design": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "size": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                    "step": "0.001",
                    "placeholder": "Size in inches",
                }
            ),
            "iadc_code": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono",
                    "placeholder": "e.g., M423",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "current_location": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "customer": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "rig": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "well": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
        }

    def clean_serial_number(self):
        serial_number = self.cleaned_data.get("serial_number")
        if serial_number:
            serial_number = serial_number.upper().strip()
            # Check uniqueness (excluding current instance for updates)
            qs = DrillBit.objects.filter(serial_number=serial_number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("A drill bit with this serial number already exists.")
        return serial_number


class DrillBitFilterForm(forms.Form):
    """
    Form for filtering drill bit list.
    """

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                "placeholder": "Search serial number...",
            }
        ),
    )
    bit_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + list(DrillBit.BitType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + list(DrillBit.Status.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )


class WorkOrderFilterForm(forms.Form):
    """
    Form for filtering work order list.
    """

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white",
                "placeholder": "Search WO number...",
            }
        ),
    )
    wo_type = forms.ChoiceField(
        required=False,
        choices=[("", "All Types")] + list(WorkOrder.WOType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All Statuses")] + list(WorkOrder.Status.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[("", "All Priorities")] + list(WorkOrder.Priority.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            }
        ),
    )
