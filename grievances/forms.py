from django import forms
from .models import Grievance, Comment, Escalation, Category,Feedback


class GrievanceForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = ['title', 'category', 'priority', 'description', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter grievance title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your grievance'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 5MB')
            
            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if attachment.content_type not in allowed_types:
                raise forms.ValidationError('Only JPEG, PNG and PDF files are allowed')
        return attachment

class EscalationForm(forms.ModelForm):
    class Meta:
        model = Escalation
        fields = ['escalated_to', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Please provide the reason for escalation...'
            }),
            'escalated_to': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['escalated_to'].queryset = self.fields['escalated_to'].queryset.filter(
            role__in=['staff', 'admin']
        )

    def clean_reason(self):
        reason = self.cleaned_data.get('reason')
        if len(reason.split()) < 10:
            raise forms.ValidationError('Please provide a detailed reason for escalation (at least 10 words)')
        return reason

        
class StatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Grievance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Add notes about this status update...'
        })
    )



class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comments', 'resolution_satisfaction', 'response_time_rating', 'suggestions']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'resolution_satisfaction': forms.Select(attrs={'class': 'form-select'}),
            'response_time_rating': forms.Select(attrs={'class': 'form-select'}),
            'suggestions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

class ReportFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    status = forms.MultipleChoiceField(
        choices=Grievance.STATUS_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    priority = forms.MultipleChoiceField(
        choices=Grievance.PRIORITY_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )