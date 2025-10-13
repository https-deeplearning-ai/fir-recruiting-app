# ✅ Heroku Deployment Setup Complete!

Your LinkedIn Assessor app is now ready to be deployed to Heroku. Here's what was configured:

## 📦 Files Created/Modified

### New Configuration Files
1. **Procfile** - Tells Heroku to run your Flask app with gunicorn
2. **runtime.txt** - Specifies Python 3.11.9
3. **.gitignore** - Prevents sensitive files from being committed
4. **ENV_TEMPLATE.txt** - Template for environment variables
5. **deploy.sh** - Automated deployment script (optional but helpful!)

### Documentation Files
1. **DEPLOYMENT.md** - Complete deployment guide with troubleshooting
2. **README_DEPLOYMENT.md** - Quick reference and checklist

### Modified Files
1. **backend/requirements.txt** - Added `gunicorn==21.2.0` for production
2. **backend/app.py** - Updated to:
   - Serve React frontend from Flask
   - Read API keys from environment variables
   - Use PORT environment variable
   - Serve React app on all routes (except API routes)
3. **frontend/src/App.js** - Changed API URLs from `http://localhost:5001/...` to `/...`
4. **frontend/build/** - Rebuilt with production optimizations

## 🚀 Quick Start - Two Ways to Deploy

### Option 1: Automated Script (Easiest)
```bash
./deploy.sh
```

This script will:
- Check if Heroku CLI is installed
- Login to Heroku if needed
- Create a Heroku app
- Set up environment variables (will prompt you)
- Deploy your code
- Open your app in browser

### Option 2: Manual Deployment
```bash
# 1. Login to Heroku
heroku login

# 2. Create app
heroku create your-app-name

# 3. Set environment variables
heroku config:set ANTHROPIC_API_KEY=your_key_here
heroku config:set CORESIGNAL_API_KEY=your_key_here
heroku config:set SUPABASE_URL=your_url_here
heroku config:set SUPABASE_KEY=your_key_here

# 4. Deploy
git push heroku main

# 5. Scale and open
heroku ps:scale web=1
heroku open
```

## 🔑 Required Environment Variables

You'll need these API keys ready:

| Variable | Where to Get It |
|----------|----------------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| `CORESIGNAL_API_KEY` | CoreSignal dashboard |
| `SUPABASE_URL` | Supabase project settings |
| `SUPABASE_KEY` | Supabase project settings (anon/public key) |

## 🏗️ Application Architecture

```
Your Heroku App
├── Web Dyno (runs gunicorn)
│   └── Flask Backend (backend/app.py)
│       ├── API Endpoints (/fetch-profile, /assess-profile, etc.)
│       └── Static File Server (serves React app)
└── React Frontend (frontend/build/)
    └── Single Page Application
```

**How it works:**
1. User visits your Heroku URL
2. Heroku routes request to gunicorn
3. Gunicorn runs Flask
4. Flask serves React for web pages
5. React makes API calls to Flask endpoints (same domain, relative URLs)
6. Flask processes requests using Anthropic, CoreSignal, and Supabase APIs

## 📝 Pre-Deployment Checklist

- [ ] Heroku CLI installed (`brew install heroku/brew/heroku`)
- [ ] Logged in to Heroku (`heroku login`)
- [ ] All API keys ready
- [ ] Git repository initialized
- [ ] All changes committed

## 🎯 After Deployment

### Test Your App
1. Visit your Heroku URL
2. Test single profile assessment
3. Test batch processing
4. Test profile search
5. Check database save/load functionality

### Monitor Your App
```bash
heroku logs --tail        # View real-time logs
heroku ps                 # Check dyno status
heroku config             # View environment variables
```

### Common Post-Deployment Tasks
```bash
heroku restart            # Restart your app
heroku ps:scale web=1     # Ensure web dyno is running
heroku releases           # View deployment history
heroku rollback           # Rollback to previous version
```

## 💡 Important Notes

### Free Tier Limitations
- App sleeps after 30 minutes of inactivity
- First request after sleep takes ~10-30 seconds
- 550-1000 free dyno hours per month
- Consider upgrading for production use

### API Rate Limits
- Monitor your Anthropic API usage
- Monitor your CoreSignal API usage
- Consider implementing request queuing for high volume

### Security Best Practices
- ✅ API keys are in environment variables (not in code)
- ✅ `.env` files are gitignored
- ✅ Sensitive data is never committed to git
- 🔄 Rotate API keys periodically
- 📊 Monitor API usage regularly

## 🆘 Troubleshooting

### App won't start?
```bash
heroku logs --tail        # Check for errors
heroku config             # Verify env vars are set
heroku restart            # Try restarting
```

### Frontend not loading?
```bash
# Check if build folder exists
ls -la frontend/build/

# Rebuild if needed
cd frontend && npm run build && cd ..

# Deploy again
git add . && git commit -m "Rebuild frontend" && git push heroku main
```

### API errors?
```bash
# Test API keys locally first
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Keys loaded:', bool(os.getenv('ANTHROPIC_API_KEY')))"

# Check on Heroku
heroku config:get ANTHROPIC_API_KEY
```

## 📚 Documentation

- **DEPLOYMENT.md** - Comprehensive deployment guide
- **README_DEPLOYMENT.md** - Quick reference and tips
- **ENV_TEMPLATE.txt** - Environment variable template

## 🎉 You're Ready!

Everything is configured and ready to deploy. Choose your deployment method:

**Quick & Easy:** Run `./deploy.sh`

**Manual Control:** Follow steps in DEPLOYMENT.md

Either way, you'll have a fully functional LinkedIn Assessor app running on Heroku in minutes!

---

**Need help?** Check the troubleshooting section in DEPLOYMENT.md or review Heroku logs with `heroku logs --tail`

