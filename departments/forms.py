from django import forms
from grievances.models import Grievance

class StatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Grievance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add remarks about this status update...'
        }),
        required=False
    )