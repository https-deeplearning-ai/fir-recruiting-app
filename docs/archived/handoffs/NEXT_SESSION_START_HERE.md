# 🚀 START HERE - Next Session Quick Start

**Date:** November 7, 2025
**Time:** Ready for next session
**Status:** Code complete, needs testing + 1 more feature

---

## ⚡ Quick Start (5 Minutes)

### 1. Run Database Migration (REQUIRED)

**Open Supabase SQL Editor and run:**
```sql
ALTER TABLE search_sessions
ADD COLUMN IF NOT EXISTS employee_ids INTEGER[] DEFAULT ARRAY[]::INTEGER[],
ADD COLUMN IF NOT EXISTS profiles_offset INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_employee_ids INTEGER DEFAULT 0;
```

### 2. Start Backend
```bash
cd backend
python3 app.py
```

### 3. Start Frontend
```bash
cd frontend
npm start
```

---

## ✅ What's Already Done (Ready to Test)

### Feature 1: Skip Stage 1 for Pre-Selected Companies ✅
**What it does:** When you select companies from research and click "Search for People", it skips unnecessary AI validation.

**Expected logs:**
```
✅ USING 12 PRE-SELECTED COMPANIES (SKIPPING STAGE 1)
   Companies: ['Vena', 'webdew', 'INFUSE', ...]
   All have CoreSignal IDs: ✅
```

### Feature 2: Load 20 More (1000 Candidates) ✅
**What it does:** Enables loading up to 1000 candidates in batches of 20.

**Expected logs:**
```
🔍 Step 1: Searching for employee IDs (max: 1000)...
   ✅ Search successful: Found 847 employee IDs
   📊 Stored 847 employee IDs in session

📡 Step 2: Collecting first 20 profiles (with caching)...
   ✅ Collected 20 profiles
   📊 Cache stats: 0 cached, 20 fetched, 0 failed
```

### Feature 3: Anthropic Debug Logging ✅
**What it does:** Shows what's being validated and discovered `website` field for better lookup.

**Expected logs:**
```
🤖 [ANTHROPIC REQUEST] Validating: 'Vena' in the fintech industry
📨 [ANTHROPIC RESPONSE] Raw: {"company_name": "Vena", "website": "vena.io", ...
✅ [VALIDATION RESULT] Vena: valid=True, relevance=high
```

### Feature 4: Profile & Company Caching ✅
**What it does:** Saves 75%+ credits on repeated searches.

**Expected logs:**
```
   20/20: ID 12345678 - FROM CACHE ✓
✅ Batch complete: 20 profiles (15 cached, 5 fetched, 0 failed)
```

---

## 🎯 What Needs to Be Done (Next Session)

### Priority 1: Implement Website-Based Company Lookup (45 min)

**Current Problem:**
- Company lookup: 0% success rate
- Companies rejected as "not found"
- Wastes API credits on failed lookups

**Solution:**
Use the `website` field from Anthropic validation for exact matching.

**Implementation:**
See complete guide in: **`HANDOFF_DOMAIN_WEBSITE_LOOKUP.md`**

**Quick summary:**
1. Add `get_by_website()` method to `coresignal_company_lookup.py` (30 lines)
2. Update ID lookup to try website first (10 lines)
3. Show website in frontend UI (15 lines JSX)

**Expected Impact:**
- 0% → 70-90% success rate
- Faster, more reliable searches
- Reduced wasted API credits

---

## 📝 Testing Checklist

### Test 1: Pre-Selected Companies Flow (10 min)
1. ✅ Run database migration
2. Run company research
3. Select 5-10 companies
4. Click "Search for People"
5. **Check logs:** Should see "SKIPPING STAGE 1"
6. **Check result:** Employees should appear

### Test 2: Load 20 More (10 min)
1. After initial search completes (20 candidates shown)
2. Click "Load 20 More" button
3. **Check logs:** Should see cache stats
4. **Check result:** 20 new profiles appear
5. Repeat 3-5 times
6. **Verify:** Can load 100+ candidates total

### Test 3: Caching (5 min)
1. Complete a search
2. Refresh page and search again with same companies
3. **Check logs:** Should see "FROM CACHE" messages
4. **Verify:** Much faster second time

---

## 📂 File Status

