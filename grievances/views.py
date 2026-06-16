from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Avg , F, ExpressionWrapper, fields, DurationField
from .models import Grievance, Comment, Escalation, Category,Feedback
from .forms import GrievanceForm, CommentForm, EscalationForm,FeedbackForm,ReportFilterForm
from users.models import CustomUser
from django.contrib.auth import logout
from departments.models import Department
from django.db.models.functions import TruncMonth, ExtractMonth
from django.http import HttpResponse, FileResponse, JsonResponse
import csv
import xlsxwriter
from io import BytesIO
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import logging
from .forms import CommentForm, StatusUpdateForm

class GrievanceListView(LoginRequiredMixin, ListView):
    model = Grievance
    template_name = 'grievances/grievance_list.html'
    context_object_name = 'grievances'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role in ['staff', 'admin']:
            # Filter by user's department name
            return Grievance.objects.filter(
                department__name=user.department
            ).order_by('-created_at')
        return Grievance.objects.filter(
            submitted_by=user
        ).order_by('-created_at')


# class GrievanceDetailView(LoginRequiredMixin, DetailView):
#     model = Grievance
#     template_name = 'grievances/grievance_detail.html'
#     context_object_name = 'grievance'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['comment_form'] = CommentForm()
#         return context

class GrievanceDetailView(LoginRequiredMixin, DetailView):
    model = Grievance
    template_name = 'grievances/grievance_detail.html'
    context_object_name = 'grievance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.all().order_by('-created_at')
        context['status_updates'] = self.object.status_updates.all().order_by('-created_at')
        context['form'] = StatusUpdateForm()  # For compatibility, though not used in template
        return context

class GrievanceCreateView(LoginRequiredMixin, CreateView):
    model = Grievance
    form_class = GrievanceForm
    template_name = 'grievances/grievance_form.html'
    success_url = reverse_lazy('grievance-list')

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        # Get department based on category
        category = form.cleaned_data['category']
        department = Department.objects.get(name=category.name)
        form.instance.department = department
        response = super().form_valid(form)
        messages.success(self.request, 'Grievance submitted successfully!')
        return response

        
class GrievanceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Grievance
    form_class = GrievanceForm
    template_name = 'grievances/grievance_form.html'
    success_url = reverse_lazy('grievance-list')

    def test_func(self):
        grievance = self.get_object()
        return self.request.user.role in ['staff', 'admin'] or grievance.submitted_by == self.request.user




# @login_required
# def add_comment(request, pk):
#     grievance = get_object_or_404(Grievance, pk=pk)
#     if request.method == 'POST':
#         form = CommentForm(request.POST, request.FILES)
#         if form.is_valid():
#             comment = form.save(commit=False)
#             comment.grievance = grievance
#             comment.user = request.user
#             comment.save()
            
#             # Update grievance last_updated timestamp
#             grievance.updated_at = timezone.now()
#             grievance.save()
            
#             messages.success(request, 'Comment added successfully!')
#         else:
#             messages.error(request, 'Error adding comment.')
#     return redirect('grievance-detail', pk=pk)

@login_required
def add_comment(request, pk):
    grievance = get_object_or_404(Grievance, id=pk)
    logger.info(f"Processing comment for grievance ID: {pk}, User: {request.user.username}")
    
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        logger.info(f"Form data: {request.POST}, Files: {request.FILES}")
        if form.is_valid():
            comment = form.save(commit=False)
            comment.grievance = grievance
            comment.created_by = request.user
            comment.created_at = timezone.now()
            comment.save()
            logger.info(f"Comment saved: ID={comment.id}, Text={comment.text}")
            messages.success(request, 'Comment added successfully.')
            return redirect('grievance_detail', pk=grievance.id)
        else:
            logger.warning(f"Form invalid, errors: {form.errors}")
            return render(request, 'grievances/grievance_detail.html', {
                'grievance': grievance,
                'comment_form': form,
                'comments': grievance.comments.all().order_by('-created_at'),
                'status_updates': grievance.status_updates.all().order_by('-created_at'),
                'form': StatusUpdateForm()
            })
    else:
        logger.warning(f"Invalid method: {request.method} for add_comment")
        return redirect('grievance_detail', pk=grievance.id)

