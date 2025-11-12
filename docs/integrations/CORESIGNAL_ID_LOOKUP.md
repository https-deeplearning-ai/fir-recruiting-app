# UI Feature: Retroactive CoreSignal ID Lookup

**Purpose:** Allow users to add CoreSignal IDs to old research sessions that were created before the ID lookup integration.

**Use Case:** User has 20 old research sessions from last month. They want to look up employee data for those companies now, but the sessions don't have CoreSignal company IDs.

---

## 🎯 Feature Design

### UI Location
**Option 1:** Session Management Page (Recommended)
- Show list of all past research sessions
- Flag sessions missing `01_company_ids.json`
- "Add Company IDs" button for each session

**Option 2:** Inline Button in Research Results
- At bottom of company research results
- "Refresh Company IDs" button
- Useful for re-running ID lookup with improved strategy

---

## 🖼️ UI Mockup

### Session List View
```
┌─────────────────────────────────────────────────────────────┐
│ Past Research Sessions                                       │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 🔍 Voice AI Companies - Nov 7, 2025                      ││
│ │ 📊 96 companies discovered                               ││
│ │ ⚠️  Company IDs: Missing                                ││
│ │ [Add Company IDs] [View Results]                        ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 🔍 Fintech Payment Companies - Nov 10, 2025             ││
│ │ 📊 100 companies discovered                              ││
│ │ ✅ Company IDs: 85/100 (85%)                            ││
│ │ [View Results]                                          ││
│ └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### ID Lookup Progress Modal
```
┌─────────────────────────────────────────────────────────────┐
│ Adding Company IDs to Session                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 🔍 Looking up CoreSignal IDs...                             │
│                                                              │
│ ████████████████░░░░░░░░░░  60/96 companies (62%)           │
│                                                              │
│ Recent:                                                      │
│ ✅ Deepgram: ID=6761084 (Tier 1 - Website)                  │
│ ✅ Krisp: ID=21473726 (Tier 2 - Name Exact)                 │
│ ❌ Google Cloud Speech: No match found                      │
│                                                              │
│ Estimated time: 2 minutes                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Completion Summary
```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Company IDs Added Successfully!                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 📊 Results:                                                  │
│   • Searchable: 82/96 companies (85%)                       │
│   • Not found: 14 companies                                  │
│   • Credits used: 0                                          │
│                                                              │
│ 🎯 Tier Breakdown:                                           │
│   • Tier 1 (Website): 45 companies                          │
│   • Tier 2 (Name): 30 companies                             │
│   • Tier 3 (Fuzzy): 7 companies                             │
│   • Tier 4 (Fallback): 0 companies                          │
│                                                              │
│ 💾 Saved to: logs/domain_search_sessions/.../01_company_... │
│                                                              │
│ [View Updated Results] [Search Employees]                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend API Endpoint

### POST /api/sessions/{session_id}/add-company-ids

**Request:**
```json
{
  "session_id": "sess_20251108_030844_b4bf34c2",
  "force_overwrite": false
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "sess_20251108_030844_b4bf34c2",
  "results": {
    "total_companies": 96,
    "with_ids": 82,
    "without_ids": 14,
    "coverage_percent": 85.4,
    "tier_breakdown": {
      "tier_1": 45,
      "tier_2": 30,
      "tier_3": 7,
      "tier_4": 0
    }
  },
  "credits_used": 0,
  "file_created": "logs/domain_search_sessions/.../01_company_ids.json"
}
```

---

## 💻 Frontend Implementation

### React Component: `SessionManager.js`

```jsx
import React, { useState } from 'react';

function SessionManager() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  async function fetchSessions() {
    const response = await fetch('/api/sessions');
    const data = await response.json();
    setSessions(data.sessions);
  }

  async function addCompanyIds(sessionId) {
    setLoading(sessionId);

    try {
      const response = await fetch(`/api/sessions/${sessionId}/add-company-ids`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });

      const result = await response.json();

      if (result.success) {
        // Show success notification
        alert(`✅ Added IDs to ${result.results.with_ids}/${result.results.total_companies} companies`);

        // Refresh session list
        fetchSessions();
      }
    } catch (error) {
      console.error('Failed to add company IDs:', error);
      alert('❌ Failed to add company IDs');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="session-manager">
      <h2>Past Research Sessions</h2>

      {sessions.map(session => (
        <div key={session.id} className="session-card">
          <h3>{session.title}</h3>
          <p>{session.company_count} companies</p>

          {!session.has_company_ids && (
            <button
              onClick={() => addCompanyIds(session.id)}
              disabled={loading === session.id}
            >
              {loading === session.id ? 'Adding IDs...' : 'Add Company IDs'}
            </button>
          )}

          {session.has_company_ids && (
            <span className="badge">✅ {session.id_coverage}% with IDs</span>
          )}
        </div>
      ))}
    </div>
  );
}

