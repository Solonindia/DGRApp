from django import forms
from .models import ChecklistItem

class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ['report_type', 'checkpoint', 'frequency_level']  # ✅ include frequency_level

