# Deployment Strategy Without Credit Card

## Option 1: CSIR-IGIB Infrastructure (Recommended) 🏛️

Since you're at a premier government research institute, leverage institutional resources:

### A. Contact IT Department
```
Subject: Request for hosting RNA Lab Navigator - Dr. Debojyoti Chakraborty's Lab

Dear IT Team,

We've developed an internal tool for our RNA biology lab (21 members) that needs hosting:
- Django web application for document search with AI
- PostgreSQL database for metadata
- Requires ~2GB RAM, 20GB storage
- Internal access only (no public internet exposure needed)

Can we get:
1. A VM or container on institute servers?
2. A subdomain like rna-lab.igib.res.in?
3. PostgreSQL database access?

This will help preserve institutional knowledge and accelerate research.

Regards,
[Your name]
```

### B. Use Institute's Static IP
If you have a workstation with static IP:
1. Deploy on your lab workstation
2. Use institute's firewall rules to allow access
3. Create DNS entry with IT's help

## Option 2: Free Tier Combination (Immediate Solution) 🚀

### Step 1: Deploy Backend on PythonAnywhere
```bash
# 1. Sign up at pythonanywhere.com (no card needed)
# 2. Create a new web app → Django → Python 3.9
# 3. In Bash console:
git clone https://github.com/visvikbharti/rna-lab-navigator.git
cd rna-lab-navigator/backend
pip install -r requirements.txt

# 4. Configure settings_pythonanywhere.py
```

### Step 2: Database on Aiven
```bash
# 1. Sign up at aiven.io (no card for trial)
# 2. Create PostgreSQL service (free trial)
# 3. Get connection string
```

### Step 3: Minimal Working Version
Create `backend/rna_backend/settings_free.py`:
```python
from .settings import *

# PythonAnywhere specific
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']

# Aiven PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'defaultdb',
        'USER': 'avnadmin',
        'PASSWORD': 'your-aiven-password',
        'HOST': 'your-db.aivencloud.com',
        'PORT': '26257',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Disable features that need more resources
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously
USE_WEAVIATE = False  # Use simple search instead
```

## Option 3: Academic Programs (Check Today!) 🎓

### GitHub Student/Researcher Benefits
Even if you're not a student, researchers often qualify:
1. Go to: https://education.github.com/benefits/offers
2. Apply with your @igib.res.in email
3. Get access to:
   - Heroku credits ($312)
   - DigitalOcean credits ($200)
   - Azure credits ($100)

### Google Cloud Research Credits
1. Visit: https://cloud.google.com/edu/researchers
2. Apply for research credits (up to $5,000)
3. Use institutional email
4. Mention "AI/ML for biological research"

### AWS Cloud Credit for Research
1. Visit: https://aws.amazon.com/government-education/research-and-technical-computing/cloud-credit-for-research/
2. Up to $20,000 in credits
3. Perfect for government research institutes

## Option 4: Clever Workarounds 💡

### A. Split Deployment
```
Frontend: Vercel (already done) ✓
Backend API: Deta Space (free, no card)
Database: Supabase (free tier)
File Storage: Cloudinary (free tier)
Vector DB: Pinecone (free tier)
```

### B. Development Tunnel (Temporary)
```bash
# Use Cloudflare Tunnel (no card needed)
# 1. Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64

# 2. Run tunnel
./cloudflared-linux-amd64 tunnel --url http://localhost:8000

# Gives you URL like: https://random-name.trycloudflare.com
```

### C. Peer-to-Peer Deployment
Use Holepunch/Hypercore protocol for P2P hosting (experimental but free)

## Option 5: Community Resources 🤝

### Research Computing Communities
1. **XSEDE** (US-based but international researchers can apply)
2. **EGI** (European Grid Infrastructure - open to collaborations)
3. **OSG** (Open Science Grid)

### Indian Specific
1. **National Knowledge Network (NKN)** - May provide hosting
2. **PARAM Supercomputing** - Sometimes offers web hosting
3. **C-DAC Resources** - For research projects

## Immediate Action Plan 📋

### This Week:
1. **Today**: Set up PythonAnywhere + free database
2. **Tomorrow**: Email IT department for institutional hosting
3. **Day 3**: Apply for researcher credits (Google/AWS)

### Simplified Demo Version:
```bash
# Quick demo for your PI
# Use SQLite + PythonAnywhere
# Disable Weaviate, use simple search
# Still fully functional for beta testing!
```

## My Recommendation 🎯

**Best Path Forward:**
1. **Immediate**: Deploy simplified version on PythonAnywhere (today)
2. **Short-term**: Get institutional hosting from IT (this week)
3. **Long-term**: Apply for research cloud credits (this month)

This gives you:
- Working demo TODAY for your lab
- Sustainable solution via institute
- Professional deployment via cloud credits

## Need Help?

I can guide you through:
1. Setting up PythonAnywhere (takes 30 minutes)
2. Writing email to IT department
3. Applying for research credits
4. Creating simplified settings.py

Which option would you like to pursue first?