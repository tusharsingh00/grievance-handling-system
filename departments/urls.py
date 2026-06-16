from django.urls import path
from . import views

urlpatterns = [
    path('', views.department_dashboard, name='department-dashboard'),
    path('grievances/', views.department_grievance_list, name='department-grievance-list'),
    path('grievance/<int:pk>/update-status/', views.update_grievance_status, name='update-grievance-status'),
    # path('grievance/<int:grievance_id>/comment/', views.add_comment, name='add-comment'),


]