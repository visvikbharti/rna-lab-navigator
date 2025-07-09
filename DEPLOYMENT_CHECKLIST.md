# RNA Lab Navigator Deployment Checklist - PythonAnywhere & Vercel

## Pre-Deployment Verification ✅

### Backend (PythonAnywhere) 
- [x] Database configured: `rnalab$rna_lab_db`
- [x] Settings file: `settings_pythonanywhere.py`
- [x] CORS configured for Vercel URLs
- [x] Static files configured with WhiteNoise
- [x] Environment variables set (OPENAI_API_KEY, DB_PASSWORD, etc.)
- [x] Admin user created (admin / GODisone@1)
- [x] API endpoints accessible at https://rnalab.pythonanywhere.com/api/

### Frontend (Vercel) Configuration
- [x] Branch: `pythonanywhere-deploy`
- [x] Root Directory: `frontend`
- [x] Framework: Vite
- [x] Build Command: `npm run build`
- [x] Output Directory: `dist`
- [x] Environment Variable: `VITE_API_URL=https://rnalab.pythonanywhere.com`

### Critical Fixes Applied ✅
- [x] Token naming standardized to `access_token` / `refresh_token`
- [x] API base URL configuration fixed (removed hardcoded localhost)
- [x] Import error fixed (ActivityIcon → ClockIcon)
- [x] CORS configuration added to backend
- [x] API endpoints updated to include `/api` prefix

### API Endpoint Verification
- Login: `POST https://rnalab.pythonanywhere.com/api/auth/login/`
- Refresh: `POST https://rnalab.pythonanywhere.com/api/auth/refresh/`
- Profile: `GET https://rnalab.pythonanywhere.com/api/auth/profile/`
- Documents: `GET https://rnalab.pythonanywhere.com/api/documents/`
- Query: `POST https://rnalab.pythonanywhere.com/api/query/`

## Deployment Steps 🚀

### 1. Commit Changes
```bash
git add -A
git commit -m "Fix critical deployment issues - token naming, CORS, API config"
git push origin pythonanywhere-deploy
```

### 2. Update PythonAnywhere
1. SSH to PythonAnywhere or use web console
2. Navigate to project: `cd ~/rna-lab-navigator`
3. Pull latest changes: `git pull origin pythonanywhere-deploy`
4. If settings changed, reload web app from PythonAnywhere dashboard

### 3. Deploy to Vercel (Fresh Project)
1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select `visvikbharti/rna-lab-navigator`
4. Configure Import Settings:
   ```
   Root Directory: frontend
   Framework Preset: Vite
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```
5. BEFORE clicking Deploy:
   - Click "Environment Variables"
   - Add:
     - Name: `VITE_API_URL`
     - Value: `https://rnalab.pythonanywhere.com`
     - Environments: All (Production, Preview, Development)
6. Under Git configuration:
   - Production Branch: `pythonanywhere-deploy`
   - Automatically deploy: ✓
7. Click "Deploy"

## Post-Deployment Testing 🧪

### 1. Frontend Accessibility
- [ ] Visit https://rna-lab-navigator.vercel.app
- [ ] Check console for errors (F12)
- [ ] Verify API calls go to correct backend URL

### 2. Authentication Flow
- [ ] Login with admin / GODisone@1
- [ ] Check tokens in localStorage (access_token, refresh_token)
- [ ] Verify token refresh works (wait for expiry or force refresh)
- [ ] Test logout functionality

### 3. Core Features
- [ ] Document upload (if enabled)
- [ ] Search/Query functionality
- [ ] User management (admin panel)
- [ ] Audit logs visibility

### 4. CORS Verification
- [ ] No CORS errors in browser console
- [ ] Preflight OPTIONS requests succeed
- [ ] Credentials included in requests

## Common Issues & Solutions 🔧

### Issue: "Login failed" error
**Check:**
1. Browser Console → Network tab → Check login request URL
2. Should be: `https://rnalab.pythonanywhere.com/api/auth/login/`
3. Check response status and error message

**Fix:**
- Ensure VITE_API_URL doesn't include `/api` suffix
- Verify CORS is configured on backend
- Check token naming consistency

### Issue: CORS errors
**Check:**
1. Browser console for CORS error messages
2. OPTIONS preflight request in Network tab

**Fix:**
- Update CORS_ALLOWED_ORIGINS in settings_pythonanywhere.py
- Ensure frontend URL is in the list
- Reload PythonAnywhere web app

### Issue: 404 Not Found on API calls
**Check:**
1. Network tab for exact URL being called
2. Verify `/api` prefix is included

**Fix:**
- Check AuthContext.jsx and api/client.js for correct paths
- Ensure all API calls include `/api` prefix

### Issue: Tokens not persisting
**Check:**
1. localStorage in browser DevTools
2. Look for `access_token` and `refresh_token`

**Fix:**
- Ensure consistent token naming across all files
- Check api/client.js and AuthContext.jsx use same names

## Environment-Specific Notes 📝

### PythonAnywhere Limitations
- Free tier: 100 CPU seconds/day
- No background tasks (Celery disabled)
- No WebSockets
- Database: 512MB limit
- Bandwidth: 10GB/month

### Vercel Limitations
- Free tier: 100GB bandwidth/month
- Serverless functions: 10 second timeout
- Build time: 45 minutes max

## Success Criteria ✓
- [ ] Users can login successfully
- [ ] API responses return within 5 seconds
- [ ] No console errors in production
- [ ] All core features functional
- [ ] CORS working properly
- [ ] Tokens persist across page refreshes

## Quick Health Checks
```bash
# Backend API
curl https://rnalab.pythonanywhere.com/api/health/

# Frontend
curl https://rna-lab-navigator.vercel.app/

# Test login endpoint
curl -X POST https://rnalab.pythonanywhere.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"GODisone@1"}'
```

## Final Notes
- Both services auto-sleep when inactive (cold start delays)
- First request after inactivity may be slow
- Monitor PythonAnywhere CPU seconds usage
- Check Vercel bandwidth usage monthly

---

**Ready for Production! 🎉**

Once all checks pass, your RNA Lab Navigator is ready for your 21 lab members to use!