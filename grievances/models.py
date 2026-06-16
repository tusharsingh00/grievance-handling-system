from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Count
from departments.models import Department





class Category(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical Support'),
        ('hr', 'HR Related Issues'),
        ('facility', 'Facility Management'),
        ('security', 'Security Issues'),
        ('academic', 'Academic Matters'),
        ('financial', 'Financial Concerns'),
        ('general', 'General Inquiries')
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name_plural = "Categories"
  



class Grievance(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='grievances')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='submitted_grievances'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_grievances'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='department_grievances'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='grievance_attachments/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Set department based on category if not already set
        if not self.department_id and self.category_id:
            self.department = self.category.department
        
        # Set due date based on priority if not set
        if not self.due_date:
            priority_hours = {
                'low': 72,
                'medium': 48,
                'high': 24,
                'urgent': 12
            }
            self.due_date = timezone.now() + timezone.timedelta(hours=priority_hours[self.priority])

        # Set resolved_at timestamp when status changes to resolved
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


        
class Comment(models.Model):
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(upload_to='comment_attachments/', blank=True, null=True)
    is_internal = models.BooleanField(
        default=False, 
        help_text="Internal notes visible only to staff"
    )

    def __str__(self):
        return f'Comment by {self.user.username} on {self.grievance.title}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.is_internal:
            self.send_comment_notification()

    def send_comment_notification(self):
        subject = f'New Comment on Grievance #{self.grievance.id}'
        message = render_to_string('grievances/email/new_comment.html', {
            'comment': self
        })
        recipients = [self.grievance.submitted_by.email]
        if self.grievance.assigned_to:
            recipients.append(self.grievance.assigned_to.email)
        
        send_mail(
            subject,
            message,
            'noreply@example.com',
            recipients,
            fail_silently=True,
        )

class Escalation(models.Model):
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE)
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='escalated_by'
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='escalated_to'
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolution_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Escalation for {self.grievance.title}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if self.resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self.send_escalation_notification()

    def send_escalation_notification(self):
        subject = f'Grievance #{self.grievance.id} Escalated'
        message = render_to_string('grievances/email/escalation_notification.html', {
            'escalation': self
        })
        send_mail(
            subject,
            message,
            'noreply@example.com',
            [self.escalated_to.email],
            fail_silently=True,
        )



class Feedback(models.Model):
    RATING_CHOICES = [
        (1, '1 - Very Dissatisfied'),
        (2, '2 - Dissatisfied'),
        (3, '3 - Neutral'),
        (4, '4 - Satisfied'),
        (5, '5 - Very Satisfied')
    ]

    grievance = models.OneToOneField('Grievance', on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    resolution_satisfaction = models.IntegerField(choices=RATING_CHOICES)
    response_time_rating = models.IntegerField(choices=RATING_CHOICES)
    suggestions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback for Grievance #{self.grievance.id}"

    class Meta:
        ordering = ['-created_at']