### Uncommitted Changes (Test Before Committing)
```
backend/coresignal_service.py                          | +254 lines
backend/jd_analyzer/api/domain_search.py               | +90 lines
backend/jd_analyzer/company/company_validation_agent.py | +13 lines
backend/utils/search_session.py                        | +113 lines
backend/utils/supabase_storage.py                      | +15 lines
backend/coresignal_company_lookup.py                   | +56 lines
frontend/src/App.js                                    | +8 lines
```

**Total:** ~550 lines of new code

### Git Status
```bash
# Check what's changed:
git status

# Review changes:
git diff backend/jd_analyzer/api/domain_search.py

# When ready to commit (after testing):
# DON'T commit yet - test first!
```

---

## 🐛 Known Issues

### Issue 1: Company Lookup 0% Success
**Status:** Known issue, fix documented in `HANDOFF_DOMAIN_WEBSITE_LOOKUP.md`
**Impact:** Companies can still be searched by name, just less reliable
**Priority:** HIGH

### Issue 2: Database Migration Required
**Status:** Not yet run
**Impact:** BLOCKS all testing
**Priority:** CRITICAL - Do this first!

---

## 📚 Reference Documents

### Quick Reference
- **This file** - Quick start guide
- **HANDOFF_DOMAIN_WEBSITE_LOOKUP.md** - Website lookup implementation (45 min task)

### Detailed Reference
- **HANDOFF_SESSION_NOV_7_2025.md** - Complete session notes (2200 lines)
  - Part 1: Morning session fixes (8 fixes)
  - Part 2: System state & verification
  - Part 3: Afternoon session fixes (4 fixes)
  - Part 4: Search/collect pattern details
  - Testing commands and examples

---

## 💡 Pro Tips

### Tip 1: Check Logs First
Always check backend terminal for these indicators:
- ✅ "SKIPPING STAGE 1" = Pre-selected flow working
- ✅ "FROM CACHE" = Caching working
- ✅ "ANTHROPIC RESPONSE" = Validation working

### Tip 2: Database First
If you see errors like "column does not exist", you forgot the migration.

### Tip 3: Test Incrementally
1. Test pre-selected flow first
2. Then test load-more
3. Then test caching
4. Then implement website lookup

### Tip 4: Don't Commit Until Tested
All code is staged but not committed. Test thoroughly first!

---

## ⏱️ Estimated Timeline

**Before you start coding:**
- Database migration: 5 min
- Test pre-selected flow: 10 min
- Test load-more: 10 min
- Test caching: 5 min

**Subtotal:** 30 minutes of testing

**New development:**
- Implement website lookup: 45 min
- Test website lookup: 15 min
- Commit all code: 5 min

**Total Session Time:** ~95 minutes (1.5 hours)

---

## 🎯 Success Criteria

**You're done when:**
1. ✅ Database migration successful
2. ✅ "Search for People" shows employees (not "0 companies found")
3. ✅ "Load 20 More" works 5+ times
4. ✅ Cache stats show hits on second search
5. ✅ Website lookup gives 70%+ success rate
6. ✅ All changes committed to git

---

## 🆘 If Something Goes Wrong

### Error: "column employee_ids does not exist"
**Fix:** Run database migration (see step 1 above)

### Error: "No employees found" after clicking "Search for People"
**Check logs for:**
- "SKIPPING STAGE 1" - Should see this if companies pre-selected
- If you see "Stage 1 discovery" instead, something's wrong
- Check that companies have `coresignal_company_id` field

### Error: "Load 20 More" button disappears immediately
**Likely causes:**
- Session not found
- employee_ids not stored
- profiles_offset not tracking

**Debug:**
- Check Supabase `search_sessions` table
- Verify `employee_ids` column populated
- Check backend logs for session creation

---

## 📞 Quick Commands

```bash
# Check git status
git status

# See what changed
git diff --stat

# View specific file changes
git diff backend/jd_analyzer/api/domain_search.py

# Check backend logs
# Look in terminal where python3 app.py is running

# Check Supabase tables
# search_sessions - should have new columns
# stored_profiles - should fill up with cached profiles
# stored_companies - should fill up with cached companies
```

---

**Ready to start?** Run the database migration and start testing! 🚀

**Questions?** Check `HANDOFF_DOMAIN_WEBSITE_LOOKUP.md` for website lookup implementation.

**Need details?** Check `HANDOFF_SESSION_NOV_7_2025.md` for complete session notes.
