# LinkedIn Profile AI Assessor

A full-stack LinkedIn profile assessment application that combines CoreSignal API for profile data with Claude AI for intelligent candidate evaluation. The system supports single profile assessment, batch processing via CSV, intelligent profile search with natural language queries, and a comprehensive recruiter feedback system.

## 🎯 Features

### Core Assessment Features
- 🔍 **Single Profile Assessment**: Analyze individual LinkedIn profiles with AI-powered evaluation
- 📦 **Batch Processing**: Upload CSV files for parallel candidate assessment (15-50 concurrent workers)
- 🔎 **Intelligent Search**: Find profiles using natural language queries (e.g., "Find me a technical leader with AI/ML experience in the Bay Area")
- 🎯 **Weighted Requirements**: Define up to 5 custom criteria with percentage weights for targeted scoring
- 💾 **Database Storage**: Save and load assessments via Supabase with session grouping

### NEW: Recruiter Feedback System (Phase 2) ✅
- 👍 **Quick Feedback Buttons**: Like, Dislike, and Pass reasons with pre-defined options
- 📝 **Custom Notes**: Add detailed feedback with auto-save functionality
- 🎤 **Voice-to-Text**: Record notes using Web Speech API for hands-free input
- 📊 **Feedback History**: View all previous feedback from multiple recruiters with timestamps
- 👥 **Multi-Recruiter Support**: Track which recruiter gave which feedback
- 🎨 **Visual Indicators**: Pulsing green dots on candidates with existing feedback
- 💫 **Sliding Drawer UI**: Clean, modern interface that stays visible while scrolling

### NEW: Viewport-Aware Accordion Management ✅
- 👁️ **Intersection Observer**: Automatically detects which candidate is most visible in viewport
- 🎯 **Smart Auto-Collapse**: Opening feedback drawer collapses other accordions to prevent UI overlap
- 📍 **Context-Aware**: Feedback opens for the candidate you're currently viewing, not just the one clicked
- 🔄 **Race Condition Free**: Eliminated infinite toggle loops with controlled React state
- ✨ **Visual Highlighting**: Active cards show purple border and gradient background

### Company Intelligence (Phase 1) ✅
- 🏢 **Company Tooltips**: Hover over company names to see funding, growth signals, employee count
- 💼 **LinkedIn-Style Cards**: Familiar work experience display with enriched company context
- 🎨 **Visual Indicators**: Color-coded funding stages (Seed, Series A/B, Growth, Public, Mature)
- 🖼️ **Company Logos**: Display company logos with fallback icons
- 💰 **One-Stop Research**: No need to switch between LinkedIn and Crunchbase
- 📊 **API Cost Optimization**: Only enriches companies from 2020+ (saves 60-80% API credits)

## 🛠️ Tech Stack

### Backend
- **Flask** + **Gunicorn**: Python web framework with WSGI server (120s timeout for batch processing)
- **Anthropic Claude Sonnet 4.5**: AI assessment engine (claude-sonnet-4-5-20250929)
- **CoreSignal API**: LinkedIn profile data extraction with company enrichment
- **Supabase**: PostgreSQL database via REST API for storing assessments and feedback
- **aiohttp**: Async HTTP requests for parallel profile fetching
- **ThreadPoolExecutor**: Concurrent AI assessments (15-50 workers based on deployment)

### Frontend
- **React 19**: Modern JavaScript framework with hooks
- **CSS3**: Responsive styling with modern UI patterns
- **Intersection Observer API**: Viewport detection for smart accordion management
- **Web Speech API**: Voice-to-text for recruiter notes
- **Fetch API**: HTTP requests with progress tracking

### Deployment
- **Render**: Cloud hosting platform with auto-deploy from GitHub
- **Environment-based config**: Separate configs for development/production (config.py)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- API Keys:
  - CoreSignal API key
  - Anthropic API key
  - Supabase URL and Key

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your_anthropic_key"
export CORESIGNAL_API_KEY="your_coresignal_key"
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_anon_key"

# Run Flask server (port 5001)
python3 app.py
```

### Frontend Setup

```bash
cd frontend
npm install

# Development server (port 3000)
npm start

