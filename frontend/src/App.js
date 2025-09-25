// App.js
import React, { useState } from 'react';
import './App.css';

function App() {
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [userPrompt, setUserPrompt] = useState('');
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetchingProfile, setFetchingProfile] = useState(false);
  const [error, setError] = useState('');
  const [profileSummary, setProfileSummary] = useState(null);
  const [profileData, setProfileData] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFetchingProfile(true);
    setError('');
    setAssessment(null);
    setProfileSummary(null);
    setProfileData(null);

    try {
      // Step 1: Fetch profile data from CoreSignal API
      console.log('Fetching profile data for:', linkedinUrl);
      
      const fetchResponse = await fetch('http://localhost:5001/fetch-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          linkedin_url: linkedinUrl
        }),
      });

      const fetchData = await fetchResponse.json();

      if (!fetchData.success) {
        let errorMessage = fetchData.error || 'Failed to fetch profile data';
        if (fetchData.debug_info) {
          errorMessage += `\n\nDebug Info:\n- Original URL: ${fetchData.debug_info.original_url}\n- Normalized URL: ${fetchData.debug_info.normalized_url}\n- Search strategies tried: ${fetchData.debug_info.strategies_tried}`;
        }
        setError(errorMessage);
        setLoading(false);
        setFetchingProfile(false);
        return;
      }

      console.log('Profile data fetched successfully');
      setProfileData(fetchData.profile_data);
      setFetchingProfile(false);

      // Step 2: Assess the profile
      console.log('Assessing profile...');
      
      const assessResponse = await fetch('http://localhost:5001/assess-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile_data: fetchData.profile_data,
          user_prompt: userPrompt || 'Provide a general professional assessment'
        }),
      });

      const assessData = await assessResponse.json();

      if (assessData.success) {
        setAssessment(assessData.assessment);
        setProfileSummary(assessData.profile_summary);
      } else {
        setError(assessData.error || 'An error occurred while assessing the profile');
      }
    } catch (err) {
      setError('Network error. Please make sure the Flask server is running on port 5001.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
      setFetchingProfile(false);
    }
  };

  const handleLoadSample = () => {
    // Load a sample LinkedIn URL
    setLinkedinUrl('https://www.linkedin.com/in/adityakalro');
  };

  const renderScoreBar = (score) => {
    const numericScore = typeof score === 'number' ? score : parseFloat(score);
    if (isNaN(numericScore)) return null;
    
    const percentage = (numericScore / 10) * 100;
    const getColor = (score) => {
      if (score >= 8) return '#4CAF50';
      if (score >= 6) return '#FF9800';
      return '#f44336';
    };

    return (
      <div className="score-container">
        <div className="score-bar">
          <div 
            className="score-fill" 
            style={{ 
              width: `${percentage}%`, 
              backgroundColor: getColor(numericScore) 
            }}
          ></div>
        </div>
        <span className="score-text">{numericScore}/10</span>
      </div>
    );
  };

  return (
    <div className="App">
      <div className="container">
        <h1>LinkedIn Profile AI Assessor</h1>
        <p className="description">
          Enter a LinkedIn profile URL and get an AI-powered assessment
        </p>

        <form onSubmit={handleSubmit} className="input-form">
          <div className="form-group">
            <label htmlFor="linkedinUrl">LinkedIn Profile URL:</label>
            <input
              id="linkedinUrl"
              type="text"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://www.linkedin.com/in/username"
              required
            />
            <button 
              type="button" 
              onClick={handleLoadSample}
              className="sample-btn"
            >
              Load Sample URL
            </button>
          </div>

          <div className="form-group">
            <label htmlFor="userPrompt">Assessment Criteria (Optional):</label>
            <input
              id="userPrompt"
              type="text"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="e.g., 'Focus on leadership experience and technical skills' or 'Evaluate for senior developer role'"
            />
          </div>

          <button 
            type="submit" 
            className="submit-btn" 
            disabled={loading}
          >
            {fetchingProfile ? 'Fetching Profile...' : loading ? 'Analyzing Profile...' : 'Assess Profile'}
          </button>
        </form>

        {error && (
          <div className="error">
            <h3>Error:</h3>
            <p>{error}</p>
          </div>
        )}

        {/* {profileData && (
          <div className="profile-data">
            <h2>Fetched Profile Data</h2>
            <div className="profile-info">
              <div><strong>Name:</strong> {profileData.full_name || 'N/A'}</div>
              <div><strong>Headline:</strong> {profileData.headline || 'N/A'}</div>
              <div><strong>Location:</strong> {profileData.location || 'N/A'}</div>
              <div><strong>Industry:</strong> {profileData.industry || 'N/A'}</div>
              <div><strong>Connections:</strong> {profileData.connections_count || 'N/A'}</div>
              <div><strong>Experience Count:</strong> {profileData.experience_count || 'N/A'}</div>
            </div>
          </div>
        )} */}

        {profileSummary && (
          <div className="profile-summary">
            <h2>User Profile</h2>
            <div className="summary-grid">
              <div><strong>Name:</strong> {profileSummary.full_name}</div>
              <div><strong>Location:</strong> {profileSummary.location}</div>
              <div><strong>Industry:</strong> {profileSummary.industry}</div>
              <div><strong>Experience:</strong> {profileSummary.total_experience_years} years</div>
            </div>
            
            {profileSummary.current_roles && profileSummary.current_roles.length > 0 && (
              <div className="current-roles">
                <h3>Current Roles:</h3>
                {profileSummary.current_roles.map((role, index) => (
                  <div key={index} className="role">
                    {role.title} at {role.company_name}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {assessment && (
          <div className="assessment-results">
            <h2>AI Assessment Results</h2>
            
            {assessment.overall_score && (
              <div className="score-section">
                <h3>Overall Profile Score</h3>
                {renderScoreBar(assessment.overall_score)}
                {assessment.recommend !== undefined && (
                  <div className={`recommendation ${assessment.recommend ? 'recommend' : 'not-recommend'}`}>
                    <strong>Outreach Recommendation: </strong>
                    {assessment.recommend ? '✅ RECOMMEND' : '❌ NOT RECOMMENDED'}
                  </div>
                )}
              </div>
            )}

            {assessment.career_trajectory && (
              <div className="section">
                <h3>Career Trajectory Analysis</h3>
                <p>{assessment.career_trajectory}</p>
              </div>
            )}

            {assessment.strengths && assessment.strengths.length > 0 && (
              <div className="section">
                <h3>Key Strengths</h3>
                <ul>
                  {assessment.strengths.map((strength, index) => (
                    <li key={index}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}

            {assessment.weaknesses && assessment.weaknesses.length > 0 && (
              <div className="section">
                <h3>Key Weaknesses</h3>
                <ul>
                  {assessment.weaknesses.map((weakness, index) => (
                    <li key={index}>{weakness}</li>
                  ))}
                </ul>
              </div>
            )}

        
            {assessment.detailed_analysis && (
              <div className="section">
                <h3>Detailed Analysis</h3>
                <div className="detailed-analysis">
                  {assessment.detailed_analysis}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;