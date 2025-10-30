# JD Analyzer Integration Guide

Step-by-step guide for integrating the JD Analyzer module into the frontend to auto-populate weighted assessment criteria from job descriptions.

---

## Overview

The JD Analyzer module allows users to:
1. Paste a job description
2. Auto-extract weighted assessment criteria
3. Review and edit suggested requirements
4. Use those weights for candidate evaluation

This eliminates manual rubric creation and ensures consistency across assessments.

---

## Backend Setup

### 1. Register API Routes

Add to `backend/app.py` (after line 43):

```python
# Import JD analyzer routes
from jd_analyzer.api_endpoints import register_jd_analyzer_routes

# Register routes (after CORS setup)
register_jd_analyzer_routes(app)
```

### 2. Test API Endpoints

```bash
# Start backend
cd backend
python3 app.py

# Test JD parsing (in another terminal)
curl -X POST http://localhost:5001/api/jd/parse \
  -H "Content-Type: application/json" \
  -d '{"jd_text": "Senior ML Engineer with 5+ years..."}'

# Test weight generation
curl -X POST http://localhost:5001/api/jd/generate-weights \
  -H "Content-Type: application/json" \
  -d '{
    "jd_text": "Senior ML Engineer...",
    "num_requirements": 5
  }'

# Test full analysis
curl -X POST http://localhost:5001/api/jd/full-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "jd_text": "Senior ML Engineer...",
    "num_requirements": 5
  }'
```

---

## Frontend Integration

### Step 1: Add JD Input Section to UI

Add a new section in `frontend/src/App.js` for JD analysis:

```javascript
// Add state variables (in App component)
const [jdText, setJDText] = useState('');
const [jdAnalyzing, setJDAnalyzing] = useState(false);
const [jdAnalysisResult, setJDAnalysisResult] = useState(null);

// Add JD analysis function
const analyzeJD = async () => {
  if (!jdText.trim()) {
    alert('Please paste a job description');
    return;
  }

  setJDAnalyzing(true);
  setJDAnalysisResult(null);

  try {
    const response = await fetch('http://localhost:5001/api/jd/full-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jd_text: jdText,
        num_requirements: 5
      })
    });

    const data = await response.json();

    if (data.success) {
      setJDAnalysisResult(data);

      // Auto-populate requirement fields
      const newRequirements = data.weighted_requirements.map((req, index) => ({
        id: index + 1,
        text: req.requirement,
        weight: req.weight,
        description: req.description,
        scoring_criteria: req.scoring_criteria
      }));

      setRequirements(newRequirements);
      alert('Requirements auto-populated from JD! Review and adjust as needed.');
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (error) {
    console.error('Error analyzing JD:', error);
    alert('Failed to analyze job description');
  } finally {
    setJDAnalyzing(false);
  }
};
```

### Step 2: Add UI Component

Add this section **before** the requirement input fields:

```javascript
{/* JD Analyzer Section */}
<div className="jd-analyzer-section" style={{
  marginBottom: '30px',
  padding: '20px',
  border: '2px dashed #ccc',
  borderRadius: '8px',
  backgroundColor: '#f9f9f9'
}}>
  <h3>✨ Auto-Generate Requirements from Job Description</h3>
  <p style={{ fontSize: '14px', color: '#666' }}>
    Paste a job description below and we'll automatically extract weighted assessment criteria.
  </p>

  <textarea
    value={jdText}
    onChange={(e) => setJDText(e.target.value)}
    placeholder="Paste full job description here..."
    rows="10"
    style={{
      width: '100%',
      padding: '12px',
      fontSize: '14px',
      fontFamily: 'monospace',
      border: '1px solid #ccc',
      borderRadius: '4px',
      marginBottom: '10px'
    }}
  />

  <button
    onClick={analyzeJD}
    disabled={jdAnalyzing || !jdText.trim()}
    style={{
      padding: '12px 24px',
      backgroundColor: jdAnalyzing ? '#ccc' : '#6200ea',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      cursor: jdAnalyzing ? 'not-allowed' : 'pointer',
      fontSize: '16px',
      fontWeight: 'bold'
    }}
  >
    {jdAnalyzing ? 'Analyzing...' : '🤖 Analyze & Auto-Fill'}
  </button>

  {jdAnalysisResult && (
    <div style={{
      marginTop: '20px',
      padding: '15px',
      backgroundColor: '#e8f5e9',
      borderRadius: '4px',
      border: '1px solid #4caf50'
    }}>
      <h4 style={{ color: '#2e7d32', marginBottom: '10px' }}>
        ✓ Analysis Complete
      </h4>
      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
        <strong>Role:</strong> {jdAnalysisResult.requirements.role_title}
      </p>
      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
        <strong>Seniority:</strong> {jdAnalysisResult.requirements.seniority_level}
      </p>
      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
        <strong>Location:</strong> {jdAnalysisResult.requirements.location}
      </p>
      <p style={{ fontSize: '14px', marginBottom: '10px' }}>
        <strong>Generated {jdAnalysisResult.weighted_requirements.length} requirements</strong> with a total weight of {100 - jdAnalysisResult.general_fit_weight}% (General Fit: {jdAnalysisResult.general_fit_weight}%)
      </p>
      <details style={{ fontSize: '13px' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
          View Keywords Extracted
        </summary>
        <div style={{ marginTop: '10px', paddingLeft: '15px' }}>
          {jdAnalysisResult.keywords.map((keyword, i) => (
            <span key={i} style={{
              display: 'inline-block',
              padding: '4px 8px',
              margin: '4px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              {keyword}
            </span>
          ))}
        </div>
      </details>
    </div>
  )}
</div>
```

