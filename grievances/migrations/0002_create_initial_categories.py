from django.db import migrations

def create_initial_categories(apps, schema_editor):
    Category = apps.get_model('grievances', 'Category')
    Department = apps.get_model('departments', 'Department')
    
    # Define choices directly in the migration
    CATEGORY_CHOICES = {
        'technical': 'Technical Support',
        'hr': 'HR Related Issues',
        'facility': 'Facility Management',
        'security': 'Security Issues',
        'academic': 'Academic Matters',
        'financial': 'Financial Concerns',
        'general': 'General Inquiries'
    }
    
    # Create departments and their categories
    departments_data = {
        'IT Department': ['technical'],
        'HR Department': ['hr'],
        'Facility Management': ['facility'],
        'Security Department': ['security'],
        'Academic Affairs': ['academic'],
        'Finance Department': ['financial'],
        'General Administration': ['general']
    }
    
    for dept_name, categories in departments_data.items():
        dept, _ = Department.objects.get_or_create(name=dept_name)
        for category_name in categories:
            Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': CATEGORY_CHOICES[category_name],
                    'department': dept
                }
            )

def reverse_func(apps, schema_editor):
    Category = apps.get_model('grievances', 'Category')
    Category.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('grievances', '0001_initial'),
        ('departments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_categories, reverse_func),
    ]