# Production build
npm run build
# Then copy build/* to backend/ for deployment
```

### Database Setup

1. Create a Supabase project
2. Run the SQL schema from `docs/SUPABASE_SCHEMA.sql`
3. Tables created:
   - `stored_profiles` - Profile caching
   - `stored_companies` - Company data caching
   - `candidate_assessments` - AI assessment results
   - `recruiter_feedback` - Feedback notes and ratings

## 📖 Usage

### 1. Single Profile Assessment
1. Select "Single Profile" mode
2. Enter LinkedIn profile URL
3. (Optional) Add assessment criteria and weighted requirements
4. Click "Assess Profile"
5. View detailed assessment with work experience and company intelligence
6. Add feedback using the feedback drawer (purple tab on right)

### 2. Batch Processing
1. Select "Batch Processing" mode
2. Upload CSV with column: "Profile URL" or "LinkedIn URL"
3. (Optional) Add assessment criteria
4. Click "Assess Candidates"
5. View ranked results sorted by weighted score
6. Save to database or export results

### 3. Intelligent Search
1. Select "Profile Search" mode
2. Enter natural language query (e.g., "Find me a sales director in healthcare based in New York")
3. Select number of profiles (20-100)
4. Click "Search Profiles"
5. Download CSV with matching profiles

### 4. Recruiter Feedback
1. Open any candidate accordion
2. Click the purple feedback tab on the right edge
3. Choose quick feedback (Like/Dislike/Pass) or add custom notes
4. Use microphone icon for voice-to-text
5. Feedback auto-saves to database
6. View feedback history for all previous notes

## 🔑 Key API Endpoints

### Profile Assessment
- `POST /fetch-profile` - Fetch LinkedIn profile data from CoreSignal
- `POST /assess-profile` - Generate AI assessment with weighted scoring
- `POST /batch-assess-profiles` - Process multiple candidates in parallel

### Profile Search
- `POST /search-profiles` - Natural language search → CoreSignal query → CSV export

### Database Operations
- `POST /save-assessment` - Store assessment in Supabase
- `GET /load-assessments` - Retrieve all stored assessments

### Feedback System
- `POST /save-feedback` - Save recruiter feedback (likes/dislikes/notes)
- `GET /get-feedback-history` - Load all feedback for a candidate

## 📂 Project Structure

```
linkedin_profile_ai_assessor/
├── backend/
│   ├── app.py                      # Main Flask application (1317 lines)
│   ├── coresignal_service.py       # CoreSignal API integration with enrichment
│   ├── config.py                   # Deployment-specific configuration
│   ├── requirements.txt            # Python dependencies
│   └── [frontend build files]      # Served by Flask in production
├── frontend/
│   ├── src/
│   │   ├── App.js                  # Main React component (2300+ lines)
│   │   ├── App.css                 # Styling with feedback drawer, accordions
│   │   ├── components/
│   │   │   ├── CompanyTooltip.js          # Company intelligence tooltip
│   │   │   ├── CompanyTooltip.css
│   │   │   ├── WorkExperienceCard.js      # LinkedIn-style experience card
│   │   │   ├── WorkExperienceCard.css
│   │   │   ├── WorkExperienceSection.js   # Work history container
│   │   │   └── WorkExperienceSection.css
│   │   └── index.js                # React entry point
│   ├── package.json                # Node.js dependencies
│   ├── public/                     # Static assets
│   └── build/                      # Production build
├── docs/
│   ├── SUPABASE_SCHEMA.sql         # Database schema
│   ├── README.md                   # Documentation index
│   ├── archived/                   # Historical documentation
│   ├── investigations/             # Research and analysis
│   └── technical-decisions/        # Architecture decisions
├── render.yaml                     # Render deployment config
├── requirements.txt                # Root dependencies
├── runtime.txt                     # Python version for Render
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## 🎨 Key Implementation Details

### Weighted Scoring System
- Supports up to 5 custom requirements with percentage weights
- Each requirement scored 1-10 with detailed analysis
- General fit auto-calculated from remaining percentage (100% - custom weights)
- Final weighted score = Σ(requirement_score × weight%)

### CoreSignal Integration
- **Profile Fetching**: Two-step process (search by URL → fetch full profile by ID)
- **Company Enrichment**: Uses `/company_base/` endpoint for richer data (45+ fields)
- **Smart Caching**: Session-based caching to avoid redundant API calls
- **Freshness Tracking**: Uses CoreSignal's `checked_at` timestamp for data recency

### AI Assessment
- **Model**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- **Temperature**: 0.1 for consistency
- **Prompt Engineering**: Structured rubric with weighted criteria
- **Experience Calculation**: Handles overlapping roles with interval merging

