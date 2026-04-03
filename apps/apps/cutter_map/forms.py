"""
Cutter Map Forms
"""

from django import forms
from .models import CutterMapDocument


class CutterMapUploadForm(forms.ModelForm):
    """Form for uploading cutter map PDFs."""

    class Meta:
        model = CutterMapDocument
        fields = ['original_pdf']
        widgets = {
            'original_pdf': forms.FileInput(attrs={
                'accept': '.pdf',
                'class': 'form-control'
            })
        }

    def clean_original_pdf(self):
        pdf = self.cleaned_data.get('original_pdf')
        if pdf:
            if not pdf.name.lower().endswith('.pdf'):
                raise forms.ValidationError('File must be a PDF.')
            if pdf.size > 16 * 1024 * 1024:  # 16MB limit
                raise forms.ValidationError('File size must be less than 16MB.')
        return pdf
