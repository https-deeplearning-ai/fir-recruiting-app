# LinkedIn Profile Assessor

A full-stack web application that analyzes LinkedIn profiles using AI for comprehensive professional assessments. Features intelligent search, single profile analysis, batch processing, and weighted requirement scoring.

## Features

- 🔎 **Intelligent Search**: Find profiles by user specified filters (e.g. job title, location, industry, etc.)
- 💯 **Single Profile Assessment**: Analyze individual LinkedIn profiles
- 📊 **Batch Processing**: Upload CSV files for bulk candidate assessment  
- 🎯 **Weighted Requirements**: Define custom criteria with importance weights
- 💾 **Data Persistence**: Save assessments to Supabase database
- 🤖 **AI-Powered**: Uses Claude AI for intelligent analysis and scoring

## Tech Stack

### Backend
- **Flask** + **Gunicorn**: Python web framework with WSGI server
- **Anthropic Claude**: AI assessment engine
- **CoreSignal API**: LinkedIn profile data extraction
- **Supabase**: PostgreSQL database for storing assessments
- **aiohttp**: Async HTTP requests for batch processing
- **python-dotenv**: Environment variable management

### Frontend
- **React 19**: Modern JavaScript framework
- **CSS3**: Responsive styling with modern UI
- **Fetch API**: HTTP requests

### Deployment
- **Render**: Cloud hosting platform
- **Environment-based config**: Separate configs for development/production

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- CoreSignal API key
- Anthropic API key
- Supabase account

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your_key_here"
export CORESIGNAL_API_KEY="your_key_here"  
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Usage

1. **Intelligent Search**: Search profiles by skills/location
3. **Single Profile**: Enter LinkedIn URL + optional criteria
3. **Batch Processing**: Upload CSV with candidate URLs
4. **Weighted Requirements**: Define custom criteria with importance weights
5. **Save Results**: Store assessments in database for later review

## Key API Endpoints

- `POST /fetch-profile` - Get LinkedIn profile data
- `POST /assess-profile` - Generate AI assessment
- `POST /batch-assess-profiles` - Process multiple candidates
- `POST /intelligent-search` - Find profiles by criteria
- `GET /saved-assessments` - Retrieve stored assessments
- `POST /save-assessments` - Store assessment results

## Project Structure

```
linkedin-assessor/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── coresignal_service.py  # CoreSignal API integration
│   ├── config.py             # Environment-specific settings
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/App.js            # React main component
│   ├── src/App.css           # Styling
│   └── package.json          # Node.js dependencies
├── render.yaml               # Render deployment config
└── requirements.txt          # Root dependencies
```
