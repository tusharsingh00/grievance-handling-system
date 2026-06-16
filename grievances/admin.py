from django.contrib import admin
from .models import Category, Grievance, Comment, Escalation

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'priority', 'submitted_by', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description')
    raw_id_fields = ('submitted_by', 'assigned_to')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('grievance', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content',)
    raw_id_fields = ('grievance', 'user')

@admin.register(Escalation)
class EscalationAdmin(admin.ModelAdmin):
    list_display = ('grievance', 'escalated_by', 'escalated_to', 'created_at', 'resolved')
    list_filter = ('resolved', 'created_at')
    search_fields = ('reason', 'resolution_note')
    raw_id_fields = ('grievance', 'escalated_by', 'escalated_to')