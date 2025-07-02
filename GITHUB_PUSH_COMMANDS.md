# GitHub Push Commands

After creating your GitHub repository, run these commands:

```bash
# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/rna-lab-navigator.git

# Verify remote was added
git remote -v

# Push current branch
git push -u origin fix-openai-api-v1

# Also push main branch for reference
git checkout main
git push -u origin main

# Switch back to our working branch
git checkout fix-openai-api-v1
```

## Alternative: Using GitHub CLI (if you have it installed)

```bash
# Create repo and push in one command
gh repo create rna-lab-navigator --private --source=. --remote=origin --push
```

## After pushing, your repository will be at:
https://github.com/YOUR_USERNAME/rna-lab-navigator