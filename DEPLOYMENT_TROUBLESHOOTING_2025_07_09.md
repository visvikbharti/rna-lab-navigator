# RNA Lab Navigator - Deployment Troubleshooting Guide
**Date: July 9, 2025**
**Author: Senior Full-Stack Developer Analysis**

## 🔍 Current Deployment Status

### Frontend (Vercel)
- **URL**: https://rna-lab-navigator.vercel.app/ (and various preview URLs)
- **Status**: ✅ Deployed
- **Branch**: `pythonanywhere-deploy`
- **Issues**: SPA routing fixed with vercel.json rewrites

### Backend (PythonAnywhere)
- **URL**: https://rnalab.pythonanywhere.com
- **Status**: ⚠️ Partially functional
- **Key Issues**:
  1. 500 error on login endpoint (missing environment variables)
  2. Database migrations may be pending
  3. CORS configuration needs reload after latest changes

## 🚨 Critical Issues Identified

### 1. **Backend Environment Variables Not Set**
The login endpoint returns 500 error because required environment variables are missing on PythonAnywhere:
- `SECRET_KEY` - Django secret key
- `DB_PASSWORD` - PostgreSQL password
- `OPENAI_API_KEY` - OpenAI API key

### 2. **Database Configuration**
- Database user is `super` not `rnalab` (per settings_pythonanywhere.py)
- Port is `14669` (not default 5432)
- Host is `rnalab-4669.postgres.pythonanywhere-services.com`

### 3. **ML Features Disabled**
Due to PythonAnywhere free tier limitations:
- Sentence transformers mocked out
- Redis cache disabled (using DummyCache)
- Celery running in eager mode (no background workers)
- Cross-encoder disabled
- Using simple search instead of vector search

### 4. **Recent Deployment History**
From git log analysis:
- Multiple attempts to fix deployment issues
- CORS whitelist updated for Vercel URLs
- Database configuration fixed multiple times
- WSGI configuration patched for missing dependencies

## 📋 Action Plan

### Phase 1: Fix Backend (PythonAnywhere) - **URGENT**

1. **Set Environment Variables** (PythonAnywhere Web Tab):
   ```bash
   SECRET_KEY = <generate new key>
   DB_PASSWORD = <your PostgreSQL password>
   OPENAI_API_KEY = <your OpenAI API key>
   DB_PORT = 14669
   ```

2. **Update Backend Code**:
   ```bash
   cd ~/rna-lab-navigator
   git pull origin pythonanywhere-deploy
   ```

3. **Run Database Migrations**:
   ```bash
   cd ~/rna-lab-navigator/backend
   source venv/bin/activate
   python manage.py migrate --settings=rna_backend.settings_pythonanywhere
   ```

4. **Create/Verify Admin User**:
   ```bash
   python manage.py createsuperuser --settings=rna_backend.settings_pythonanywhere
   # Username: admin
   # Password: GODisone@1
   ```

5. **Collect Static Files**:
   ```bash
   python manage.py collectstatic --noinput --settings=rna_backend.settings_pythonanywhere
   ```

6. **Reload Web App**:
   - Go to PythonAnywhere dashboard → Web tab → Click "Reload" button

### Phase 2: Verify Authentication Flow

1. **Test Login Endpoint**:
   ```bash
   curl -X POST https://rnalab.pythonanywhere.com/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "GODisone@1"}'
   ```

2. **Check Frontend-Backend Connection**:
   - Open https://rna-lab-navigator.vercel.app/
   - Open DevTools → Network tab
   - Attempt login
   - Verify tokens are stored in localStorage

### Phase 3: Test Core Features

1. **Document Upload**:
   - Test PDF upload functionality
   - Verify ingestion works without Redis/Celery

2. **Search/Query**:
   - Test simple search functionality
   - Verify RAG responses work without vector DB

3. **Admin Panel**:
   - Access https://rnalab.pythonanywhere.com/admin/
   - Verify all models are accessible

## 🔧 Configuration Files Reference

### Backend Files
- `backend/rna_backend/settings_pythonanywhere.py` - Main settings
- `backend/wsgi_complete_for_pythonanywhere.py` - WSGI config
- `backend/pythonanywhere_patches.py` - Dependency patches

### Frontend Files
- `frontend/.env.production` - Production environment variables
- `frontend/src/api/config.js` - API configuration
- `vercel.json` - Vercel deployment config

## 🚀 Quick Commands

### Backend Health Check
```bash
# On PythonAnywhere console
cd ~/rna-lab-navigator
python backend/manage.py check --settings=rna_backend.settings_pythonanywhere
```

### Frontend Local Test
```bash
# On local machine
cd frontend
VITE_API_URL=https://rnalab.pythonanywhere.com npm run dev
```

## 📊 Success Criteria

1. ✅ Login works without 500 error
2. ✅ Tokens stored in localStorage
3. ✅ Admin panel accessible
4. ✅ Document upload functional
5. ✅ Search returns results in <5 seconds
6. ✅ No CORS errors in console

## 🔮 Future Improvements

1. **Upgrade PythonAnywhere Plan** for:
   - Redis support
   - Background workers
   - More CPU seconds
   - WebSocket support

2. **Implement Monitoring**:
   - Sentry for error tracking
   - Performance monitoring
   - Usage analytics

3. **Security Hardening**:
   - Remove exposed keys from git history
   - Implement rate limiting
   - Add 2FA for admin users

4. **Performance Optimization**:
   - Implement caching strategy
   - Optimize database queries
   - Add CDN for static assets

## 🆘 Troubleshooting Tips

### If Login Still Fails:
1. Check PythonAnywhere error log: `~/rna-lab-navigator/backend/error.log`
2. Verify environment variables are set correctly
3. Ensure database connection works
4. Check CORS configuration matches frontend URL

### If Frontend Can't Connect:
1. Verify `VITE_API_URL` in Vercel environment variables
2. Check browser console for CORS errors
3. Ensure backend is reloaded after CORS changes
4. Test API directly with curl

### Common PythonAnywhere Issues:
- **CPU Seconds Exceeded**: Optimize queries, reduce API calls
- **Import Errors**: Check pythonanywhere_patches.py is loaded
- **Static Files 404**: Run collectstatic and reload

## 📝 Notes

- PythonAnywhere free tier has significant limitations
- ML features are mocked to work within constraints
- Simple search replaces vector search functionality
- Performance may be slower than local development

---

**Next Immediate Step**: Set environment variables on PythonAnywhere and reload the web app.