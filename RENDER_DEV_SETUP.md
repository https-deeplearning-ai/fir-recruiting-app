# Render Dev Environment Setup Guide

**Purpose:** Create a separate free dev environment on Render to test the Chrome extension integration without affecting production.

---

## 🎯 What We're Setting Up

- **Production:** `https://linkedin-ai-assessor-ffhz.onrender.com` (main branch) - KEEP AS IS
- **Dev:** `https://linkedin-ai-assessor-dev.onrender.com` (dev/enhancements branch) - NEW

---

## 📋 Step-by-Step Setup

### Step 1: Create New Web Service on Render

1. **Go to Render Dashboard:** https://dashboard.render.com
2. **Click "New +"** (top right) → **"Web Service"**
3. **Connect Repository:**
   - If not already connected: Click "Connect account" → GitHub
   - Select repository: `yi031/linkedin_profile_ai_assessor`
   - Click "Connect"

### Step 2: Configure the Dev Service

**Basic Configuration:**
- **Name:** `linkedin-ai-assessor-dev` (or any name you prefer)
- **Region:** Same as production (e.g., Ohio)
- **Branch:** `dev/enhancements` ⭐ **IMPORTANT: Select this branch!**
- **Root Directory:** Leave blank
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`

**Plan:**
- Select **"Free"** plan (for testing)
- Note: Free tier sleeps after 15 min of inactivity

### Step 3: Add Environment Variables

**CRITICAL:** Click "Advanced" → "Add Environment Variable" and add these 4 variables:

```bash
# 1. Anthropic API Key
Key: ANTHROPIC_API_KEY
Value: [Your Anthropic API key - same as production]

# 2. CoreSignal API Key
Key: CORESIGNAL_API_KEY
Value: [Your CoreSignal API key - same as production]

# 3. Supabase URL
Key: SUPABASE_URL
Value: [Your Supabase project URL - same as production]

# 4. Supabase Key
Key: SUPABASE_KEY
Value: [Your Supabase anon/service key - same as production]
```

**Where to find these values:**
- Go to your production service: `linkedin-ai-assessor-ffhz`
- Click "Environment" tab
- Copy the values from there

**Optional (auto-detected):**
- `RENDER=true` is set automatically by Render

### Step 4: Create the Service

1. Click **"Create Web Service"** at the bottom
2. Render will start building and deploying
3. **Wait for deployment** (~2-3 minutes)
4. Status should change to "Live" (green)

### Step 5: Get Your Dev URL

Once deployed, you'll see:
- **URL:** `https://linkedin-ai-assessor-dev.onrender.com` (or similar)
- **Copy this URL** - you'll need it for extension configuration

---

## 🧪 Verify Dev Environment is Working

### Test 1: Basic Health Check

Open in browser:
```
https://linkedin-ai-assessor-dev.onrender.com/
```

**Expected:** React frontend loads (your web app)

### Test 2: Extension Auth Endpoint

Open in browser:
```
https://linkedin-ai-assessor-dev.onrender.com/extension/auth
```

**Expected:**
```json
{
  "authenticated": true,
  "message": "Extension API ready"
}
```

**If you see this:** ✅ Dev environment is working!

### Test 3: Check Render Logs

1. Go to Render Dashboard → `linkedin-ai-assessor-dev`
2. Click "Logs" tab
3. Should see:
```
 * Running on http://0.0.0.0:10000
 * Debugger is active!
```

---

## 🗄️ Database Setup (Supabase)

**IMPORTANT:** You're using the **same Supabase database** for both dev and production.

### Run Migrations (If Not Already Done)

1. **Go to Supabase:** https://supabase.com/dashboard
2. **Select your project**
3. **Click "SQL Editor"**

**Run First Migration:**
```sql
-- Copy entire contents of: backend/migrations/add_enhancement_tables.sql
-- Paste here and click "Run"
```

**Run Second Migration:**
```sql
-- Copy entire contents of: backend/migrations/add_assessment_fields.sql
-- Paste here and click "Run"
```

**Verify tables exist:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'recruiter_lists',
    'extension_profiles',
    'recruiter_exports'
  );

-- Should return 3 rows
```

---

## 🔌 Configure Chrome Extension for Dev

### Option A: Use Extension Settings Page

1. **Open extension popup**
2. **Click "Settings"**
3. **Update Backend URL:**
   - Change from: `https://linkedin-ai-assessor-ffhz.onrender.com`
   - To: `https://linkedin-ai-assessor-dev.onrender.com`
4. **Click "Save Settings"**

### Option B: Manually Edit Extension Code (for quick switching)

**File:** `chrome-extension/options/options.js`

Add a dev mode toggle or environment selector (optional enhancement).

---

## 🧪 Test Dev Environment

