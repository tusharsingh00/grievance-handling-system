from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'department', 'phone')
        widgets = {
            'department': forms.Select(choices=[
                ('hr', 'Human Resources'),
                ('it', 'Information Technology'),
                ('finance', 'Finance'),
                ('operations', 'Operations'),
                ('support', 'Customer Support')
            ]),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
        }

class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ('email', 'department', 'phone')
        widgets = {
            'department': forms.Select(choices=[
                ('hr', 'Human Resources'),
                ('it', 'Information Technology'),
                ('finance', 'Finance'),
                ('operations', 'Operations'),
                ('support', 'Customer Support')
            ]),
        }

class DepartmentUserCreationForm(UserCreationForm):
    DEPARTMENT_CHOICES = [
        ('it', 'IT Department'),
        ('hr', 'Human Resources'),
        ('facilities', 'Facilities Management'),
        ('legal', 'Legal Department'),
        ('academic', 'Academic Department'),
        ('operations', 'Operations'),
        ('security', 'Security'),
        ('general', 'General')
    ]

    department = forms.ChoiceField(choices=DEPARTMENT_CHOICES, required=True)
    role = forms.ChoiceField(choices=[('staff', 'Department Staff'), ('admin', 'Department Admin')])

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'department', 'role', 'phone')