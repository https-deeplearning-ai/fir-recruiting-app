# Quick Start Guide - Deep Research Feature

## 🚀 Get Started in 5 Minutes

### Step 1: Clone and Setup (2 min)

```bash
# Clone the repository
git clone [repository-url]
cd linkedin_profile_ai_assessor

# Install backend dependencies
cd backend
pip3 install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Step 2: Configure Environment (1 min)

Create `backend/.env` file:

```bash
# Required for deep research
ANTHROPIC_API_KEY=sk-ant-...      # Get from Anthropic Console
TAVILY_API_KEY=tvly-...           # Get from Tavily (free tier OK)
CORESIGNAL_API_KEY=...            # Get from CoreSignal
SUPABASE_URL=https://...          # Get from Supabase project
SUPABASE_KEY=eyJ...               # Get from Supabase project

# Optional
OPENAI_API_KEY=sk-...             # For GPT-5 fallback
```

### Step 3: Run the Application (2 min)

```bash
# Terminal 1 - Start backend
cd backend
python3 app.py
# Should see: "Running on http://127.0.0.1:5001"

# Terminal 2 - Start frontend
cd frontend
npm start
# Should open: http://localhost:3000
```

---

## 🎯 See Deep Research in Action

### Quick Test Flow

1. **Open browser:** http://localhost:3000
2. **Click:** "JD Analyzer" tab
3. **Paste this test JD:**

```
We're looking for a Senior Voice AI Engineer.

Requirements:
- 5+ years in voice AI or speech recognition
- Experience with ASR systems
- Python, PyTorch/TensorFlow
- Real-time audio processing

Nice to have:
- Experience at companies like Deepgram or AssemblyAI
- Knowledge of TTS systems
```

4. **Click:** "Extract Requirements & Generate Weights"
5. **Click:** "Start Research"
6. **Watch:** Companies get discovered and researched
7. **Note:** Backend collects deep data (not all shown in UI yet)

---

## 🔍 Understanding What You're Seeing

### Current UI Shows:
```
Deepgram                           9.5/10
Based on their voice AI products...
Software | 150 employees | Series B
```

### Backend Actually Collected:
- Website: deepgram.com
- Products: ["ASR API", "TTS", "Audio Intelligence"]
- Funding: $72M Series B
- Tech Stack: ["Python", "Rust", "CUDA"]
- Recent News: ["Launched Aura TTS", "Nova-2 model"]
- Research Quality: 85%

**The data is there - just not displayed yet!**

---

## 📂 Key Files to Know

### 1. Deep Research Core
**`backend/company_deep_research.py`**
- The brain of web search
- Uses Claude Agent SDK
- Line 46: `research_company()` - main function

### 2. Integration Point
**`backend/company_research_service.py`**
- Line 947: `_deep_research_companies()` - orchestrator
- Line 188: Where it's called in the flow

### 3. Frontend Display (Needs Work)
**`frontend/src/App.js`**
- Line 4299: Company card display
- This is where you add the new fields

### 4. Test Scripts
**`backend/test_deep_research_manual.py`**
- Run this to see what data we collect
- Shows full JSON output

---

## 🧪 Quick Backend Test

### Test Deep Research Directly

```bash
cd backend
python3 -c "
import asyncio
from company_deep_research import CompanyDeepResearch

async def test():
    researcher = CompanyDeepResearch()
    result = await researcher.research_company(
        'Deepgram',
        'voice AI',
        {'industry': 'AI/ML'}
    )
    print('Website:', result.get('website'))
    print('Products:', result.get('products'))
    print('Funding:', result.get('funding'))
    print('Quality:', result.get('research_quality'))

asyncio.run(test())
"
```

Expected output:
```
🔍 Deep researching Deepgram for voice AI...
✅ Research complete for Deepgram (quality: 85%)
Website: deepgram.com
Products: ['ASR API', 'TTS', 'Audio Intelligence']
Funding: {'stage': 'Series B', 'amount': '$72M'}
Quality: 0.85
```

---

## 🔧 Continue Development

### Your Mission: Display the Hidden Data

The backend is collecting amazing data that users can't see. Your job:

1. **Open:** `frontend/src/App.js:4299`
2. **Add:** Display for `company.web_research` fields
3. **Test:** Verify data shows up
4. **Polish:** Make it look good

### Quick Implementation (10 min)

Add this after line 4304 in App.js:

```jsx
{/* Quick hack to show deep research data */}
{company.web_research && (
  <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#f3f4f6', borderRadius: '4px' }}>
    <div>🌐 <a href={`https://${company.web_research.website}`} target="_blank">
      {company.web_research.website}
    </a></div>
    <div>🛠️ {company.web_research.products?.join(', ')}</div>
    <div>💰 {company.web_research.funding?.amount}</div>
    <div>📊 Research Quality: {(company.research_quality * 100).toFixed(0)}%</div>
  </div>
)}
```

---

## 📊 Check Your Progress

### Backend Working? ✅
```bash
curl -X POST http://localhost:5001/research-companies \
  -H "Content-Type: application/json" \
  -d '{
    "jd_data": {
      "title": "ML Engineer",
      "requirements": {"domain": "voice AI"}
    }
  }'
```

Should return: `{"success": true, "session_id": "..."}`

### Frontend Connected? ✅
1. Open Developer Tools (F12)
2. Go to Network tab
3. Click "Start Research"
4. Should see: POST to `/research-companies`

### Deep Research Running? ✅
Check backend console for:
```
🔍 Deep researching Deepgram for voice AI...
✅ Found CoreSignal company_id: 12345
👥 Found 5 sample employees
📊 Evaluation: Score=9.5, Category=direct_competitor
```

---

## 🐛 Common Issues

### "Import error: claude-agent-sdk"
```bash
pip install claude-agent-sdk==0.1.5
```

### "ANTHROPIC_API_KEY not found"
```bash
# Make sure .env file is in backend/ folder
cd backend
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### "No companies discovered"
- Check TAVILY_API_KEY is set
- Try with seed companies: ["Deepgram", "AssemblyAI"]

### "Frontend not showing data"
- Open console (F12)
- Check for JavaScript errors
- Verify `company.web_research` exists

---

## 📚 Learn More

### Understand the Architecture
Read: `IMPLEMENTATION_GUIDE.md`

### See Full Data Examples
Read: `DATA_EXAMPLES.md`

### Complete Frontend Integration
Read: `FRONTEND_INTEGRATION_TODO.md`

---

## 💡 Pro Tips

1. **Use the test scripts** - They show exactly what data is available
2. **Check the console** - Backend prints useful debug info
3. **Inspect network requests** - See actual API responses
4. **Start simple** - Just display website first, then add more

---

## 🎯 Success Checklist

After 1 hour, you should:
- [ ] Have the app running locally
- [ ] See companies being discovered
- [ ] Understand what deep research does
- [ ] Know where to add UI code
- [ ] Have displayed at least one new field

After 1 day, you should:
- [ ] Display all web_research fields
- [ ] Add quality indicators
- [ ] Implement expand/collapse
- [ ] Add export functionality
- [ ] Polish the UI

---

## 🚢 Ship It!

When you're done:
1. **Test:** Run through the full flow
2. **Commit:** Your changes
3. **Document:** What you added
4. **Deploy:** Follow existing deployment process

Welcome to the Deep Research feature - let's make that hidden data visible! 🚀