### Quick Test (5 minutes)

1. **Load extension** with dev backend URL configured
2. **Go to LinkedIn profile:** https://www.linkedin.com/in/satyanadella
3. **Click extension icon**
4. **Create list:** "Dev Test List"
5. **Add profile** to list

**Check Render Dev Logs:**
```
POST /extension/create-list
POST /extension/add-profile
Status: 200
```

**Check Supabase:**
```sql
SELECT * FROM recruiter_lists WHERE list_name = 'Dev Test List';
-- Should show the list you created
```

**If this works:** ✅ Dev environment is fully functional!

---

## 🔄 Switching Between Dev and Prod

### Method 1: Extension Settings

**For Dev:**
- Extension Settings → Backend URL: `https://linkedin-ai-assessor-dev.onrender.com`

**For Prod:**
- Extension Settings → Backend URL: `https://linkedin-ai-assessor-ffhz.onrender.com`

### Method 2: Load Two Versions of Extension

1. **Copy extension folder:**
```bash
cp -r chrome-extension chrome-extension-dev
```

2. **Edit `chrome-extension-dev/options/options.js`:**
   - Set default backend URL to dev environment

3. **Load both in Chrome:**
   - One pointing to dev, one to prod
   - Use different names/icons to distinguish

---

## 🚀 Deploy Updates to Dev

**Automatic Deployment (recommended):**
1. Make changes to `dev/enhancements` branch
2. Commit and push to GitHub:
```bash
git add .
git commit -m "Your changes"
git push origin dev/enhancements
```
3. Render auto-deploys dev environment
4. Wait ~2-3 minutes for deployment
5. Test changes

**Manual Deployment:**
1. Go to Render Dashboard → `linkedin-ai-assessor-dev`
2. Click "Manual Deploy" → "Deploy latest commit"

---

## 📊 Dev vs Prod Comparison

| Aspect | Production | Dev |
|--------|-----------|-----|
| **URL** | `linkedin-ai-assessor-ffhz.onrender.com` | `linkedin-ai-assessor-dev.onrender.com` |
| **Branch** | `main` | `dev/enhancements` |
| **Database** | Shared Supabase (same database) | Shared Supabase (same database) |
| **Plan** | Paid (always on) | Free (sleeps after 15 min) |
| **Purpose** | Live users | Testing new features |
| **Auto-deploy** | On push to `main` | On push to `dev/enhancements` |

---

## ⚠️ Important Notes

### Shared Database

**Both dev and prod use the same Supabase database.** This means:
- ✅ Easy to test with real data
- ⚠️ **Be careful not to break production data**
- 💡 Use distinct list names for testing (e.g., "DEV - Test List")

### Separating Dev Data (Optional)

If you want completely separate data:

**Option 1: Create a test Supabase project**
- Create new Supabase project for dev
- Update dev environment `SUPABASE_URL` and `SUPABASE_KEY`
- Run migrations on test project

**Option 2: Use table prefixes**
- Add `dev_` prefix to dev data
- Requires code changes to filter by prefix

**For now:** Using the same database is fine for testing.

### Free Tier Limitations

Render free tier:
- ✅ Sleeps after 15 minutes of inactivity
- ✅ First request after sleep takes 30-60 seconds (cold start)
- ✅ 750 hours/month free (plenty for testing)
- ✅ Auto-deploy on push

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Dev service shows "Live" (green) status on Render
- [ ] Opening dev URL shows React frontend
- [ ] `/extension/auth` endpoint returns `{"authenticated": true}`
- [ ] All 4 environment variables are set
- [ ] Database migrations have been run (3 new tables exist)
- [ ] Extension can connect to dev backend
- [ ] Can create lists and add profiles
- [ ] Data appears in Supabase tables

---

## 🆘 Troubleshooting

### Service won't start

**Check Render logs for errors:**
- Missing environment variables
- Build command failed
- Start command syntax error

**Fix:** Update environment variables or commands in Render settings.

### Extension can't connect to dev

**Check:**
- Dev service is "Live" (not deploying or sleeping)
- Extension settings have correct dev URL (no typos)
- No CORS errors in browser console

**Fix:** Wait for deployment to complete, or wake up sleeping service.

### "Table does not exist" errors

**Migrations not run.**

**Fix:** Run both migration SQL files in Supabase SQL Editor.

---

## 🎯 Next Steps After Setup

1. ✅ Test basic connectivity (create list, add profile)
2. ✅ Test batch assessment with 2-3 profiles
3. ✅ Test CSV export
4. ✅ Verify complete workflow works
5. ✅ If all tests pass → Merge to main and deploy to production

---

**Ready to create the dev environment?** Follow the steps above, then use the dev URL to test the Chrome extension integration!
