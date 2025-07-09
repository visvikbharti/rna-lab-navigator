# RNA Lab Navigator - Immediate Action Plan
**Date: July 9, 2025**
**Priority: URGENT - Backend is currently broken**

## 🚨 CRITICAL ISSUE
The backend login endpoint returns 500 error because environment variables are not set on PythonAnywhere.

## 📋 STEP-BY-STEP FIXES (Do in Order)

### Step 1: Generate Django Secret Key (5 min)
```bash
# Run this locally or in any Python environment
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```
Save the output - you'll need it in Step 2.

### Step 2: Set PythonAnywhere Environment Variables (10 min)
1. Log into PythonAnywhere
2. Go to "Web" tab
3. Scroll to "Environment variables" section
4. Add these variables:
   ```
   SECRET_KEY = [paste generated key from Step 1]
   DB_PASSWORD = [your PostgreSQL password from Databases tab]
   OPENAI_API_KEY = sk-proj-[your actual OpenAI key]
   DB_PORT = 14669
   ```
5. Click "Save"

### Step 3: Update Backend Code (5 min)
Open PythonAnywhere Bash console and run:
```bash
cd ~/rna-lab-navigator
git pull origin pythonanywhere-deploy
```

### Step 4: Install/Update Dependencies (5 min)
```bash
cd ~/rna-lab-navigator/backend
source venv/bin/activate
pip install -r requirements_pythonanywhere.txt
```

### Step 5: Run Database Migrations (5 min)
```bash
python manage.py migrate --settings=rna_backend.settings_pythonanywhere
```

### Step 6: Create Admin User (2 min)
```bash
python manage.py shell --settings=rna_backend.settings_pythonanywhere
```
Then in the Python shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@rnalab.com', 'GODisone@1')
    print("Admin user created")
else:
    print("Admin user already exists")
exit()
```

### Step 7: Collect Static Files (3 min)
```bash
python manage.py collectstatic --noinput --settings=rna_backend.settings_pythonanywhere
```

### Step 8: Reload Web App (1 min)
1. Go back to PythonAnywhere "Web" tab
2. Click the big green "Reload" button
3. Wait for reload to complete

### Step 9: Test Login Endpoint (2 min)
```bash
# In PythonAnywhere console
curl -X POST https://rnalab.pythonanywhere.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "GODisone@1"}'
```

Expected response should include:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {...}
}
```

### Step 10: Test Frontend Login (2 min)
1. Open https://rna-lab-navigator.vercel.app/
2. Open browser DevTools (F12) → Network tab
3. Try logging in with:
   - Username: admin
   - Password: GODisone@1
4. Check localStorage for tokens

## ✅ Success Checklist
- [ ] No 500 error on login
- [ ] Tokens received from backend
- [ ] Tokens stored in localStorage
- [ ] Can access admin panel at https://rnalab.pythonanywhere.com/admin/
- [ ] No CORS errors in browser console

## 🆘 If Something Goes Wrong

### Check Error Logs
```bash
# In PythonAnywhere console
tail -n 50 ~/rna-lab-navigator/backend/error.log
tail -n 50 /var/log/rnalab.pythonanywhere.com.error.log
```

### Debug Environment Variables
```bash
cd ~/rna-lab-navigator
python -c "
import os
print('SECRET_KEY set:', bool(os.environ.get('SECRET_KEY')))
print('DB_PASSWORD set:', bool(os.environ.get('DB_PASSWORD')))
print('OPENAI_API_KEY set:', bool(os.environ.get('OPENAI_API_KEY')))
"
```

### Test Database Connection
```bash
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='rnalab-4669.postgres.pythonanywhere-services.com',
        database='rnalab\$rna_lab_db',
        user='super',
        password=os.environ.get('DB_PASSWORD'),
        port='14669'
    )
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print('❌ Database connection failed:', e)
"
```

## 🎯 Expected Timeline
Total time: ~35 minutes
- Environment setup: 15 min
- Backend updates: 10 min
- Testing: 10 min

## 📞 Need Help?
1. Check PythonAnywhere forums
2. Review error logs
3. Ensure all environment variables are set correctly
4. Verify database credentials from Databases tab

---

**START WITH STEP 1 NOW** - The system is currently broken and needs these fixes immediately.