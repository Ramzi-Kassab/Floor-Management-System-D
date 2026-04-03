"""
ARDT FMS - Documents Forms
Version: 5.4 - Sprint 2

Forms for document management.
"""

from django import forms

from .models import Document, DocumentCategory

# Tailwind CSS classes
TAILWIND_INPUT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_SELECT = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_TEXTAREA = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white"
TAILWIND_FILE = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ardt-blue focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-ardt-blue file:text-white hover:file:bg-blue-700"


class DocumentCategoryForm(forms.ModelForm):
    """Form for document categories."""

    class Meta:
        model = DocumentCategory
        fields = ["code", "name", "parent", "description", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category code (e.g., PROC, SPEC)"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Category name"}),
            "parent": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "description": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Category description"}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 text-ardt-blue border-gray-300 rounded focus:ring-ardt-blue"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude self from parent choices (prevent circular reference)
        if self.instance.pk:
            self.fields["parent"].queryset = DocumentCategory.objects.exclude(pk=self.instance.pk).filter(is_active=True)
        else:
            self.fields["parent"].queryset = DocumentCategory.objects.filter(is_active=True)

    def clean_code(self):
        """Ensure code is uppercase."""
        code = self.cleaned_data.get("code")
        if code:
            return code.upper()
        return code


class DocumentForm(forms.ModelForm):
    """Form for document upload and editing."""

    class Meta:
        model = Document
        fields = [
            "code",
            "name",
            "category",
            "file",
            "version",
            "revision_date",
            "status",
            "description",
            "keywords",
            "is_confidential",
            "expires_at",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Document code (e.g., DOC-001)"}),
            "name": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Document title"}),
            "category": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "file": forms.FileInput(
                attrs={
                    "class": TAILWIND_FILE,
                    "accept": ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.jpg,.jpeg,.png,.gif",
                }
            ),
            "version": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "1.0"}),
            "revision_date": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
            "status": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "description": forms.Textarea(
                attrs={"class": TAILWIND_TEXTAREA, "rows": 3, "placeholder": "Document description"}
            ),
            "keywords": forms.TextInput(attrs={"class": TAILWIND_INPUT, "placeholder": "Keywords (comma-separated)"}),
            "is_confidential": forms.CheckboxInput(
                attrs={"class": "w-4 h-4 text-ardt-blue border-gray-300 rounded focus:ring-ardt-blue"}
            ),
            "expires_at": forms.DateInput(attrs={"class": TAILWIND_INPUT, "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = DocumentCategory.objects.filter(is_active=True)
        # File is not required when editing
        if self.instance.pk:
            self.fields["file"].required = False

    def clean_code(self):
        """Ensure code is uppercase."""
        code = self.cleaned_data.get("code")
        if code:
            return code.upper()
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Calculate file size and mime type if file uploaded
        if self.cleaned_data.get("file"):
            uploaded_file = self.cleaned_data["file"]
            instance.file_size = uploaded_file.size
            instance.mime_type = uploaded_file.content_type or ""

        if commit:
            instance.save()
            self.save_m2m()

        return instance
