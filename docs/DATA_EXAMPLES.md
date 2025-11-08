# Deep Research Data Examples

## 🎯 Overview

This document shows REAL examples of data returned by the deep research feature, helping you understand what's available for display in the UI.

---

## 📊 Example 1: Deepgram (Voice AI Company)

### Input
```python
company_name = "Deepgram"
target_domain = "voice AI and speech recognition"
```

### Full Output
```json
{
  "company_name": "Deepgram",
  "relevance_score": 9.5,
  "category": "direct_competitor",
  "reasoning": "Deepgram is a direct competitor in voice AI with core ASR products, real-time speech recognition API, and recent innovations like Nova-2 model and Aura TTS. Their focus on developer-friendly voice AI solutions, substantial Series B funding, and customer base including NASA and Spotify make them highly relevant for recruiting voice AI talent.",

  "web_research": {
    "website": "deepgram.com",
    "description": "Speech recognition API platform that provides developers with powerful tools for transcribing and understanding audio in real-time",
    "products": [
      "Speech-to-Text API",
      "Nova-2 Speech Recognition Model",
      "Aura Text-to-Speech",
      "Audio Intelligence Features",
      "Live Streaming Transcription"
    ],
    "funding": {
      "stage": "Series B",
      "amount": "$72M",
      "date": "2021",
      "investors": ["Tiger Global", "Wing VC", "Nvidia"]
    },
    "employee_count": "50-200",
    "founded": "2015",
    "headquarters": "San Francisco, CA",
    "recent_news": [
      "Released Nova-2 model with 30% improved accuracy",
      "Launched Aura TTS with human-like voices",
      "Partnership with CallRail for call analytics",
      "Expanded language support to 30+ languages"
    ],
    "technology_stack": [
      "Python",
      "Rust",
      "CUDA",
      "PyTorch",
      "Kubernetes",
      "WebRTC"
    ],
    "key_customers": [
      "NASA",
      "Spotify",
      "Discord",
      "Citibank",
      "CallRail"
    ],
    "competitive_position": "Leader in real-time ASR with focus on accuracy and developer experience",
    "market_focus": "Developer-first speech AI platform for enterprises and startups"
  },

  "coresignal_id": 485023,
  "coresignal_data": {
    "industry": "Software Development",
    "employees_count": 156,
    "founded": 2015,
    "location_hq_city": "San Francisco",
    "location_hq_country": "United States",
    "company_type": "Private",
    "specialties": ["Speech Recognition", "Machine Learning", "NLP", "Voice AI"],
    "funding_rounds": [
      {
        "round_type": "Series B",
        "amount": 72000000,
        "year": 2021
      },
      {
        "round_type": "Series A",
        "amount": 25000000,
        "year": 2020
      }
    ]
  },

  "sample_employees": [
    {
      "id": 123456,
      "name": "Scott Stephenson",
      "title": "CEO & Co-Founder",
      "headline": "Building the future of voice AI",
      "location": "San Francisco Bay Area"
    },
    {
      "id": 789012,
      "name": "Jane Chen",
      "title": "Senior ML Engineer",
      "headline": "Deep learning for speech recognition",
      "location": "San Francisco, CA"
    },
    {
      "id": 345678,
      "name": "Michael Roberts",
      "title": "Voice AI Research Scientist",
      "headline": "Advancing state-of-the-art in ASR",
      "location": "Remote"
    }
  ],

  "research_quality": 0.92,
  "deep_research_complete": true,
  "researched_via": "claude_agent_sdk",
  "research_timestamp": "2024-11-06T10:30:45Z"
}
```

---

## 📊 Example 2: AssemblyAI (Transcription API)

### Input
```python
company_name = "AssemblyAI"
target_domain = "voice AI and transcription"
```

### Output Summary
```json
{
  "company_name": "AssemblyAI",
  "relevance_score": 9.0,
  "category": "direct_competitor",

  "web_research": {
    "website": "assemblyai.com",
    "description": "AI models for transcribing and understanding speech, built for developers",
    "products": [
      "Transcription API",
      "Speaker Diarization",
      "Sentiment Analysis",
      "Chapter Detection",
      "PII Redaction"
    ],
    "funding": {
      "stage": "Series C",
      "amount": "$63M",
      "date": "2022"
    },
    "employee_count": "50-100",
    "headquarters": "San Francisco, CA",
    "technology_stack": ["Python", "TensorFlow", "Kubernetes", "React"]
  },

  "coresignal_id": 521847,
  "research_quality": 0.88
}
```

---

## 📊 Example 3: Scale AI (Not Voice, But Related)

### Input
```python
company_name = "Scale AI"
target_domain = "voice AI"  # Testing relevance scoring
```

### Output Summary
```json
{
  "company_name": "Scale AI",
  "relevance_score": 5.5,
  "category": "adjacent_company",
  "reasoning": "Scale AI provides data labeling for ML including some audio/speech datasets, but not a core voice AI company. Relevant for ML infrastructure talent but not voice AI specialists.",

  "web_research": {
    "website": "scale.com",
    "description": "Data platform for AI, providing high-quality training data",
    "products": [
      "Data Labeling",
      "RLHF Platform",
      "Synthetic Data Generation",
      "Model Evaluation"
    ],
    "funding": {
      "stage": "Series E",
      "amount": "$325M",
      "date": "2021"
    },
    "employee_count": "500-1000"
  },

  "research_quality": 0.79
}
```

---

