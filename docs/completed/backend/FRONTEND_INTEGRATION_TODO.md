# Frontend Integration TODO

## 📍 Current State

**Location:** `frontend/src/App.js`
**Lines:** 4299-4310 (Company card display)
**Status:** Basic display only - missing deep research data

---

## ✅ Task List

### Priority 1: Display Core Deep Research Data

#### Task 1.1: Add Website Link
**Location:** After line 4303 (score badge)

```jsx
{/* Add website link */}
{company.web_research && company.web_research.website && (
  <div className="company-website">
    <a
      href={`https://${company.web_research.website}`}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        color: '#7c3aed',
        textDecoration: 'none',
        fontSize: '14px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        marginTop: '8px'
      }}
    >
      <span>🌐</span>
      {company.web_research.website}
    </a>
  </div>
)}
```

#### Task 1.2: Add Products Display
**Location:** After reasoning (line 4304)

```jsx
{/* Display products */}
{company.web_research && company.web_research.products && (
  <div className="company-products" style={{ marginTop: '12px' }}>
    <strong style={{ fontSize: '12px', color: '#6b7280' }}>Products:</strong>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
      {company.web_research.products.slice(0, 3).map((product, idx) => (
        <span
          key={idx}
          style={{
            padding: '2px 8px',
            backgroundColor: '#f3f4f6',
            borderRadius: '4px',
            fontSize: '12px'
          }}
        >
          {product}
        </span>
      ))}
    </div>
  </div>
)}
```

#### Task 1.3: Add Funding Information
**Location:** After products section

```jsx
{/* Display funding */}
{company.web_research && company.web_research.funding && (
  <div className="company-funding" style={{ marginTop: '8px' }}>
    <span style={{ fontSize: '13px' }}>
      💰 <strong>{company.web_research.funding.amount}</strong>
      {' '}({company.web_research.funding.stage})
      {company.web_research.funding.date && ` - ${company.web_research.funding.date}`}
    </span>
  </div>
)}
```

---

### Priority 2: Add Quality Indicators

#### Task 2.1: Research Quality Bar
**Location:** After company meta (line 4309)

```jsx
{/* Research Quality Indicator */}
{company.research_quality !== undefined && (
  <div className="research-quality" style={{ marginTop: '12px' }}>
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '12px',
      marginBottom: '4px'
    }}>
      <span style={{ color: '#6b7280' }}>Research Quality</span>
      <span style={{ fontWeight: '600' }}>
        {(company.research_quality * 100).toFixed(0)}%
      </span>
    </div>
    <div style={{
      width: '100%',
      height: '6px',
      backgroundColor: '#e5e7eb',
      borderRadius: '3px',
      overflow: 'hidden'
    }}>
      <div style={{
        width: `${company.research_quality * 100}%`,
        height: '100%',
        background: company.research_quality > 0.7
          ? 'linear-gradient(to right, #10b981, #34d399)'  // Green for high quality
          : company.research_quality > 0.4
          ? 'linear-gradient(to right, #f59e0b, #fbbf24)'  // Yellow for medium
          : 'linear-gradient(to right, #ef4444, #f87171)',  // Red for low
        transition: 'width 0.3s ease'
      }} />
    </div>
  </div>
)}
```

#### Task 2.2: CoreSignal Validation Badge
**Location:** Next to company name (line 4301)

```jsx
<div className="company-header">
  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
    <h5>{company.company_name}</h5>
    {company.coresignal_id && (
      <span style={{
        padding: '2px 6px',
        backgroundColor: '#dcfce7',
        color: '#166534',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: '500'
      }}>
        ✓ Verified
      </span>
    )}
  </div>
  <span className="score-badge">{company.relevance_score}/10</span>
