# Cambridge Statistics - Auto Deployment Setup

## Automatic Deployment is NOW ACTIVE! 🚀

Your site is configured for **automatic deployment** to cambridgestatistics.com. Here's how it works:

### Method 1: Automatic (Recommended)
Simply push any changes to GitHub and they'll automatically deploy:

```bash
git add .
git commit -m "Your change description"
git push
```

**Changes go live in ~2 minutes!**

### Method 2: Quick Deploy Script
Use the included script for even easier deployment:

```bash
./deploy.sh
```

This script will:
- ✅ Check for changes
- 📦 Stage all files
- 💾 Commit with timestamp
- 🚀 Push to GitHub (triggers auto-deploy)

### Method 3: Claude Code Integration
When working with Claude Code, any commits made will automatically trigger deployment.

## How It Works

1. **GitHub Repository**: https://github.com/karakotaram/cambridge-crime-map
2. **Netlify Hosting**: Connected to the GitHub repo
3. **Auto-Deploy**: Every push to `main` branch triggers deployment
4. **Live Site**: https://cambridgestatistics.com

## File Structure

- `*.html` - Website pages (auto-deploy on change)
- `*.py` - Data processing scripts (run these to regenerate HTML)
- `netlify.toml` - Deployment configuration
- `.github/workflows/` - GitHub Actions for validation

## Quick Commands

```bash
# Check status
git status

# Deploy changes
./deploy.sh

# Regenerate data (if needed)
python crimes_by_year.py
```

## Troubleshooting

- **Deploy failed?** Check GitHub Actions tab in the repository
- **Changes not showing?** Wait 2-3 minutes, then check cambridgestatistics.com
- **Need help?** The deployment logs are available in Netlify dashboard

---

🎉 **You're all set!** Any changes you make will now automatically deploy to production!