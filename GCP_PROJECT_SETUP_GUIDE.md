# Step-by-Step Guide: Creating Your First GCP Project

## Part 1: Create Google Cloud Account

### Step 1: Go to Google Cloud
1. Open your browser and go to: https://cloud.google.com
2. Click on **"Get started for free"** button
3. Sign in with your Google account (use your institutional email if possible)

### Step 2: Set up billing
1. Google gives you **$300 free credits** for 90 days
2. You'll need to add a credit/debit card (won't be charged during free trial)
3. Select your country as **India**
4. Fill in your details and card information

## Part 2: Create Your Project

### Step 3: Access Cloud Console
1. After signup, you'll be redirected to: https://console.cloud.google.com
2. You'll see a welcome screen

### Step 4: Create New Project
1. Click on the **project dropdown** at the top (might show "My First Project")
2. Click **"NEW PROJECT"** button
3. Fill in:
   - **Project name**: `rna-lab-navigator`
   - **Project ID**: Will be auto-generated (like `rna-lab-navigator-123456`)
   - **Organization**: Leave as "No organization" if not using institutional account
4. Click **"CREATE"**
5. Wait 30 seconds for project creation

### Step 5: Note Your Project ID
**IMPORTANT**: Copy your Project ID somewhere safe. It will look like:
- `rna-lab-navigator-123456` (with random numbers at the end)

## Part 3: Install gcloud CLI

### Step 6: Download gcloud
1. Go to: https://cloud.google.com/sdk/docs/install
2. Select your operating system:
   - **For macOS**: Download the `.tar.gz` file
   - **For Windows**: Download the installer `.exe`
   - **For Linux**: Use the apt/yum commands shown

### Step 7: Install gcloud (macOS)
```bash
# After downloading, in Terminal:
cd ~/Downloads
tar -xf google-cloud-cli-*.tar.gz
./google-cloud-sdk/install.sh

# Restart your terminal, then initialize:
gcloud init
```

### Step 8: Authenticate gcloud
When you run `gcloud init`:
1. It will open a browser window
2. Select your Google account
3. Click "Allow" to grant permissions
4. Go back to terminal
5. Select your project from the list (or enter the Project ID)
6. Choose region: Type `23` for `asia-south1-a` (Mumbai)

## Part 4: Deploy RNA Lab Navigator

### Step 9: Clone and Navigate
```bash
cd ~/Downloads  # or wherever you want
git clone https://github.com/visvikbharti/rna-lab-navigator.git
cd rna-lab-navigator
```

### Step 10: Run Setup Script
```bash
./gcp-setup.sh
```

When prompted:
1. **Enter your GCP Project ID**: Paste the ID you copied in Step 5
2. **Enter your preferred region**: Just press Enter (default: asia-south1)

The script will:
- Enable all required APIs (this takes 2-3 minutes)
- Create database (5-10 minutes)
- Create Redis instance (5-10 minutes)
- Deploy your backend
- Show you the final URL

### Step 11: Deploy Weaviate
```bash
./weaviate-gcp-setup.sh
```

When prompted:
1. **Choose option**: Type `1` (for Compute Engine)
2. **Enter zone**: Just press Enter (default: asia-south1-a)

### Step 12: Update Frontend
1. The setup script will show you a URL like:
   ```
   Cloud Run URL: https://rna-lab-backend-abc123-uc.a.run.app
   ```
2. Update your frontend:
   ```bash
   cd frontend
   echo "VITE_API_BASE_URL=https://rna-lab-backend-abc123-uc.a.run.app/api" > .env.production
   vercel --prod
   ```

## Part 5: Verify Everything Works

### Step 13: Test Your Backend
```bash
# Replace with your actual Cloud Run URL
curl https://rna-lab-backend-abc123-uc.a.run.app/health/
```

Should return: `{"status": "healthy"}`

### Step 14: Test Your Frontend
1. Go to your Vercel URL: https://rna-lab-navigator.vercel.app
2. Try logging in with:
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

### "Permission denied" error
```bash
# Make scripts executable
chmod +x gcp-setup.sh
chmod +x weaviate-gcp-setup.sh
```

### "gcloud: command not found"
- Make sure you restarted your terminal after installation
- Or run: `source ~/.bashrc` (Linux/macOS)

### "Billing account required"
- You must enable billing even with free credits
- Go to: https://console.cloud.google.com/billing
- Link your project to the billing account

### API not enabled errors
The script should enable all APIs automatically, but if you see errors:
1. Go to: https://console.cloud.google.com/apis/library
2. Search and enable:
   - Cloud Run API
   - Cloud SQL Admin API
   - Memorystore for Redis API
   - Secret Manager API

## Costs After Free Trial

After your $300 credits or 90 days:
- Monthly cost: ~₹7,000-8,500 ($85-105)
- You can set up budget alerts to monitor spending
- You can shut down services anytime to stop charges

## Next Steps

1. **Change admin password**: Log in and update the default password
2. **Add lab members**: Create accounts for your 21 team members
3. **Upload documents**: Start ingesting your lab's PDFs and theses
4. **Set up backups**: Configure automated backups in Cloud Console

## Support

- **GCP Issues**: https://cloud.google.com/support
- **Application Issues**: Create issue at https://github.com/visvikbharti/rna-lab-navigator/issues
- **Billing Questions**: Check https://console.cloud.google.com/billing