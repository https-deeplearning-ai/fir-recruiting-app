# LinkedIn Profile AI Assessor

A full-stack web application that analyzes LinkedIn profiles using AI to provide comprehensive professional assessments. The system fetches LinkedIn profile data via CoreSignal API and uses Claude AI to generate detailed evaluations.

## Features

### Core Features
- 🔍 **LinkedIn URL Input**: Simply paste a LinkedIn profile URL
- 🤖 **AI-Powered Assessment**: Uses Claude Sonnet 4.5 for intelligent profile analysis (best for coding and complex agents)
- 📊 **Comprehensive Scoring**: 1-10 scale with weighted requirements
- ✅ **Binary Recommendation**: Clear recommend/not recommend decision
- 🎯 **Custom Criteria**: Specify assessment criteria for targeted evaluation
- 📱 **Modern UI**: Clean, responsive React frontend

### NEW: Enhanced Recruiter UX (Phase 1)
- 🏢 **Company Intelligence Tooltips**: Hover over company names to see funding data, stage, growth signals
- 💼 **LinkedIn-Style Work Experience Cards**: Familiar interface with enriched company context
- 🎨 **Visual Indicators**: Color-coded funding stages (Seed, Series A/B, Growth, Public, Mature)
- 💰 **One-Stop Research Hub**: No need to switch between LinkedIn and Crunchbase
- 🚀 **Growth Signals**: Hypergrowth, Recently Funded, B2B, Modern Tech Stack indicators
- 📊 **API Cost Optimization**: Only enriches companies from 2020+ (saves 60-80% API credits)

### Additional Features
- 📦 **Batch Processing**: Upload CSV with multiple LinkedIn URLs for parallel assessment
- 🔎 **Natural Language Search**: Find candidates using conversational queries
- 💾 **Database Storage**: Save and load assessments via Supabase
- 📈 **Real-time Progress**: Loading overlays with progress tracking
- 🎯 **Weighted Requirements**: Assign percentage weights to up to 5 custom criteria

## Tech Stack

### Backend
- **Flask**: Python web framework
- **CoreSignal API**: LinkedIn profile data extraction
- **Anthropic Claude**: AI assessment engine
- **CORS**: Cross-origin resource sharing

### Frontend
- **React**: Modern JavaScript framework
- **CSS3**: Responsive styling
- **Fetch API**: HTTP requests

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- CoreSignal API key
- Anthropic API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
   ```

4. **Start the Flask server:**
   ```bash
   python3 app.py
   ```
   Server will run on `http://localhost:5001`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```
   App will run on `http://localhost:3000`

## Usage

1. **Open the application** in your browser at `http://localhost:3000`
2. **Enter a LinkedIn URL** in the format: `https://www.linkedin.com/in/username`
3. **Add assessment criteria** (optional) to focus the evaluation
4. **Click "Assess Profile"** to get AI-powered analysis
5. **Review the results** including score, strengths, weaknesses, and recommendation

## API Endpoints

### `POST /fetch-profile`
Fetches LinkedIn profile data from CoreSignal API.

**Request:**
```json
{
  "linkedin_url": "https://www.linkedin.com/in/username"
}
```

**Response:**
```json
{
  "success": true,
  "profile_data": { ... },
  "employee_id": "123456"
}
```

### `POST /assess-profile`
Generates AI assessment of the profile.

**Request:**
```json
{
  "profile_data": { ... },
  "user_prompt": "Assessment criteria"
}
```