### Step 3: Update Requirement Input Fields

Modify the requirement input section to show auto-populated values:

```javascript
{requirements.map((req, index) => (
  <div key={req.id} className="requirement-input">
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <span style={{ fontWeight: 'bold', minWidth: '30px' }}>
        {index + 1}.
      </span>

      <input
        type="text"
        value={req.text}
        onChange={(e) => {
          const newReqs = [...requirements];
          newReqs[index].text = e.target.value;
          setRequirements(newReqs);
        }}
        placeholder={`Requirement ${index + 1}`}
        style={{
          flex: 1,
          padding: '10px',
          fontSize: '14px',
          border: '1px solid #ccc',
          borderRadius: '4px'
        }}
      />

      <input
        type="number"
        value={req.weight}
        onChange={(e) => {
          const newReqs = [...requirements];
          newReqs[index].weight = parseInt(e.target.value) || 0;
          setRequirements(newReqs);
        }}
        placeholder="%"
        min="0"
        max="100"
        style={{
          width: '70px',
          padding: '10px',
          fontSize: '14px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          textAlign: 'center'
        }}
      />
      <span style={{ fontSize: '14px' }}>%</span>
    </div>

    {/* Show description if auto-populated */}
    {req.description && (
      <div style={{
        marginTop: '8px',
        marginLeft: '40px',
        fontSize: '13px',
        color: '#666',
        fontStyle: 'italic'
      }}>
        {req.description}
      </div>
    )}

    {/* Show scoring criteria if auto-populated */}
    {req.scoring_criteria && (
      <details style={{ marginTop: '5px', marginLeft: '40px' }}>
        <summary style={{
          fontSize: '12px',
          color: '#888',
          cursor: 'pointer'
        }}>
          Scoring Criteria
        </summary>
        <div style={{
          marginTop: '5px',
          fontSize: '12px',
          color: '#666',
          paddingLeft: '15px'
        }}>
          {req.scoring_criteria}
        </div>
      </details>
    )}
  </div>
))}
```

---

## CSS Styling

Add to `frontend/src/App.css`:

```css
/* JD Analyzer Section */
.jd-analyzer-section {
  animation: fadeIn 0.3s ease-in;
}

.jd-analyzer-section h3 {
  margin-top: 0;
  color: #6200ea;
  font-size: 20px;
}

.jd-analyzer-section textarea {
  resize: vertical;
  min-height: 150px;
}

.jd-analyzer-section textarea:focus {
  outline: none;
  border-color: #6200ea;
  box-shadow: 0 0 0 2px rgba(98, 0, 234, 0.1);
}

.jd-analyzer-section button:hover:not(:disabled) {
  background-color: #4a00b8;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(98, 0, 234, 0.3);
}

.jd-analyzer-section button:active:not(:disabled) {
  transform: translateY(0);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## User Flow

### 1. User Pastes Job Description

```
┌─────────────────────────────────────────┐
│ ✨ Auto-Generate Requirements from JD   │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ Senior ML Engineer with 5+ years... │ │
│ │                                     │ │
│ │ Must-have:                          │ │
│ │ - Voice AI / real-time systems     │ │
│ │ - LLM fine-tuning experience       │ │
│ │ - Python, PyTorch, TensorFlow      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [🤖 Analyze & Auto-Fill]                │
└─────────────────────────────────────────┘
```

### 2. System Analyzes (3-5 seconds)

```
┌─────────────────────────────────────────┐
│ [Analyzing...]                          │
│                                         │
│ ⏳ Extracting requirements...           │
│ ⏳ Generating weighted criteria...      │
│ ⏳ Extracting keywords...               │
└─────────────────────────────────────────┘
```

### 3. Results Auto-Populate

```
┌─────────────────────────────────────────┐
│ ✓ Analysis Complete                     │
│                                         │
│ Role: Senior ML Engineer                │
│ Seniority: senior                       │
│ Location: San Francisco Bay Area        │
│ Generated 5 requirements (90% total)    │
│                                         │
│ [View Keywords Extracted ▼]             │
└─────────────────────────────────────────┘