</div>
```

---

### Priority 3: Add Expandable Details

#### Task 3.1: Add State for Expanded Companies
**Location:** Add after line 96 (state declarations)

```jsx
const [expandedCompanies, setExpandedCompanies] = useState({});
```

#### Task 3.2: Add Expand/Collapse Button
**Location:** After research quality section

```jsx
{/* Expand/Collapse for more details */}
{company.web_research && (
  <button
    onClick={() => setExpandedCompanies({
      ...expandedCompanies,
      [company.company_name]: !expandedCompanies[company.company_name]
    })}
    style={{
      marginTop: '12px',
      padding: '6px 12px',
      backgroundColor: 'transparent',
      border: '1px solid #e5e7eb',
      borderRadius: '4px',
      fontSize: '13px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '4px'
    }}
  >
    <span>{expandedCompanies[company.company_name] ? '▼' : '▶'}</span>
    {expandedCompanies[company.company_name] ? 'Show Less' : 'Show More'}
  </button>
)}
```

#### Task 3.3: Add Expanded Content
**Location:** After expand button

```jsx
{/* Expanded Details */}
{expandedCompanies[company.company_name] && company.web_research && (
  <div style={{
    marginTop: '12px',
    padding: '12px',
    backgroundColor: '#f9fafb',
    borderRadius: '6px',
    fontSize: '13px'
  }}>
    {/* Recent News */}
    {company.web_research.recent_news && company.web_research.recent_news.length > 0 && (
      <div style={{ marginBottom: '12px' }}>
        <strong>Recent News:</strong>
        <ul style={{ marginTop: '4px', marginLeft: '20px' }}>
          {company.web_research.recent_news.map((news, idx) => (
            <li key={idx} style={{ marginBottom: '2px' }}>{news}</li>
          ))}
        </ul>
      </div>
    )}

    {/* Technology Stack */}
    {company.web_research.technology_stack && (
      <div style={{ marginBottom: '12px' }}>
        <strong>Tech Stack:</strong>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
          {company.web_research.technology_stack.map((tech, idx) => (
            <span key={idx} style={{
              padding: '2px 6px',
              backgroundColor: '#e0e7ff',
              color: '#3730a3',
              borderRadius: '3px',
              fontSize: '11px'
            }}>
              {tech}
            </span>
          ))}
        </div>
      </div>
    )}

    {/* Key Customers */}
    {company.web_research.key_customers && (
      <div style={{ marginBottom: '12px' }}>
        <strong>Key Customers:</strong>
        <span style={{ marginLeft: '8px' }}>
          {company.web_research.key_customers.join(', ')}
        </span>
      </div>
    )}

    {/* Sample Employees */}
    {company.sample_employees && company.sample_employees.length > 0 && (
      <div>
        <strong>Sample Employees:</strong>
        <ul style={{ marginTop: '4px', marginLeft: '20px' }}>
          {company.sample_employees.slice(0, 3).map((emp, idx) => (
            <li key={idx}>
              {emp.name} - <em>{emp.title}</em>
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
)}
```

---

### Priority 4: Add Export Functionality

#### Task 4.1: Add Export Button
**Location:** After the category header (around line 4280)

```jsx
{/* Export button for deep research data */}
<button
  onClick={() => exportDeepResearch()}
  style={{
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    padding: '12px 24px',
    backgroundColor: '#7c3aed',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  }}
>
  <span>📥</span>
  Export Research Data
</button>
```

#### Task 4.2: Add Export Function
**Location:** Add before the return statement in main component

```jsx
const exportDeepResearch = () => {
  if (!companyResearchResults || !companyResearchResults.companies_by_category) {
    alert('No research data to export');
    return;
  }

  // Flatten all companies from categories
  const allCompanies = Object.values(companyResearchResults.companies_by_category)
    .flat();

  // Create export data with deep research fields
  const exportData = allCompanies.map(company => ({
    name: company.company_name,
    score: company.relevance_score,
    category: company.category,
    website: company.web_research?.website || '',
    description: company.web_research?.description || '',
    products: company.web_research?.products?.join(', ') || '',
    funding_amount: company.web_research?.funding?.amount || '',
    funding_stage: company.web_research?.funding?.stage || '',
    employee_count: company.web_research?.employee_count || '',
    founded: company.web_research?.founded || '',
    headquarters: company.web_research?.headquarters || '',
    tech_stack: company.web_research?.technology_stack?.join(', ') || '',
    recent_news: company.web_research?.recent_news?.join(' | ') || '',
    research_quality: company.research_quality
      ? `${(company.research_quality * 100).toFixed(0)}%`
      : '',
    coresignal_validated: company.coresignal_id ? 'Yes' : 'No',
    reasoning: company.relevance_reasoning
  }));

  // Convert to CSV
  const headers = Object.keys(exportData[0]);
  const csvContent = [
    headers.join(','),
    ...exportData.map(row =>
      headers.map(header =>
        `"${String(row[header]).replace(/"/g, '""')}"`
      ).join(',')
    )
  ].join('\n');

  // Download file
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `deep_research_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};
```

---

## 🎨 CSS Styles to Add

### Add to App.css

```css
/* Deep Research Styles */
.company-website a:hover {
  text-decoration: underline;
}

.company-products {
  margin-top: 12px;
}

.company-funding {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.research-quality {
  margin-top: 12px;
}

.expanded-details {
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .company-card {
    padding: 12px;
  }

  .company-products {
    font-size: 12px;
  }
}
```

---

## 🧪 Testing Checklist

### Visual Testing
- [ ] Website links are clickable and open in new tab
- [ ] Products display as chips/tags
- [ ] Funding information shows correctly
- [ ] Research quality bar shows appropriate color
- [ ] CoreSignal badge appears for validated companies
- [ ] Expand/collapse works smoothly
- [ ] Export button downloads CSV file

### Data Validation
- [ ] Handles missing web_research gracefully
- [ ] Handles empty arrays (products, news, etc.)
- [ ] Handles undefined fields without errors
- [ ] Research quality displays as percentage

### Responsive Design
- [ ] Mobile view (< 768px) looks good
- [ ] Tablet view (768px - 1024px) works
- [ ] Desktop view (> 1024px) optimal

### Performance
- [ ] No lag when expanding/collapsing
- [ ] Export handles 100+ companies
- [ ] Page doesn't freeze with large datasets

---

## 🚀 Implementation Order

1. **Hour 1:** Add website, products, funding display
2. **Hour 2:** Add quality indicators and badges
3. **Hour 3:** Implement expand/collapse functionality
4. **Hour 4:** Add export feature
5. **Hour 5:** CSS styling and polish
6. **Hour 6:** Testing and bug fixes

---

## 📝 Notes for Developer

### Data Structure Reference
```javascript
company = {
  company_name: "Deepgram",
  relevance_score: 9.5,
  web_research: {
    website: "deepgram.com",
    products: ["ASR API", "TTS"],
    funding: { amount: "$72M", stage: "Series B" },
    recent_news: ["News 1", "News 2"],
    technology_stack: ["Python", "Rust"],
    key_customers: ["NASA", "Spotify"]
  },
  coresignal_id: 12345,
  research_quality: 0.85,
  sample_employees: [
    { name: "John Doe", title: "ML Engineer" }
  ]
}
```

### Common Pitfalls to Avoid
1. Always check if `web_research` exists before accessing its properties
2. Use optional chaining: `company.web_research?.website`
3. Provide default values for missing data
4. Don't assume arrays have items - check length first

### Quick Test
1. Start backend: `cd backend && python app.py`
2. Start frontend: `cd frontend && npm start`
3. Go to JD Analyzer tab
4. Click "Start Research"
5. Verify new fields display

This TODO provides everything needed to complete the frontend integration!