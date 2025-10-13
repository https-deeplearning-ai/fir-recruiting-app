# Quick Deployment Checklist

## Before Deployment

- [ ] All API keys are ready (Anthropic, CoreSignal, Supabase)
- [ ] Frontend is built (`cd frontend && npm run build`)
- [ ] Git repository is initialized and committed
- [ ] Heroku CLI is installed and logged in

## Deployment Steps

```bash
# 1. Create Heroku app
heroku create your-app-name

# 2. Set environment variables
heroku config:set ANTHROPIC_API_KEY=your_key_here
heroku config:set CORESIGNAL_API_KEY=your_key_here
heroku config:set SUPABASE_URL=your_url_here
heroku config:set SUPABASE_KEY=your_key_here

# 3. Deploy
git push heroku main

# 4. Scale
heroku ps:scale web=1

# 5. Open
heroku open
```

## Post-Deployment

- [ ] Test all features in production
- [ ] Monitor logs with `heroku logs --tail`
- [ ] Set up custom domain (optional)
- [ ] Configure SSL (automatic on Heroku)

## Files Created for Deployment

1. **Procfile** - Tells Heroku how to run your app
2. **runtime.txt** - Specifies Python version
3. **requirements.txt** - Updated with `gunicorn`
4. **app.py** - Modified to serve React frontend
5. **.gitignore** - Prevents sensitive files from being committed

## Key Changes Made

### Backend (app.py)
- Added `send_from_directory` import
- Configured Flask to serve React build folder
- Added catch-all route to serve React app
- Made API keys read from environment variables
- Changed port to use `PORT` environment variable

### Frontend (src/App.js)
- Changed all API URLs from `http://localhost:5001/...` to `/...` (relative URLs)
- Rebuilt with `npm run build`

## Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| ANTHROPIC_API_KEY | Your Anthropic API key | sk-ant-... |
| CORESIGNAL_API_KEY | Your CoreSignal API key | zGZEUYUw... |
| SUPABASE_URL | Your Supabase project URL | https://xxx.supabase.co |
| SUPABASE_KEY | Your Supabase anon key | eyJhbGci... |

## Architecture

Your app structure on Heroku:
```
├── Procfile (tells Heroku to run gunicorn)
├── runtime.txt (Python 3.11.9)
├── backend/
│   ├── app.py (Flask backend + serves React)
│   ├── requirements.txt (Python dependencies)
│   └── ... (other backend files)
└── frontend/
    └── build/ (React production build)
```

When a request comes in:
1. Heroku routes traffic to gunicorn
2. Gunicorn runs Flask (app.py)
3. Flask serves React for web pages
4. Flask handles API endpoints for backend logic

## Local Testing Before Deployment

To test the production setup locally:

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Set environment variables (or create .env file)
export ANTHROPIC_API_KEY=your_key
export CORESIGNAL_API_KEY=your_key
export SUPABASE_URL=your_url
export SUPABASE_KEY=your_key

# Run with gunicorn
gunicorn --chdir backend app:app --bind 0.0.0.0:5001
```

Visit http://localhost:5001 to test.

## Troubleshooting

### App won't start
- Check `heroku logs --tail`
- Verify environment variables: `heroku config`
- Make sure all dependencies are in requirements.txt

### Frontend not showing
- Verify build folder exists: `ls frontend/build`
- Check Flask is serving correct static folder
- Clear browser cache

### API errors
- Check API keys are set correctly
- Verify API endpoints are working: `heroku logs --tail`
- Test individual endpoints with curl

### Database connection issues
- Verify Supabase credentials
- Check Supabase project is not paused
- Test connection locally first

## Useful Heroku Commands

```bash
heroku logs --tail              # View live logs
heroku restart                  # Restart your app
heroku ps                       # Check dyno status
heroku config                   # View environment variables
heroku run bash                 # Open shell on Heroku
heroku releases                 # View deployment history
heroku rollback                 # Rollback to previous version
```

## Support

If you encounter issues:
1. Check the detailed DEPLOYMENT.md guide
2. Review Heroku logs
3. Verify all environment variables
4. Test locally first
5. Check Heroku status: https://status.heroku.com/