Requirements (Auto-Populated):
┌────────────────────────────────────────┐
│ 1. Voice AI / Real-time Systems (35%) │
│    Deep experience building voice AI   │
│    [Scoring Criteria ▼]                │
├────────────────────────────────────────┤
│ 2. LLM / ML Infrastructure (25%)      │
│    Strong ML infrastructure background │
│    [Scoring Criteria ▼]                │
├────────────────────────────────────────┤
│ 3. Product Leadership 0→1 (20%)       │
│    Experience taking products 0→1      │
│    [Scoring Criteria ▼]                │
└────────────────────────────────────────┘
```

### 4. User Reviews & Edits

User can:
- Edit requirement names
- Adjust weights
- Remove requirements
- Add new requirements
- Edit scoring criteria

### 5. Assess Candidates

Use the auto-populated requirements to evaluate candidates with weighted scoring.

---

## Advanced Features (Optional)

### Feature 1: Save JD Analysis

```javascript
// Save JD analysis for later reference
const saveJDAnalysis = () => {
  localStorage.setItem('jd_analysis', JSON.stringify({
    jd_text: jdText,
    requirements: jdAnalysisResult.requirements,
    weighted_requirements: jdAnalysisResult.weighted_requirements,
    timestamp: new Date().toISOString()
  }));
  alert('JD analysis saved!');
};

// Load saved JD
const loadSavedJD = () => {
  const saved = localStorage.getItem('jd_analysis');
  if (saved) {
    const data = JSON.parse(saved);
    setJDText(data.jd_text);
    setJDAnalysisResult({
      requirements: data.requirements,
      weighted_requirements: data.weighted_requirements
    });
  }
};
```

### Feature 2: Compare Multiple JDs

```javascript
// Compare requirements from different JDs
const compareJDs = async (jd1, jd2) => {
  const [analysis1, analysis2] = await Promise.all([
    analyzeJDRequest(jd1),
    analyzeJDRequest(jd2)
  ]);

  // Show side-by-side comparison
  setComparisonView({
    jd1: analysis1,
    jd2: analysis2,
    differences: calculateDifferences(analysis1, analysis2)
  });
};
```

### Feature 3: Export Requirements to CSV

```javascript
// Export weighted requirements
const exportRequirements = () => {
  const csv = [
    ['Requirement', 'Weight', 'Description', 'Scoring Criteria'],
    ...requirements.map(req => [
      req.text,
      `${req.weight}%`,
      req.description || '',
      req.scoring_criteria || ''
    ])
  ].map(row => row.join(',')).join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'weighted_requirements.csv';
  a.click();
};
```

---

## Testing

### Test Cases

**1. Basic JD Parsing**
```
Input: "Senior ML Engineer with 5+ years experience in NLP..."
Expected: Extract role, seniority, skills, experience years
```

**2. Weight Generation**
```
Input: JD with must-have + nice-to-have sections
Expected: 5 requirements with weights summing to 90-95%
```

**3. Empty JD Handling**
```
Input: ""
Expected: Error message "No job description provided"
```

**4. Invalid Weight Total**
```
Input: User edits weights to sum >100%
Expected: Warning message "Weights exceed 100%"
```

**5. Very Long JD (10k+ words)**
```
Input: Extremely long JD text
Expected: Graceful handling, possibly truncation
```

### Manual Test Script

```bash
# 1. Start backend
cd backend && python3 app.py

# 2. Start frontend
cd frontend && npm start

# 3. Test flow:
#    - Paste JD in textarea
#    - Click "Analyze & Auto-Fill"
#    - Wait 3-5 seconds
#    - Verify requirements appear
#    - Edit weights
#    - Verify total updates
#    - Submit for assessment
```

---

## Troubleshooting

### Issue: "API call failed"
**Solution:** Check backend is running on port 5001, verify ANTHROPIC_API_KEY is set

### Issue: "Weights don't sum to 100%"
**Solution:** This is expected - General Fit auto-calculates remaining percentage

### Issue: "Analysis takes too long (>10 seconds)"
**Solution:** Claude API may be slow, consider showing progress indicator

### Issue: "Auto-populated requirements don't match JD"
**Solution:** Review prompt in `jd_parser.py`, adjust system prompt for better extraction

---

## Production Deployment

### Environment Variables

```bash
# .env file
ANTHROPIC_API_KEY=your_key_here
```

### Build Frontend

```bash
cd frontend
npm run build
cp -r build/. ../backend/
```

### Deploy to Render

Already configured in `render.yaml` - just push to main branch:

```bash
git add .
git commit -m "feat: Add JD Analyzer for auto-generating assessment criteria"
git push origin main
```

---

## Future Enhancements

- [ ] Multi-language support (translate JDs)
- [ ] JD template library (pre-saved JDs for common roles)
- [ ] A/B testing of different weight configurations
- [ ] Integration with ATS systems (import JDs from Lever, Greenhouse)
- [ ] Candidate-to-JD similarity scoring
- [ ] Auto-suggest company filters based on JD domain

---

## Related Documentation

- [JD Analyzer README](../backend/jd_analyzer/README.md)
- [Reverse-Engineering Case Study](reverse-engineering/README.md)
- [CLAUDE.md](../CLAUDE.md)
