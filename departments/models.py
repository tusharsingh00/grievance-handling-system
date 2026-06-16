from django.db import models
from django.conf import settings


class Department(models.Model):
    DEPARTMENT_CHOICES = [
        ('technical', 'Technical Support'),
        ('hr', 'HR Related Issues'),
        ('facility', 'Facility Management'),
        ('security', 'Security Issues'),
        ('academic', 'Academic Matters'),
        ('financial', 'Financial Concerns'),
        ('general', 'General Inquiries')
    ]
    #5/5/25
    # name = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, unique=True)
    # description = models.TextField(blank=True)
    # head = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name='department_head'
    # )
    name = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

class DepartmentStaff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='staff')
    designation = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department.get_name_display()}"


class StatusUpdate(models.Model):
    grievance = models.ForeignKey('grievances.Grievance', on_delete=models.CASCADE, related_name='status_updates')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Status update for Grievance #{self.grievance.id}"