# Vercel Deployment Guide for RNA Lab Navigator

## Prerequisites
1. GitHub repository pushed (complete the GitHub push first)
2. Vercel account (free tier is fine)
3. Backend deployed (Railway/Heroku) - we'll do this after

## Step 1: Import Project in Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New..." → "Project"
3. Import Git Repository
4. Select your `rna-lab-navigator` repository
5. Select the `fix-openai-api-v1` branch

## Step 2: Configure Build Settings

Vercel should auto-detect Vite, but verify these settings:

- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

## Step 3: Set Environment Variables

Click on "Environment Variables" and add:

```
VITE_API_URL = https://your-backend-url.railway.app/api
```

(We'll update this after deploying the backend)

For now, you can use a placeholder or your local URL:
```
VITE_API_URL = http://localhost:8000/api
```

## Step 4: Deploy

1. Click "Deploy"
2. Wait for the build to complete (usually 1-2 minutes)
3. You'll get a URL like: `https://rna-lab-navigator-xyz.vercel.app`

## Step 5: Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

## Common Issues & Solutions

### Build Fails
- Check build logs for errors
- Ensure all dependencies are in package.json
- Verify Node version compatibility

### API Connection Issues
- Update VITE_API_URL to your deployed backend
- Check CORS settings in backend
- Ensure backend allows your Vercel domain

### 404 Errors on Routes
- vercel.json already configured for SPA routing
- All routes will redirect to index.html

## Post-Deployment Checklist

- [ ] Test login functionality
- [ ] Verify chat interface works
- [ ] Check text visibility (should be fixed)
- [ ] Test logout functionality
- [ ] Verify API calls are working
- [ ] Check console for any errors

## Environment Variables Reference

Production variables you'll need:
- `VITE_API_URL`: Your backend API URL
- `VITE_APP_NAME`: RNA Lab Navigator (already set)
- `VITE_ENV`: production (already set)

## Deployment URL Structure

Your app will be available at:
- Preview: `https://rna-lab-navigator-git-fix-openai-api-v1-YOUR_USERNAME.vercel.app`
- Production: `https://rna-lab-navigator.vercel.app`

## Next Steps

After frontend is deployed:
1. Deploy backend to Railway
2. Update VITE_API_URL with Railway URL
3. Redeploy on Vercel
4. Test complete system

---

Ready to deploy! 🚀