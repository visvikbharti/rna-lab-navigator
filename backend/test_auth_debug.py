from django.contrib.auth import get_user_model
from api.auth.models import User

# Check model configuration
User = get_user_model()
print(f"User model: {User}")
print(f"USERNAME_FIELD: {User.USERNAME_FIELD}")
print(f"REQUIRED_FIELDS: {User.REQUIRED_FIELDS}")

# Check if users exist
users = User.objects.all()
for user in users:
    print(f"\nUser: {user.username}")
    print(f"Email: {user.email}")
    print(f"Is active: {user.is_active}")
    print(f"Is locked: {user.is_locked}")
    print(f"Employee ID: {user.employee_id}")
    print(f"Password starts with: {user.password[:20]}...")

# Check authentication backend
from django.conf import settings
print(f"\nAUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")

# Test direct password check
user = User.objects.get(username='testuser')
from django.contrib.auth.hashers import check_password
print(f"\nPassword check for 'TestPassword123!': {check_password('TestPassword123!', user.password)}")