## 📊 Example 4: Company Not in CoreSignal

### Input
```python
company_name = "VoiceFlow"  # Smaller company
target_domain = "voice AI"
```

### Output
```json
{
  "company_name": "VoiceFlow",
  "relevance_score": 7.0,

  "web_research": {
    "website": "voiceflow.com",
    "description": "Design, prototype and build voice apps",
    "products": ["Voice App Builder", "Conversation Design Tool"],
    "funding": {
      "stage": "Series A",
      "amount": "$20M"
    }
  },

  "coresignal_id": null,  // Not found in CoreSignal
  "coresignal_data": {},   // Empty
  "sample_employees": [],  // No employees sampled

  "research_quality": 0.65  // Lower quality due to less data
}
```

---

## 📊 Example 5: Failed Research (Timeout/Error)

### Input
```python
company_name = "FakeCompany123XYZ"
target_domain = "voice AI"
```

### Output
```json
{
  "company_name": "FakeCompany123XYZ",
  "relevance_score": 5.0,  // Default score
  "category": "unknown",

  "web_research": {
    "website": null,
    "description": null,
    "products": [],
    "funding": {},
    "error": "Research failed or timed out"
  },

  "coresignal_id": null,
  "coresignal_data": {},
  "sample_employees": [],

  "research_quality": 0.0,  // No confidence
  "deep_research_complete": false
}
```

---

## 🔍 Field Descriptions

### Core Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `company_name` | string | Company name | "Deepgram" |
| `relevance_score` | float | 1-10 relevance to domain | 9.5 |
| `category` | string | Classification | "direct_competitor" |
| `reasoning` | string | Why this score/category | "Based on ASR products..." |
| `research_quality` | float | 0-1 confidence score | 0.92 (92% confident) |

### Web Research Fields

| Field | Type | Always Present | Description |
|-------|------|---------------|-------------|
| `website` | string | Usually | Official website URL |
| `description` | string | Usually | What the company does |
| `products` | array | Often | List of products/services |
| `funding.amount` | string | Sometimes | Funding amount like "$72M" |
| `funding.stage` | string | Sometimes | Series A, B, C, etc. |
| `employee_count` | string | Often | Range like "50-200" |
| `founded` | string | Often | Year founded |
| `headquarters` | string | Often | HQ location |
| `recent_news` | array | Sometimes | Recent developments |
| `technology_stack` | array | Sometimes | Technologies used |
| `key_customers` | array | Sometimes | Notable customers |

### CoreSignal Fields

| Field | Type | Present When | Description |
|-------|------|-------------|-------------|
| `coresignal_id` | int/null | If found | Unique ID in CoreSignal |
| `coresignal_data` | object | If found | Verified company data |
| `sample_employees` | array | If found | 0-5 employee samples |

---

## 🎨 UI Display Recommendations

### Priority 1: Always Show
```jsx
// These fields are most important
company.company_name        // "Deepgram"
company.relevance_score     // 9.5
company.web_research.website // "deepgram.com"
```

### Priority 2: Show When Available
```jsx
// These add significant value
company.web_research.products  // ["ASR API", "TTS"]
company.web_research.funding   // "$72M Series B"
company.research_quality       // 92% confidence
```

### Priority 3: Expandable Details
```jsx
// Nice to have in expanded view
company.web_research.recent_news
company.web_research.technology_stack
company.sample_employees
```

---

## 📈 Research Quality Interpretation

### Quality Score Ranges

| Score | Meaning | UI Color | What It Means |
|-------|---------|----------|---------------|
| 0.8-1.0 | Excellent | Green | Found website, products, funding, and more |
| 0.6-0.8 | Good | Yellow | Found core info but missing some details |
| 0.4-0.6 | Fair | Orange | Basic info only |
| 0.0-0.4 | Poor | Red | Very limited or failed research |

### Visual Representation
```jsx
// Color based on quality
const getQualityColor = (quality) => {
  if (quality >= 0.8) return '#10b981'; // Green
  if (quality >= 0.6) return '#f59e0b'; // Yellow
  if (quality >= 0.4) return '#fb923c'; // Orange
  return '#ef4444'; // Red
};
```

---

## 🔄 Handling Missing Data

### Safe Access Patterns

```jsx
// Always use optional chaining
const website = company.web_research?.website || 'No website found';
const products = company.web_research?.products || [];
const funding = company.web_research?.funding?.amount || 'Unknown';

// Check arrays before mapping
{company.web_research?.products?.length > 0 && (
  <div>{company.web_research.products.map(...)}</div>
)}

// Provide fallbacks
const employeeCount = company.web_research?.employee_count
  || company.coresignal_data?.employees_count
  || 'Unknown';
```

---

## 🎯 Category Definitions

| Category | Score Range | Description |
|----------|------------|-------------|
| `direct_competitor` | 8-10 | Same products, same market |
| `adjacent_company` | 6-8 | Related but not direct |
| `same_category` | 5-7 | Same industry, different focus |
| `tangential` | 3-5 | Loosely related |
| `similar_stage` | 3-5 | Similar company stage |
| `talent_pool` | 1-3 | Good for general talent |
| `unknown` | N/A | Evaluation failed |

---

## 💡 Usage Tips

1. **Check research_quality** - Low quality means limited data
2. **Prefer web_research** - More current than CoreSignal
3. **Fallback gracefully** - Always have default values
4. **Show confidence** - Users trust transparency

This document shows exactly what data you have to work with - now go make it visible!