from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.utils import timezone

from django.contrib import messages
from django.db.models import Count, Q
from .models import Department, DepartmentStaff, StatusUpdate
from grievances.models import Grievance
from .forms import StatusUpdateForm



def is_department_staff(user):
    return user.role in ['staff', 'admin']


"""@login_required
@user_passes_test(is_department_staff)
def department_dashboard(request):
    user = request.user
    department = Department.objects.get(name=user.department)
    
    # Get all grievances for the department
    grievances = Grievance.objects.filter(department=department)
    
    # Calculate statistics
    total_grievances = grievances.count()
    pending_grievances = grievances.filter(status__in=['new', 'in_progress']).count()
    resolved_grievances = grievances.filter(status='resolved').count()
    high_priority_grievances = grievances.filter(
        priority__in=['high', 'urgent'],
        status__in=['new', 'in_progress']
    ).count()
    
    # Get recent grievances
    recent_grievances = grievances.order_by('-created_at')[:10]
    
    # Calculate status distribution
    status_distribution = grievances.values('status').annotate(count=Count('id'))
    
    # Calculate priority distribution
    priority_distribution = grievances.values('priority').annotate(count=Count('id'))
    
    context = {
        'department': department,
        'total_grievances': total_grievances,
        'pending_grievances': pending_grievances,
        'resolved_grievances': resolved_grievances,
        'high_priority_grievances': high_priority_grievances,
        'recent_grievances': recent_grievances,
        'status_distribution': status_distribution,
        'priority_distribution': priority_distribution,
    }
    
    return render(request, 'departments/dashboard.html', context)

"""
@login_required
@user_passes_test(is_department_staff)
def department_dashboard(request):
    user = request.user
    department = Department.objects.get(name=user.department)
    
    # Get all active (non-resolved) grievances for the department
    grievances = Grievance.objects.filter(
        department=department,
        status__in=['new', 'in_progress']
    ).select_related('submitted_by')
    
    # Calculate statistics
    total_grievances = Grievance.objects.filter(department=department).count()
    pending_grievances = grievances.count()
    resolved_grievances = Grievance.objects.filter(
        department=department,
        status='resolved'
    ).count()
    high_priority_grievances = grievances.filter(
        priority__in=['high', 'urgent']
    ).count()
    
    # Get recent grievances with submitted_by information
    recent_grievances = grievances.order_by('-created_at')[:10]
    
    # Calculate status distribution
    status_distribution = Grievance.objects.filter(
        department=department
    ).values('status').annotate(count=Count('id'))
    
    # Calculate priority distribution
    priority_distribution = grievances.values('priority').annotate(count=Count('id'))
    
    context = {
        'department': department,
        'total_grievances': total_grievances,
        'pending_grievances': pending_grievances,
        'resolved_grievances': resolved_grievances,
        'high_priority_grievances': high_priority_grievances,
        'recent_grievances': recent_grievances,
        'status_distribution': status_distribution,
        'priority_distribution': priority_distribution,
    }
    
    return render(request, 'departments/dashboard.html', context)

class DepartmentGrievanceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Grievance
    template_name = 'departments/grievance_list.html'
    context_object_name = 'grievances'
    paginate_by = 10

    def test_func(self):
        return is_department_staff(self.request.user)

    def get_queryset(self):
        department = self.request.user.departmentstaff.department
        return Grievance.objects.filter(department=department).order_by('-created_at')


@login_required
@user_passes_test(is_department_staff)
def department_grievance_list(request):
    user = request.user
    department = Department.objects.get(name=user.department)
    
    # Get all grievances for the department with related fields
    grievances = Grievance.objects.filter(department=department).select_related('submitted_by')
    
    # Apply status filter if provided
    status_filter = request.GET.get('status')
    if status_filter:
        grievances = grievances.filter(status=status_filter)
    
    # Order by created date
    grievances = grievances.order_by('-created_at')
    
    context = {
        'grievances': grievances,
        'status_choices': Grievance.STATUS_CHOICES,
        'current_status': status_filter,
    }
    return render(request, 'departments/grievance_list.html', context)


@login_required
@user_passes_test(is_department_staff)
def grievance_list(request):
    staff = request.user.departmentstaff
    grievances = Grievance.objects.filter(department=staff.department.name)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        grievances = grievances.filter(status=status)
    
    context = {
        'grievances': grievances,
        'current_status': status
    }
    return render(request, 'departments/grievance_list.html', context)



@login_required
@user_passes_test(is_department_staff)
def update_grievance_status(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    department = Department.objects.get(name=request.user.department)
    
    # Check if the grievance belongs to the department
    if grievance.department != department:
        messages.error(request, "You don't have permission to update this grievance.")
        return redirect('department-dashboard')
    
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            remarks = form.cleaned_data['remarks']
            
            # Update grievance status
            old_status = grievance.status
            grievance.status = new_status
            if new_status == 'resolved':
                grievance.resolved_at = timezone.now()
            grievance.save()
            
            # Create status update record
            StatusUpdate.objects.create(
                grievance=grievance,
                updated_by=request.user,
                old_status=old_status,
                new_status=new_status,
                remarks=remarks
            )
            
            # Send notifications
            messages.success(request, 'Grievance status updated successfully.')
            
            # Notify the submitter
            notification_message = f'Your grievance "{grievance.title}" has been {grievance.get_status_display()}'
            if remarks:
                notification_message += f'. Remarks: {remarks}'
            
            messages.info(request, notification_message)
            
            # If resolved, prompt for feedback
            if new_status == 'resolved':
                messages.success(
                    request,
                    f'Your grievance has been resolved. Please provide feedback.'
                )
            
            # Redirect based on where the update was initiated
            if request.GET.get('next'):
                return redirect(request.GET.get('next'))
            return redirect('department-grievance-list')
    else:
        form = StatusUpdateForm(initial={'status': grievance.status})
    
    return render(request, 'departments/update_status.html', {
        'form': form,
        'grievance': grievance
    })

@login_required
def department_staff(request):
    if not request.user.is_staff:
        raise PermissionDenied
        
    department = request.user.department
    staff_members = department.staff.all()
    
    context = {
        'department': department,
        'staff_members': staff_members,
    }
    
    return render(request, 'departments/staff.html', context)


