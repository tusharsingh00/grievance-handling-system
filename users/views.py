from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserChangeForm,DepartmentUserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from grievances.models import Grievance
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login, logout
from django.db.models import Count,Q
from django.utils import timezone
from datetime import timedelta
from departments.models import Department
from .models import CustomUser  # Add this import




class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    
    def get_success_url(self):
        if self.request.user.role in ['staff', 'admin']:
            return reverse_lazy('department-dashboard')
        return reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.role in ['staff', 'admin']:
            messages.success(self.request, f'Welcome back, {self.request.user.get_full_name()}! You are logged in to the department dashboard.')
        else:
            messages.success(self.request, f'Welcome back, {self.request.user.get_full_name()}!')
        return response

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


class CustomLogoutView(LogoutView):
    template_name = 'users/logout.html'
    next_page = 'login'
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            messages.success(request, 'You have been successfully logged out.')
            return super().dispatch(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

@user_passes_test(lambda u: u.role == 'admin')
def register_department_user(request):
    if request.method == 'POST':
        form = DepartmentUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.department = form.cleaned_data['department']
            user.role = form.cleaned_data['role']
            user.save()
            messages.success(request, f'Department {user.get_role_display()} account created successfully!')
            return redirect('department-dashboard')
    else:
        form = DepartmentUserCreationForm()
    
    return render(request, 'users/register_department.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    grievances = Grievance.objects.filter(submitted_by=request.user)
    context = {
        'form': form,
        'total_grievances': grievances.count(),
        'pending_grievances': grievances.filter(status__in=['new', 'in_progress']).count(),
        'resolved_grievances': grievances.filter(status='resolved').count(),
    }
    return render(request, 'users/profile.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def reports(request):
    user = request.user
    grievances = Grievance.objects.filter(submitted_by=user)
    
    total_grievances = grievances.count()
    pending_count = grievances.filter(status__in=['new', 'in_progress']).count()
    resolved_count = grievances.filter(status='resolved').count()
    resolution_rate = round((resolved_count / total_grievances * 100) if total_grievances > 0 else 0, 1)
    
    category_stats = grievances.values('category__name').annotate(count=Count('id'))
    category_labels = [stat['category__name'] for stat in category_stats]
    category_data = [stat['count'] for stat in category_stats]
    
    status_stats = grievances.values('status').annotate(count=Count('id'))
    status_labels = [stat['status'] for stat in status_stats]
    status_data = [stat['count'] for stat in status_stats]
    
    six_months_ago = timezone.now() - timedelta(days=180)
    trend_stats = (
        grievances
        .filter(created_at__gte=six_months_ago)
        .extra(select={'month': "DATE_FORMAT(created_at, '%%Y-%%m')"})
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    trend_labels = [stat['month'] for stat in trend_stats]
    trend_data = [stat['count'] for stat in trend_stats]
    
    priority_stats = grievances.values('priority').annotate(count=Count('id'))
    priority_labels = [stat['priority'] for stat in priority_stats]
    priority_data = [stat['count'] for stat in priority_stats]
    
    context = {
        'total_grievances': total_grievances,
        'pending_count': pending_count,
        'resolved_count': resolved_count,
        'resolution_rate': resolution_rate,
        'category_labels': category_labels,
        'category_data': category_data,
        'status_labels': status_labels,
        'status_data': status_data,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'priority_labels': priority_labels,
        'priority_data': priority_data,
    }
    
    return render(request, 'users/reports.html', context)


from django.views.generic import TemplateView  # or appropriate view import

class DepartmentLoginView(TemplateView):
    template_name = 'users/department_login.html'  # Replace with your actual template



@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    # Get overall statistics
    total_users = CustomUser.objects.count()
    total_departments = Department.objects.count()
    total_grievances = Grievance.objects.count()
    resolved_grievances = Grievance.objects.filter(status='resolved').count()
    resolution_rate = (resolved_grievances / total_grievances * 100) if total_grievances > 0 else 0
    
    # Get department statistics
    department_stats = Department.objects.annotate(
        total=Count('department_grievances'),
        pending=Count('department_grievances', filter=Q(department_grievances__status__in=['new', 'in_progress'])),
        resolved=Count('department_grievances', filter=Q(department_grievances__status='resolved'))
    ).values('name', 'total', 'pending', 'resolved')
    
    # Calculate resolution rate for each department
    for dept in department_stats:
        dept['resolution_rate'] = (dept['resolved'] / dept['total'] * 100) if dept['total'] > 0 else 0
    
    # Get recent users
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    
    # Get recent grievances
    recent_grievances = Grievance.objects.select_related('department', 'submitted_by').order_by('-created_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_departments': total_departments,
        'total_grievances': total_grievances,
        'resolution_rate': round(resolution_rate, 1),
        'department_stats': department_stats,
        'recent_users': recent_users,
        'recent_grievances': recent_grievances,
    }
    
    return render(request, 'admin/dashboard.html', context)