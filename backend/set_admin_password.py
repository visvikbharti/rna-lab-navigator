"""
Set admin password for the superuser.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rna_backend.settings')
django.setup()

from api.auth.models import User

# Get the admin user
admin = User.objects.get(username='admin')

# Set additional fields
admin.set_password('Admin@123456')  # Strong password meeting complexity requirements
admin.employee_id = 'IGIB-2025-0001'
admin.department = 'IT/Administration'
admin.designation = 'System Administrator'
admin.role = 'ADMIN'
admin.first_name = 'System'
admin.last_name = 'Administrator'
admin.save()

print(f"Admin password set successfully!")
print(f"Username: admin")
print(f"Password: Admin@123456")
print(f"Employee ID: {admin.employee_id}")
print(f"Role: {admin.role}")