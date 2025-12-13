# Push to GitHub - Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `dataplatform` (or your preferred name)
3. Description: "Data Platform Project - Complete ETL pipeline with real-time streaming"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

```powershell
# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/dataplatform.git

# Push to GitHub
git push -u origin main
```

## Alternative: Using SSH

If you have SSH keys set up:

```powershell
git remote add origin git@github.com:YOUR_USERNAME/dataplatform.git
git push -u origin main
```

## Quick Command (Copy and Replace YOUR_USERNAME)

```powershell
git remote add origin https://github.com/YOUR_USERNAME/dataplatform.git
git branch -M main
git push -u origin main
```

---

**Note**: You'll be prompted for your GitHub username and password (or personal access token).

