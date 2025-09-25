# LinkedIn Profile AI Assessor

A full-stack web application that analyzes LinkedIn profiles using AI to provide comprehensive professional assessments. The system fetches LinkedIn profile data via CoreSignal API and uses Claude AI to generate detailed evaluations.

## Features

- 🔍 **LinkedIn URL Input**: Simply paste a LinkedIn profile URL
- 🤖 **AI-Powered Assessment**: Uses Claude AI for intelligent profile analysis
- 📊 **Comprehensive Scoring**: 1-10 scale with detailed breakdown
- ✅ **Binary Recommendation**: Clear recommend/not recommend decision
- 🎯 **Custom Criteria**: Specify assessment criteria for targeted evaluation
- 📱 **Modern UI**: Clean, responsive React frontend

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
│   ├── app.py                 # Flask application
│   ├── coresignal_service.py  # CoreSignal API integration
│   ├── requirements.txt       # Python dependencies
│   └── linkedin_url.py       # Example usage script
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── App.css           # Styling
│   │   └── index.js          # React entry point
│   ├── package.json          # Node.js dependencies
│   └── public/               # Static assets
├── .gitignore               # Git ignore rules
└── README.md               # This file
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions, please open an issue on GitHub.