export default SessionManager;
```

---

## 🔄 Backend Implementation

### Flask Route: `app.py`

```python
@app.route('/api/sessions/<session_id>/add-company-ids', methods=['POST'])
def add_company_ids_to_session(session_id):
    """
    Retroactively add CoreSignal IDs to an old session.

    This allows users to look up company IDs for sessions created
    before the ID lookup integration was implemented.
    """
    try:
        data = request.get_json()
        force_overwrite = data.get('force_overwrite', False)

        # Find session directory
        base_dir = Path(__file__).parent / "logs" / "domain_search_sessions"
        session_dir = base_dir / session_id

        if not session_dir.exists():
            return jsonify({'error': 'Session not found'}), 404

        # Check if already has IDs
        ids_file = session_dir / "01_company_ids.json"
        if ids_file.exists() and not force_overwrite:
            with open(ids_file, 'r') as f:
                existing_data = json.load(f)
                return jsonify({
                    'success': True,
                    'message': 'Session already has company IDs',
                    'results': existing_data.get('coverage', {})
                })

        # Load companies from session
        companies = load_session_companies(session_dir)

        if not companies:
            return jsonify({'error': 'No company data found in session'}), 400

        # Look up IDs using four-tier strategy
        lookup = CoreSignalCompanyLookup()

        companies_with_ids = []
        companies_without_ids = []
        tier_stats = {1: 0, 2: 0, 3: 0, 4: 0}

        for company in companies:
            company_name = company.get('name', company.get('company_name', ''))
            website = company.get('website')

            if not company_name:
                companies_without_ids.append(company)
                continue

            # Use four-tier lookup
            match = lookup.lookup_with_fallback(
                company_name=company_name,
                website=website,
                confidence_threshold=0.75,
                use_company_clean_fallback=True
            )

            if match:
                company['coresignal_company_id'] = match['company_id']
                company['coresignal_confidence'] = match.get('confidence', 1.0)
                company['coresignal_searchable'] = True
                company['lookup_tier'] = match.get('tier', 0)

                tier = match.get('tier', 0)
                if tier in tier_stats:
                    tier_stats[tier] += 1

                companies_with_ids.append(company)
            else:
                company['coresignal_searchable'] = False
                companies_without_ids.append(company)

        # Calculate coverage
        total = len(companies)
        coverage_percent = (len(companies_with_ids) / total * 100) if total else 0

        # Save to file
        output_data = {
            "stage": "retroactive_company_id_lookup",
            "original_session_id": session_id,
            "searchable_companies": companies_with_ids,
            "non_searchable_companies": companies_without_ids,
            "coverage": {
                "with_ids": len(companies_with_ids),
                "without_ids": len(companies_without_ids),
                "percentage": round(coverage_percent, 1)
            },
            "tier_breakdown": tier_stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        with open(ids_file, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'results': {
                'total_companies': total,
                'with_ids': len(companies_with_ids),
                'without_ids': len(companies_without_ids),
                'coverage_percent': round(coverage_percent, 1),
                'tier_breakdown': tier_stats
            },
            'credits_used': 0,
            'file_created': str(ids_file.relative_to(Path.cwd()))
        })

    except Exception as e:
        print(f"Error adding company IDs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
```

---

## 📊 Benefits

1. **No Data Loss** - Old sessions can be enriched with IDs
2. **Zero Credits** - Uses free `/preview` endpoints
3. **Fast** - ~1-2 seconds per company
4. **Non-Destructive** - Creates new file, preserves original session data
5. **Progress Tracking** - Real-time progress updates
6. **Re-runnable** - Can re-run with improved lookup strategies

---

## 🚀 Implementation Priority

**Phase 1: CLI Script** ✅ DONE
- `backend/retroactive_id_lookup.py`
- Run manually on sessions

**Phase 2: API Endpoint** (Recommended)
- Flask route: `/api/sessions/{session_id}/add-company-ids`
- Can be called from frontend or scripts

**Phase 3: UI Feature** (Future)
- Session management page
- Progress modals
- Batch re-processing

---

## 💡 Future Enhancements

1. **Batch Retroactive Lookup**
   - "Add IDs to All Sessions" button
   - Process multiple sessions at once

2. **Scheduled Background Jobs**
   - Automatically add IDs to new sessions
   - Cron job or task queue

3. **ID Refresh**
   - Re-run lookup on existing sessions
   - Update with improved strategy

4. **Confidence Threshold UI**
   - Let users adjust fuzzy match threshold
   - Trade-off: higher coverage vs. accuracy
