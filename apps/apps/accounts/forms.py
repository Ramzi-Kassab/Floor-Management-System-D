"""
ARDT FMS - Account Forms
Version: 5.4 - Sprint 1
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User, UserPreference


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with remember me checkbox and Tailwind styling.
    """

    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={"class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Tailwind classes to username field
        self.fields["username"].widget.attrs.update(
            {
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5",
                "placeholder": "Employee ID or Email",
                "autofocus": True,
            }
        )

        # Add Tailwind classes to password field
        self.fields["password"].widget.attrs.update(
            {
                "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5",
                "placeholder": "••••••••",
            }
        )

        # Update field labels
        self.fields["username"].label = "Username or Email"
        self.fields["password"].label = "Password"


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "mobile"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                }
            ),
            "mobile": forms.TextInput(
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                }
            ),
        }


class UserPreferenceForm(forms.ModelForm):
    """Form for editing user preferences."""

    DATE_FORMAT_CHOICES = [
        ("DD/MM/YYYY", "DD/MM/YYYY (31/12/2024)"),
        ("MM/DD/YYYY", "MM/DD/YYYY (12/31/2024)"),
        ("YYYY-MM-DD", "YYYY-MM-DD (2024-12-31)"),
    ]

    TIME_FORMAT_CHOICES = [
        ("HH:mm", "24-hour (14:30)"),
        ("hh:mm A", "12-hour (02:30 PM)"),
    ]

    ITEMS_PER_PAGE_CHOICES = [
        (10, "10"),
        (25, "25"),
        (50, "50"),
        (100, "100"),
    ]

    date_format = forms.ChoiceField(choices=DATE_FORMAT_CHOICES)
    time_format = forms.ChoiceField(choices=TIME_FORMAT_CHOICES)
    items_per_page = forms.ChoiceField(choices=ITEMS_PER_PAGE_CHOICES)

    class Meta:
        model = UserPreference
        fields = [
            "default_dashboard",
            "email_notifications",
            "push_notifications",
            "notification_sound",
            "items_per_page",
            "date_format",
            "time_format",
            "sidebar_collapsed",
        ]
        widgets = {
            "default_dashboard": forms.Select(
                choices=[
                    ("main", "Main Dashboard"),
                    ("operations", "Operations"),
                    ("maintenance", "Maintenance"),
                    ("quality", "Quality"),
                    ("inventory", "Inventory"),
                ],
                attrs={
                    "class": "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                }
            ),
            "email_notifications": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"}
            ),
            "push_notifications": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"}
            ),
            "notification_sound": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"}
            ),
            "sidebar_collapsed": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style the select fields
        select_class = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        self.fields["date_format"].widget.attrs["class"] = select_class
        self.fields["time_format"].widget.attrs["class"] = select_class
        self.fields["items_per_page"].widget.attrs["class"] = select_class
