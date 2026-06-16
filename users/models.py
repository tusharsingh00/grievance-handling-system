from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('staff', 'Department Staff'),
        ('admin', 'Department Admin')
    ]
    
    DEPARTMENT_CHOICES = [
        ('technical', 'Technical Support'),
        ('hr', 'HR Related Issues'),
        ('facility', 'Facility Management'),
        ('security', 'Security Issues'),
        ('academic', 'Academic Matters'),
        ('financial', 'Financial Concerns'),
        ('general', 'General Inquiries')
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    def save(self, *args, **kwargs):
        # Ensure department staff and admin users have a department
        if self.role in ['staff', 'admin'] and not self.department:
            self.department = 'general'
        super().save(*args, **kwargs)