### Batch Processing
- **Concurrency**: 15-50 workers based on deployment (Heroku: 15, Render: 50)
- **Profile Fetching**: Async with aiohttp for parallel API calls
- **AI Assessment**: ThreadPoolExecutor for concurrent evaluations
- **Timeout Protection**: 25-60s timeouts based on environment
- **Progress Tracking**: Real-time completion count updates

### Feedback System Architecture
- **Database**: Supabase `recruiter_feedback` table
- **State Management**: React hooks with per-candidate tracking
- **Auto-Save**: Triggers on blur, drawer close, or accordion collapse
- **Voice Input**: Web Speech API with continuous recognition
- **Viewport Detection**: Intersection Observer API for context awareness

### Viewport-Aware Accordion Management
- **Intersection Observer**: Tracks visibility ratio (0-1) for each candidate card
- **Thresholds**: 11 levels (0, 0.1, 0.2, ..., 1.0) for precise detection
- **Auto-Collapse**: When feedback drawer opens, other accordions collapse
- **Controlled State**: Single source of truth via `openAccordionId` state
- **Race Condition Prevention**: `e.preventDefault()` on summary clicks

## 🔐 Security & Configuration

### Environment Variables (Required)
```bash
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic API key
CORESIGNAL_API_KEY=...              # CoreSignal API key
SUPABASE_URL=https://...            # Supabase project URL
SUPABASE_KEY=eyJ...                 # Supabase anon key
```

### Important Notes
- ⚠️ **No hardcoded API keys** - All credentials must be in environment variables
- 🔒 **Row Level Security** - Supabase RLS policies enabled (anon role has full access)
- 📁 **Git Security** - API keys removed from all files (see commit 1458b84)

## 📊 Performance & Optimization

### API Cost Optimization
- **Company Enrichment**: Only fetches data for jobs starting 2020+
- **Savings**: 60-80% reduction in API credits per profile
- **Caching**: Session-based storage prevents duplicate fetches
- **Smart Filtering**: Skips old/irrelevant companies automatically

### Deployment Configuration
**Render (Production):**
- 50 concurrent workers
- 60s timeout
- 100 profiles per batch
- Gunicorn with 120s timeout

**Heroku (Alternative):**
- 15 concurrent workers
- 25s timeout
- 50 profiles per batch
- More conservative for smaller dynos

## 🗺️ Roadmap

### Phase 1: Company Intelligence ✅ COMPLETED
- LinkedIn-style work experience cards
- Interactive company tooltips with funding data
- Visual indicators for company stage
- API cost optimization (2020+ filter)

### Phase 2: Recruiter Feedback System ✅ COMPLETED
- Like/Dislike/Pass buttons with reasons
- Custom notes with auto-save
- Voice-to-text recording
- Feedback history display
- Multi-recruiter support
- Viewport-aware accordion management

### Phase 3: Auto-Flagging & Intelligence (PLANNED)
- Automatic flagging based on recruiter patterns
- Smart candidate recommendations
- Feedback dashboard with analytics
- Pattern visualization
- ML-based scoring refinement

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Project instructions for Claude Code
- **[docs/SUPABASE_SCHEMA.sql](docs/SUPABASE_SCHEMA.sql)** - Complete database schema
- **[docs/](docs/)** - Comprehensive documentation folder
  - `archived/` - Historical analysis and decisions
  - `investigations/` - Research reports
  - `technical-decisions/` - Architecture choices

## 🤝 Contributing

This is a proprietary recruiter tool. For feature requests or bug reports, please check the documentation first.

## 📝 Recent Updates (Latest Commit)

**Commit**: feat: Add feedback system, viewport detection, and security hardening

**Major Changes:**
- ✅ Implemented comprehensive recruiter feedback system with database persistence
- ✅ Added Intersection Observer for viewport-aware accordion management
- ✅ Fixed all race conditions in accordion state management
- ✅ Removed all hardcoded API keys (security hardening)
- ✅ Enhanced company data fetching with /company_base/ endpoint
- ✅ Added company logo display with fallback icons
- ✅ Fixed modal size constraints for better UX
- ✅ Moved all documentation to docs/ folder

**Technical Improvements:**
- 859 lines changed in App.js (feedback system, viewport detection)
- Controlled accordion components with React state
- Fixed-position feedback drawer for better scroll behavior
- Enhanced headline extraction with multi-level fallback
- Improved date parsing with robust error handling

---

**Built with Claude Code** - [https://claude.com/claude-code](https://claude.com/claude-code)

## License

This project is proprietary software. All rights reserved.