**Response:**
```json
{
  "success": true,
  "profile_summary": { ... },
  "assessment": {
    "overall_score": 8,
    "recommend": true,
    "strengths": [...],
    "weaknesses": [...],
    "career_trajectory": "...",
    "detailed_analysis": "..."
  }
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Project Structure

```
linkedin-assessor/
├── backend/
│   ├── app.py                      # Flask application (1470 lines)
│   ├── coresignal_service.py       # CoreSignal API integration with enrichment
│   ├── config.py                   # Deployment configuration
│   ├── requirements.txt            # Python dependencies
│   └── input_values.json          # Valid search field values
├── frontend/
│   ├── src/
│   │   ├── components/            # NEW: React components
│   │   │   ├── CompanyTooltip.js       # Enriched company data tooltip
│   │   │   ├── CompanyTooltip.css
│   │   │   ├── WorkExperienceCard.js   # LinkedIn-style experience card
│   │   │   ├── WorkExperienceCard.css
│   │   │   ├── WorkExperienceSection.js # Work history container
│   │   │   └── WorkExperienceSection.css
│   │   ├── App.js                 # Main React component (1700 lines)
│   │   ├── App.css                # Styling
│   │   └── index.js               # React entry point
│   ├── package.json               # Node.js dependencies
│   └── public/                    # Static assets
├── docs/                          # Documentation
│   ├── COMMUNICATION_LOG.md       # Change history and decisions
│   ├── ENHANCED_UX_GUIDE.md       # User guide for new features
│   ├── TESTING_GUIDE.md           # Testing instructions
│   ├── API_OPTIMIZATION_SUMMARY.md # Cost optimization details
│   ├── HEADLINE_FRESHNESS_FIX.md
│   └── IMPLEMENTATION_SUMMARY.md
├── .gitignore
└── README.md                      # This file
```

## Configuration

### CoreSignal API
The CoreSignal API key is hardcoded in `coresignal_service.py`. For production, move this to environment variables.

### Anthropic API
Set your Anthropic API key as an environment variable:
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

## Scoring System

The AI assessment uses a rigorous 1-10 scoring system:

- **9-10**: Exceptional fit - meets all key requirements
- **7-8**: Good fit - minor gaps but strong potential
- **5-6**: Moderate fit - some significant gaps but potential
- **3-4**: Poor fit - major gaps, better suited for different roles
- **1-2**: Not recommended - fundamental mismatches

---

## Enhanced Recruiter UX (NEW)

### Company Intelligence Tooltips

The app now displays enriched company data inline with work experience, eliminating the need to switch between LinkedIn and Crunchbase.

**How to Use:**
1. Enable "🏢 Deep Dive Company Research" checkbox when assessing a profile
2. View the candidate's detailed assessment
3. Scroll to the "Work Experience" section
4. **Hover over company names** (blue text with ℹ️ icon) to see tooltips

**Tooltip Data:**
- 💰 Funding stage (Seed, Series A/B/C, Growth, Public)
- 💵 Amount raised
- 📊 Total funding rounds
- 🏭 Company type (Public, Private, Non-Profit)
- 📅 Company age
- 📍 Headquarters location
- 👥 Employee count
- 💼 Business model (B2B/B2C)
- 🚀 Growth signals (Hypergrowth, Recently Funded, Modern Tech, etc.)

**Visual Indicators:**
- 🌱 Seed stage (green)
- 🚀 Series A (blue)
- 📈 Series B (orange)
- 📊 Growth/Late Stage (purple)
- 🏛️ Public (gray)
- 🏢 Mature (brown)

**API Cost Optimization:**
- Only enriches companies from jobs starting in 2020 or later
- Saves 60-80% of API credits per profile
- Focuses on recent, relevant experience
- Session-based caching for repeated companies

**For detailed information, see:**
- [Enhanced UX Guide](ENHANCED_UX_GUIDE.md) - Complete user guide
- [Testing Guide](TESTING_GUIDE.md) - How to test the features
- [API Optimization Summary](API_OPTIMIZATION_SUMMARY.md) - Cost savings details

---

## Documentation

- **[COMMUNICATION_LOG.md](COMMUNICATION_LOG.md)** - Complete history of changes and decisions
- **[ENHANCED_UX_GUIDE.md](ENHANCED_UX_GUIDE.md)** - User guide for company intelligence features
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing scenarios and debugging tips
- **[API_OPTIMIZATION_SUMMARY.md](API_OPTIMIZATION_SUMMARY.md)** - API cost optimization strategies
- **[CLAUDE.md](CLAUDE.md)** - Project instructions for Claude Code

---

## Roadmap

### Phase 1: Company Intelligence Tooltips ✅ COMPLETED
- LinkedIn-style work experience cards
- Interactive company tooltips with funding data
- Visual indicators for company stage
- API cost optimization (2020+ filter)

### Phase 2: Recruiter Feedback System (PLANNED)
- 👍 Like/Dislike buttons
- 🚩 Custom red flags
- ✅ Custom green flags
- 📝 Notes on candidates
- 🧠 Pattern learning from feedback

### Phase 3: Auto-Flagging & Intelligence (PLANNED)
- Automatic flagging based on recruiter patterns
- Smart candidate recommendations
- Feedback dashboard
- Pattern visualization

---

## Contributing

For feature requests or bug reports, please check the [Communication Log](COMMUNICATION_LOG.md) first to see if it's already been addressed.

---

## License

This project is proprietary software. All rights reserved.