@login_required
def escalate_grievance(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.method == 'POST':
        form = EscalationForm(request.POST)
        if form.is_valid():
            escalation = form.save(commit=False)
            escalation.grievance = grievance
            escalation.escalated_by = request.user
            escalation.save()
            messages.success(request, 'Grievance escalated successfully!')
    return redirect('grievance-detail', pk=pk)


#imp one
"""@login_required
def dashboard(request):
    user = request.user
    
    # Get department object for staff/admin users
    department = None
    if user.role in ['staff', 'admin']:
        department = Department.objects.get(name=user.department)
        grievances = Grievance.objects.filter(department=department)
    else:
        grievances = Grievance.objects.filter(submitted_by=user)
    
    context = {
        'total_grievances': grievances.count(),
        'pending_grievances': grievances.filter(status__in=['new', 'in_progress']).count(),
        'resolved_grievances': grievances.filter(status='resolved').count(),
        'recent_grievances': grievances.order_by('-created_at')[:5],
    }

    if user.role in ['staff', 'admin']:
        context.update({
            'overdue_grievances': grievances.filter(
                status__in=['new', 'in_progress'],
                due_date__lt=timezone.now()
            ).count(),
            'high_priority_grievances': grievances.filter(
                priority__in=['urgent', 'high'],
                status__in=['new', 'in_progress']
            ).count(),
            'assigned_grievances': grievances.filter(assigned_to=user).count(),
            'department_stats': {
                'total': grievances.count(),
                'pending': grievances.filter(status__in=['new', 'in_progress']).count(),
                'resolved': grievances.filter(status='resolved').count(),
                'resolved_percentage': (
                    grievances.filter(status='resolved').count() / grievances.count() * 100
                    if grievances.count() > 0 else 0
                ),
                'pending_percentage': (
                    grievances.filter(status__in=['new', 'in_progress']).count() / grievances.count() * 100
                    if grievances.count() > 0 else 0
                )
            }
        })

    return render(request, 'grievances/dashboard.html', context)
"""

@login_required
def dashboard(request):
    user = request.user
    
    # Get department object for staff/admin users
    department = None
    if user.role in ['staff', 'admin']:
        department = Department.objects.get(name=user.department)
        grievances = Grievance.objects.filter(department=department)
    else:
        grievances = Grievance.objects.filter(submitted_by=user)
    
    # Get recent grievances with submitted_by information
    recent_grievances = grievances.select_related('submitted_by', 'category').order_by('-created_at')[:5]
    
    context = {
        'total_grievances': grievances.count(),
        'pending_grievances': grievances.filter(status__in=['new', 'in_progress']).count(),
        'resolved_grievances': grievances.filter(status='resolved').count(),
        'recent_grievances': recent_grievances,
    }

    if user.role in ['staff', 'admin']:
        context.update({
            'overdue_grievances': grievances.filter(
                status__in=['new', 'in_progress'],
                due_date__lt=timezone.now()
            ).count(),
            'high_priority_grievances': grievances.filter(
                priority__in=['urgent', 'high'],
                status__in=['new', 'in_progress']
            ).count(),
            'assigned_grievances': grievances.filter(assigned_to=user).count(),
            'department_stats': {
                'total': grievances.count(),
                'pending': grievances.filter(status__in=['new', 'in_progress']).count(),
                'resolved': grievances.filter(status='resolved').count(),
                'resolved_percentage': (
                    grievances.filter(status='resolved').count() / grievances.count() * 100
                    if grievances.count() > 0 else 0
                ),
                'pending_percentage': (
                    grievances.filter(status__in=['new', 'in_progress']).count() / grievances.count() * 100
                    if grievances.count() > 0 else 0
                )
            }
        })

    return render(request, 'grievances/dashboard.html', context)


"""@login_required
def update_grievance_status(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        
        if new_status:
            old_status = grievance.status
            grievance.status = new_status
            if new_status == 'resolved':
                grievance.resolved_at = timezone.now()
            grievance.save()
            
            # Create status update
            status_update = StatusUpdate.objects.create(
                grievance=grievance,
                old_status=old_status,
                new_status=new_status,
                updated_by=request.user,
                remarks=remarks
            )
            
            # Send notification to user
            messages.success(request, f'Grievance status updated to {grievance.get_status_display()}')
            
            # Create notification for the submitter
            if grievance.submitted_by != request.user:
                notification_message = f'Your grievance "{grievance.title}" has been {grievance.get_status_display()}'
                if remarks:
                    notification_message += f'. Remarks: {remarks}'
                
                messages.info(
                    request._request,
                    notification_message
                )
                
                # If resolved, send feedback request
                if new_status == 'resolved':
                    messages.success(
                        request._request,
                        f'Your grievance "{grievance.title}" has been resolved. Please provide feedback.'
                    )
            
            return JsonResponse({
                'status': 'success',
                'new_status': grievance.get_status_display(),
                'message': 'Status updated successfully'
            })
    
    return JsonResponse({'status': 'error'}, status=400)

"""
@login_required
def update_grievance_status(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            old_status = grievance.status
            grievance.status = new_status
            if new_status == 'resolved':
                grievance.resolved_at = timezone.now()
            grievance.save()
            
            # Create status update
            StatusUpdate.objects.create(
                grievance=grievance,
                old_status=old_status,
                new_status=new_status,
                updated_by=request.user
            )
            
            # Send notification to user
            messages.success(request, f'Grievance status updated to {grievance.get_status_display()}')
            
            # Notify the submitter
            if grievance.submitted_by != request.user:
                messages.info(
                    grievance.submitted_by,
                    f'Your grievance "{grievance.title}" has been updated to {grievance.get_status_display()}'
                )
            
            return JsonResponse({
                'status': 'success',
                'new_status': grievance.get_status_display()
            })
    
    return JsonResponse({'status': 'error'}, status=400)

logger = logging.getLogger(__name__)
@login_required
def reports(request):
    user = request.user
    
    if user.role in ['staff', 'admin']:
        # Department staff/admin view
        department = Department.objects.get(name=user.department)
        grievances = Grievance.objects.filter(department=department)
    else:
        # Regular user view
        grievances = Grievance.objects.filter(submitted_by=user)
    
    # Calculate basic statistics
    total_grievances = grievances.count()
    resolved_count = grievances.filter(status='resolved').count()
    pending_count = grievances.filter(status__in=['new', 'in_progress']).count()
    resolution_rate = (resolved_count / total_grievances * 100) if total_grievances > 0 else 0
    
    # Category distribution
    category_stats = grievances.values('category__name').annotate(count=Count('id'))
    category_labels = [stat['category__name'] for stat in category_stats]
    category_data = [stat['count'] for stat in category_stats]
    
    # Status distribution
    status_stats = grievances.values('status').annotate(count=Count('id'))
    status_labels = [stat['status'] for stat in status_stats]
    status_data = [stat['count'] for stat in status_stats]
    
    # Priority distribution
    priority_stats = grievances.values('priority').annotate(count=Count('id'))
    priority_labels = [stat['priority'] for stat in priority_stats]
    priority_data = [stat['count'] for stat in priority_stats]
    
    # Monthly trend
    monthly_stats = grievances.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    trend_labels = [stat['month'].strftime('%B %Y') for stat in monthly_stats]
    trend_data = [stat['count'] for stat in monthly_stats]
    
    # Response time analysis (for staff/admin)
    if user.role in ['staff', 'admin']:
        avg_response_time = grievances.filter(
            status='resolved'
        ).exclude(
            resolved_at=None
        ).annotate(
            response_time=models.F('resolved_at') - models.F('created_at')
        ).aggregate(
            avg=models.Avg('response_time')
        )['avg']
    else:
        avg_response_time = None
    
    context = {
        'total_grievances': total_grievances,
        'resolved_count': resolved_count,
        'pending_count': pending_count,
        'resolution_rate': round(resolution_rate, 1),
        'category_labels': category_labels,
        'category_data': category_data,
        'status_labels': status_labels,
        'status_data': status_data,
        'priority_labels': priority_labels,
        'priority_data': priority_data,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'avg_response_time': avg_response_time,
    }
    
    return render(request, 'users/reports.html', context)



@login_required
def reports(request):
    # Get user-specific grievances
    if request.user.role in ['staff', 'admin']:
        grievances = Grievance.objects.filter(department__name=request.user.department)
    else:
        grievances = Grievance.objects.filter(submitted_by=request.user)
    
    form = ReportFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['start_date']:
            grievances = grievances.filter(created_at__gte=form.cleaned_data['start_date'])
        if form.cleaned_data['end_date']:
            grievances = grievances.filter(created_at__lte=form.cleaned_data['end_date'])
        if form.cleaned_data['status']:
            grievances = grievances.filter(status__in=form.cleaned_data['status'])
        if form.cleaned_data['category']:
            grievances = grievances.filter(category__in=form.cleaned_data['category'])
        if form.cleaned_data['priority']:
            grievances = grievances.filter(priority__in=form.cleaned_data['priority'])
    
    # Handle export formats
    export_format = request.GET.get('export_format')
    if export_format == 'csv':
        return export_csv(request, grievances)
    elif export_format == 'excel':
        return export_excel(request, grievances)
    
    return render(request, 'grievances/report_generator.html', {
        'form': form,
        'grievances': grievances
    })



def submit_feedback(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)

    # Check if feedback already exists for this grievance
    if Feedback.objects.filter(grievance=grievance).exists():
        messages.error(request, 'Feedback has already been submitted for this grievance.')
        return redirect('grievance-detail', pk=pk)  # Redirect to the grievance detail page

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.grievance = grievance
            feedback.user = request.user
            feedback.save()

            # Notify department staff about new feedback
            create_staff_notification(
                grievance.department.staff.all(),
                f'New feedback received for grievance #{grievance.id}'
            )

            messages.success(request, 'Thank you for your feedback!')
            return redirect('dashboard')
    else:
        form = FeedbackForm()

    return render(request, 'grievances/feedback_form.html', {
        'form': form,
        'grievance': grievance
    })

    
def create_staff_notification(staff_users, message):
    for staff in staff_users:
        Notification.objects.create(
            user=staff,
            message=message,
            notification_type='feedback'
        )


@login_required
def analytics_dashboard(request):
    # Get user-specific grievances
    if request.user.role in ['staff', 'admin']:
        grievances = Grievance.objects.filter(department__name=request.user.department)
    else:
        grievances = Grievance.objects.filter(submitted_by=request.user)
    
    # Calculate statistics
    total_grievances = grievances.count()
    resolved_grievances = grievances.filter(status='resolved').count()
    
    # Calculate monthly trend data
    monthly_data = grievances.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    monthly_labels = [entry['month'].strftime('%B %Y') for entry in monthly_data]
    monthly_counts = [entry['count'] for entry in monthly_data]
    
    # Calculate category distribution
    category_data = grievances.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    category_labels = [entry['category__name'] for entry in category_data]
    category_counts = [entry['count'] for entry in category_data]
    
    # Calculate average resolution time
    resolved_grievances_qs = grievances.filter(
        status='resolved',
        resolved_at__isnull=False
    ).annotate(
        resolution_time=ExpressionWrapper(
            F('resolved_at') - F('created_at'),
            output_field=DurationField()
        )
    )
    
    avg_resolution_time = resolved_grievances_qs.aggregate(
        avg_time=Avg('resolution_time')
    )['avg_time']
    
    # Get feedback statistics
    feedback_stats = Feedback.objects.filter(
        grievance__in=grievances
    ).aggregate(
        avg_rating=Avg('rating'),
        avg_satisfaction=Avg('resolution_satisfaction'),
        avg_response_time=Avg('response_time_rating')
    )
    
    context = {
        'total_grievances': total_grievances,
        'resolved_grievances': resolved_grievances,
        'avg_resolution_time': avg_resolution_time,
        'feedback_stats': feedback_stats,
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
        'category_labels': category_labels,
        'category_counts': category_counts,
    }
    
    return render(request, 'grievances/analytics_dashboard.html', context)

@login_required
def generate_report(request):
    user = request.user
    if user.role in ['staff', 'admin']:
        grievances = Grievance.objects.filter(department__name=user.department)
    else:
        grievances = Grievance.objects.filter(submitted_by=user)
    
    form = ReportFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['start_date']:
            grievances = grievances.filter(created_at__gte=form.cleaned_data['start_date'])
        if form.cleaned_data['end_date']:
            grievances = grievances.filter(created_at__lte=form.cleaned_data['end_date'])
        if form.cleaned_data['status']:
            grievances = grievances.filter(status__in=form.cleaned_data['status'])
        if form.cleaned_data['category']:
            grievances = grievances.filter(category__in=form.cleaned_data['category'])
        if form.cleaned_data['priority']:
            grievances = grievances.filter(priority__in=form.cleaned_data['priority'])
    
    # Handle export formats
    export_format = request.GET.get('export_format')
    if export_format == 'csv':
        return export_csv(request, grievances)
    elif export_format == 'excel':
        return export_excel(request, grievances)
    
    return render(request, 'grievances/report_generator.html', {
        'form': form,
        'grievances': grievances
    })


def export_csv(request, grievances):
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="grievances_report_{timestamp}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Category', 'Status', 'Priority', 'Submitted By', 'Created At', 'Resolved At'])
    
    for grievance in grievances:
        writer.writerow([
            grievance.id,
            grievance.title,
            grievance.category.name,
            grievance.get_status_display(),
            grievance.get_priority_display(),
            grievance.submitted_by.get_full_name() or grievance.submitted_by.username,
            grievance.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            grievance.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if grievance.resolved_at else 'N/A'
        ])
    
    return response


def export_excel(request, grievances):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Add headers with formatting
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0066cc',
        'color': 'white',
        'border': 1
    })
    
    headers = ['ID', 'Title', 'Category', 'Status', 'Priority', 'Submitted By', 'Created At', 'Resolved At']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Add data with formatting
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
    cell_format = workbook.add_format({'border': 1})
    
    for row, grievance in enumerate(grievances, start=1):
        worksheet.write(row, 0, grievance.id, cell_format)
        worksheet.write(row, 1, grievance.title, cell_format)
        worksheet.write(row, 2, grievance.category.name, cell_format)
        worksheet.write(row, 3, grievance.get_status_display(), cell_format)
        worksheet.write(row, 4, grievance.get_priority_display(), cell_format)
        worksheet.write(row, 5, grievance.submitted_by.get_full_name() or grievance.submitted_by.username, cell_format)
        worksheet.write(row, 6, grievance.created_at, date_format)
        if grievance.resolved_at:
            worksheet.write(row, 7, grievance.resolved_at, date_format)
        else:
            worksheet.write(row, 7, 'N/A', cell_format)
    
    # Adjust column widths
    for col in range(len(headers)):
        worksheet.set_column(col, col, 15)
    
    workbook.close()
    output.seek(0)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="grievances_report_{timestamp}.xlsx"'
    return response



