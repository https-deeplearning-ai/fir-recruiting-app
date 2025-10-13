# Render Deployment Guide

## Overview
This guide will help you deploy the LinkedIn AI Assessor to Render, which provides better performance and no timeout limits compared to Heroku.

## Benefits of Render over Heroku
- ✅ **No 30-second timeout limits** - Can process large batches
- ✅ **Better performance** - Dedicated resources
- ✅ **Same pricing** - $7/month for Starter plan
- ✅ **Easier deployment** - Direct GitHub integration
- ✅ **Auto-scaling** - Handles traffic spikes

## Deployment Steps

### 1. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository

### 2. Create New Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository: `linkedin-assessor`
3. Use these settings:
   - **Name**: `linkedin-ai-assessor`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2`
   - **Plan**: Starter ($7/month)

### 3. Set Environment Variables
In Render dashboard, go to Environment tab and add:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `CORESIGNAL_API_KEY`: Your CoreSignal API key  
- `SUPABASE_URL`: Your Supabase URL
- `SUPABASE_KEY`: Your Supabase key

### 4. Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy
3. Your app will be available at: `https://linkedin-ai-assessor.onrender.com`

## Configuration Details

### Automatic Environment Detection
The app automatically detects if it's running on Render vs Heroku:

**On Render:**
- 50 concurrent API calls
- 60-second timeout
- 100 candidate batch size
- 2 workers for better performance

**On Heroku:**
- 15 concurrent API calls  
- 25-second timeout
- 50 candidate batch size
- 1 worker (conservative)

### Performance Comparison
- **Heroku**: 20 candidates in ~30 seconds (with timeout risk)
- **Render**: 50 candidates in ~30 seconds (no timeout risk)

## Migration from Heroku
1. Deploy to Render using steps above
2. Test with small batch (5-10 candidates)
3. Test with larger batch (20-50 candidates)
4. Update your domain/bookmarks to Render URL
5. Keep Heroku as backup until Render is fully tested

## Troubleshooting
- **Build fails**: Check Python version in requirements.txt
- **Environment variables**: Ensure all API keys are set
- **Timeout issues**: Render doesn't have the 30-second limit
- **Performance**: Render provides dedicated resources

## Support
- Render documentation: https://render.com/docs
- Render support: Available on paid plans
