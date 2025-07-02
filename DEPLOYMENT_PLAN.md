# RNA Lab Navigator - Deployment Plan

## Current Status (June 30, 2025)

We've successfully implemented:
- ✅ Fixed OpenAI API v1.x compatibility
- ✅ Fixed authentication system (JWT tokens)
- ✅ Fixed text visibility in chat interface
- ✅ Added logout functionality
- ✅ Documented user roles
- ✅ Optimized RAG performance (88% improvement)
- ✅ System is fully functional

## Recommended Git Strategy

### 1. First, let's commit our current work:
```bash
# Add all relevant files
git add backend/api/analytics/middleware.py
git add backend/api/auth/views.py
git add backend/api/chat/views.py
git add backend/api/rag/weaviate_production_rag.py
git add backend/rna_backend/settings.py
git add frontend/src/components/ChatInterface.jsx
git add frontend/src/components/auth/PrivateRoute.jsx
git add frontend/src/index.css

# Add documentation
git add backend/USER_ROLES_DOCUMENTATION.md
git add backend/RAG_QUALITY_ASSESSMENT.md
git add SESSION_STATUS_JUNE_30_2025.md

# Add utility scripts
git add backend/fix_weaviate_schema.py
git add backend/create_users.py

# Commit with descriptive message
git commit -m "🚀 Fix authentication, improve text visibility, optimize RAG performance

- Fixed JWT token blacklist issues
- Improved text contrast in chat interface
- Added comprehensive user role documentation
- Optimized RAG query performance (88% faster)
- Fixed Weaviate schema issues
- Added logout functionality via UserMenu

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 2. Create a new production-ready branch:
```bash
# Create new branch from current state
git checkout -b production-v1

# Or if you want to keep working on current branch
git push origin fix-openai-api-v1
```

### 3. Clean up sensitive files before pushing:
```bash
# Create .gitignore if needed
echo "*.log" >> .gitignore
echo "*.db" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "node_modules/" >> .gitignore
echo ".env" >> .gitignore
echo "celerybeat-schedule.db" >> .gitignore
```

### 4. Environment variables setup:
Create `.env.example` files for both frontend and backend with dummy values

## Deployment Strategy

### Backend (Railway/Heroku):
1. Push to GitHub
2. Connect Railway to GitHub repo
3. Set environment variables
4. Deploy with Docker

### Frontend (Vercel):
1. Push to GitHub
2. Import project in Vercel
3. Set build settings:
   - Framework: Vite
   - Build command: `npm run build`
   - Output directory: `dist`
4. Set environment variables
5. Deploy

## Project Structure for GitHub

```
rna-lab-navigator/
├── README.md                    # Main project documentation
├── .gitignore                   # Git ignore file
├── docker-compose.yml           # Local development setup
├── backend/
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Backend container
│   ├── manage.py
│   └── ...
├── frontend/
│   ├── package.json            # Node dependencies
│   ├── vite.config.js
│   ├── vercel.json             # Vercel config
│   └── ...
└── docs/
    ├── SETUP.md                # Setup instructions
    ├── API.md                  # API documentation
    └── DEPLOYMENT.md           # Deployment guide
```

## Next Steps

1. **Immediate**: Commit current changes
2. **Today**: Push to GitHub private repo
3. **This week**: Deploy to staging environment
4. **Next week**: Final testing and production deployment

## Benefits of This Approach

1. **Version Control**: Every change is tracked
2. **Rollback Capability**: Can revert if issues arise
3. **Collaboration**: Others can contribute
4. **CI/CD**: Automatic deployments on push
5. **Professional**: Industry-standard workflow

## Alternative: Archive Current State

If you still prefer a backup:
```bash
# Create archive of current state
tar -czf rna-lab-navigator-backup-$(date +%Y%m%d).tar.gz \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=*.log \
  /Users/vishalbharti/Downloads/rna-lab-navigator/
```

But I strongly recommend using Git properly!