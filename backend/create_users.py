from api.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

# Delete existing users
User.objects.all().delete()
print('All users deleted')

# Create superuser properly
User = get_user_model()

# Create superuser
superuser = User.objects.create_superuser(
    username='admin',
    email='admin@rnalabnavigator.com',
    password='AdminPassword123!',
    employee_id='ADM001'
)
superuser.role = 'ADMIN'
superuser.save()
print('Superuser created!')

# Create regular user
user = User.objects.create_user(
    username='testuser',
    email='testuser@rnalabnavigator.com',
    password='TestPassword123!',
    employee_id='EMP001'
)
user.role = 'LAB_MEMBER'
user.save()
print('Regular user created!')

# Verify passwords
admin_pwd = 'AdminPassword123!'
test_pwd = 'TestPassword123!'
print(f'Admin password check: {check_password(admin_pwd, superuser.password)}')
print(f'Test user password check: {check_password(test_pwd, user.password)}')