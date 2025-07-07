# PythonAnywhere Setup Guide for RNA Lab Navigator

## Critical Fix Required (As of July 7, 2025)

The login endpoint is returning a 500 error due to missing environment variables and database configuration. Follow these steps to fix it:

## 1. Database Configuration Fix ✅ (Already Fixed)

The database hostname has been corrected in `backend/rna_backend/settings_pythonanywhere.py`:
```python
'HOST': 'rnalab-postgres.postgres.pythonanywhere-services.com',  # Correct format
```

## 2. Set Environment Variables (Required Immediately)

Go to your PythonAnywhere dashboard → Web tab → Environment variables section and add:

```bash
# 1. Generate a new SECRET_KEY
# Run this in a PythonAnywhere console to generate one:
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 2. Add these variables in the Web tab:
SECRET_KEY = <paste the generated key here>
DB_PASSWORD = <your PostgreSQL password from Databases tab>
OPENAI_API_KEY = <your OpenAI API key>

# Optional but recommended:
DB_PORT = 5432
WEAVIATE_URL = <leave empty for now, uses simple search>
```

## 3. Push the Database Fix to PythonAnywhere

```bash
cd ~/rna-lab-navigator
git pull origin pythonanywhere-deploy
```

## 4. Run Database Migrations

```bash
cd ~/rna-lab-navigator/backend
source venv/bin/activate
python manage.py migrate --settings=rna_backend.settings_pythonanywhere
```

## 5. Create/Reset Admin User

```bash
python manage.py createsuperuser --settings=rna_backend.settings_pythonanywhere
# Username: admin
# Email: admin@rnalab.com
# Password: GODisone@1
```

## 6. Collect Static Files

```bash
python manage.py collectstatic --noinput --settings=rna_backend.settings_pythonanywhere
```

## 7. Reload the Web App

**Important**: After setting environment variables, you MUST reload the web app:
1. Go to PythonAnywhere dashboard
2. Web tab
3. Click the green "Reload" button

## 8. Test the Deployment

```bash
cd ~/rna-lab-navigator
python test_api_endpoints.py
```

## Expected Output After Fixes

```
✓ Backend accessible
✓ CORS headers present
✓ Correct origin allowed
✓ Login endpoint exists
✓ Login with credentials
✓ Access token received
✓ Refresh token received
✓ Authenticated request
✓ Query endpoint

Tests passed: 5/5
✓ All tests passed! System is ready for beta testing.
```

## Quick Debugging Commands

```bash
# Check if environment variables are set
cd ~/rna-lab-navigator
python debug_pythonanywhere.py

# Quick fix attempt (after setting env vars)
python fix_login_500.py

# View error logs
tail -f ~/rna-lab-navigator/backend/error.log

# Test database connection manually
python -c "
import psycopg2
conn = psycopg2.connect(
    host='rnalab-postgres.postgres.pythonanywhere-services.com',
    database='rnalab\$rna_lab_db',
    user='rnalab',
    password='YOUR_DB_PASSWORD_HERE'
)
print('Connection successful!')
conn.close()
"
```

## Current Status (July 7, 2025)

- ✅ CORS configuration fixed
- ✅ Database hostname corrected
- ❌ Environment variables need to be set
- ❌ Database migrations pending
- ❌ Admin user creation pending

## Next Steps After This Setup

1. Launch beta testing with 5 lab members
2. Monitor for any performance issues
3. Set up daily preprint ingestion
4. Implement user feedback from beta testing

## Support

If you encounter issues:
1. Check `~/rna-lab-navigator/backend/error.log`
2. Run `debug_pythonanywhere.py` for diagnostics
3. Contact Vishal Bharti or check the deployment status document