@login_required
def reports_dashboard(request):
    user = request.user
    if user.role in ['staff', 'admin']:
        grievances = Grievance.objects.filter(department__name=user.department)
    else:
        grievances = Grievance.objects.filter(submitted_by=user)
    
    # Calculate report statistics
    total_grievances = grievances.count()
    resolved_count = grievances.filter(status='resolved').count()
    resolution_rate = (resolved_count / total_grievances * 100) if total_grievances > 0 else 0
    
    # Get category distribution
    category_stats = grievances.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get monthly trend
    monthly_stats = grievances.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'total_grievances': total_grievances,
        'resolved_count': resolved_count,
        'resolution_rate': round(resolution_rate, 1),
        'category_stats': category_stats,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'grievances/reports_dashboard.html', context)

# def add_comment(request, grievance_id):
#     grievance = get_object_or_404(Grievance, pk=grievance_id)

#     if request.method == 'POST':
#         comment_text = request.POST.get('comment')

#         if comment_text:
#             # Create a new comment
#             comment = Comment.objects.create(grievance=grievance, user=request.user, content=comment_text)

#             # Optionally, send an email or handle attachments here

#             # Return a success response as JSON
#             return JsonResponse({'status': 'success', 'message': 'Comment added successfully.'})

#         else:
#             return JsonResponse({'status': 'error', 'message': 'Comment text is required.'})

#     return render(request, 'grievances/grievance_detail.html', {'grievance': grievance})

@login_required
def add_comment(request, pk):
    grievance = get_object_or_404(Grievance, id=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.grievance = grievance
            comment.created_by = request.user
            comment.created_at = timezone.now()
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('grievance_detail', pk=grievance.id)
    else:
        form = CommentForm()
    
    return render(request, 'grievances/grievance_detail.html', {
    'grievance': grievance,
    'comment_form': form,
    'comments': grievance.comments.all()
})
