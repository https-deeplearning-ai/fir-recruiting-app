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
  const [weightedRequirements, setWeightedRequirements] = useState([]);
  const [newRequirement, setNewRequirement] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchMode, setBatchMode] = useState(false);

  // Dummy profile data for testing
  const dummyProfileData = {
    "id": 532675010,
    "parent_id": 532675010,
    "is_parent": 1,
    "full_name": "Yiling Zhao",
    "first_name": "Yiling",
    "last_name": "Zhao",
    "headline": "Engineer @ AI Fund | GenAI, Data Science",
    "created_at": "2022-03-31 19:06:04",
    "updated_at": "2025-09-16 19:19:14",
    "checked_at": "2025-09-16 19:19:14",
    "public_profile_id": "768276954",
    "profile_url": "https://www.linkedin.com/in/yiling-zhao-876364195",
    "location": "Stanford, California, United States",
    "industry": null,
    "summary": "📧 ylzhao@stanford.edu 🎓 https://scholar.google.com/citations?user=KwJrOK4AAAAJ&hl=en 👩‍💻 https://github.com/yi031",
    "services": null,
    "profile_photo_url": "https://static.licdn.com/aero-v1/sc/h/9c8pery4andzj6ohjkjp54ma2",
    "deleted": 0,
    "country": "United States",
    "country_iso_2": "US",
    "country_iso_3": "USA",
    "regions": [
      {
        "region": "Americas"
      },
      {
        "region": "Northern America"
      },
      {
        "region": "AMER"
      }
    ],
    "recommendations_count": null,
    "connections_count": 268,
    "follower_count": 270,
    "experience_count": 7,
    "shorthand_name": "yiling-zhao-876364195",
    "canonical_shorthand_name": "ylzhao31",
    "shorthand_names": [
      {
        "shorthand_name": "yiling-zhao-876364195"
      },
      {
        "shorthand_name": "ylzhao31"
      }
    ],
    "historical_ids": [
      {
        "id": 532675010
      }
    ],
    "also_viewed": [],
    "awards": [],
    "certifications": [
      {
        "id": "27ad3715009a6c975df48a4b9d02e8d6",
        "title": "Google Data Analytics Specialization",
        "issuer": "Coursera",
        "credential_id": null,
        "certificate_url": "https://www.coursera.org/account/accomplishments/specialization/certificate/G73VXTPG9X9W?trk=public_profile_certification-title",
        "date_from": "May 2022",
        "date_from_year": 2022,
        "date_from_month": 5,
        "date_to": null,
        "date_to_year": null,
        "date_to_month": null,
        "issuer_url": "https://www.linkedin.com/company/coursera",
        "order_in_profile": 1,
        "deleted": 0,
        "created_at": "2024-09-02 23:15:34",
        "updated_at": "2025-09-16 19:19:14"
      }
    ],
    "courses": [],
    "education": [
      {
        "id": "9f0a5582c4d55ec4b55e1ea729306eca",
        "institution": "Stanford University",
        "program": "Master of Science - MS",
        "date_from": null,
        "date_from_year": null,
        "date_from_month": null,
        "date_to": null,
        "date_to_year": null,
        "date_to_month": null,
        "activities_and_societies": null,
        "description": null,
        "institution_url": "https://www.linkedin.com/school/stanford-university",
        "institution_shorthand_name": "stanford-university",
        "order_in_profile": 1,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "c8498ea7b5be9571a5280d8264618308",
        "institution": "University of California, Los Angeles",
        "program": "Bachelor of Science - BS",
        "date_from": null,
        "date_from_year": null,
        "date_from_month": null,
        "date_to": null,
        "date_to_year": null,
        "date_to_month": null,
        "activities_and_societies": null,
        "description": null,
        "institution_url": "https://www.linkedin.com/school/ucla",
        "institution_shorthand_name": "ucla",
        "order_in_profile": 1,
        "deleted": 1,
        "created_at": "2022-07-07 15:22:11",
        "updated_at": "2022-07-07 15:22:11"
      }
    ],
    "experience": [
      {
        "id": "93a916a1ec8d9e40882bc70648391f7d",
        "title": "Engineer in Residence",
        "location": null,
        "company_id": 11931736,
        "company_source_id": 18619445,
        "company_name": "AI Fund",
        "company_url": "https://www.linkedin.com/company/aifund",
        "company_url_shorthand_name": "aifund",
        "company_url_canonical_shorthand_name": "aifund",
        "company_industry": "Venture Capital and Private Equity Principals",
        "company_website": "https://www.aifund.ai/",
        "company_employees_count": 89,
        "company_size": "11-50 employees",
        "date_from": "August 2025",
        "date_from_year": 2025,
        "date_from_month": 8,
        "date_to": null,
        "date_to_year": null,
        "date_to_month": null,
        "is_current": 1,
        "duration": "2 months",
        "description": null,
        "order_in_profile": 1,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "ab35c7734482e012f72b2147e8a090a1",
        "title": "Research Assistant",
        "location": "Stanford, California, United States",
        "company_id": 26226775,
        "company_source_id": 1790,
        "company_name": "Stanford University School of Medicine",
        "company_url": "https://www.linkedin.com/school/stanford-university-school-of-medicine",
        "company_url_shorthand_name": "stanford-university-school-of-medicine",
        "company_url_canonical_shorthand_name": "stanford-university-school-of-medicine",
        "company_industry": "Higher Education",
        "company_website": "http://med.stanford.edu",
        "company_employees_count": 9150,
        "company_size": "5,001-10,000 employees",
        "date_from": "March 2025",
        "date_from_year": 2025,
        "date_from_month": 3,
        "date_to": "June 2025",
        "date_to_year": 2025,
        "date_to_month": 6,
        "is_current": 0,
        "duration": "4 months",
        "description": null,
        "order_in_profile": 2,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "00ca2d76954e35390440b02eeba4d289",
        "title": "Research Assistant",
        "location": null,
        "company_id": 26226757,
        "company_source_id": 10174162,
        "company_name": "Stanford University Graduate School of Education",
        "company_url": "https://www.linkedin.com/school/stanfordeducation",
        "company_url_shorthand_name": "stanfordeducation",
        "company_url_canonical_shorthand_name": "stanfordeducation",
        "company_industry": "Higher Education",
        "company_website": "https://ed.stanford.edu/",
        "company_employees_count": 342,
        "company_size": "201-500 employees",
        "date_from": "April 2024",
        "date_from_year": 2024,
        "date_from_month": 4,
        "date_to": "June 2025",
        "date_to_year": 2025,
        "date_to_month": 6,
        "is_current": 0,
        "duration": "1 year 3 months",
        "description": null,
        "order_in_profile": 3,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "332922f5d94e0ebc3289a06b2bc3551e",
        "title": "Research Assistant",
        "location": null,
        "company_id": 12954599,
        "company_source_id": 18927585,
        "company_name": "Stanford Institute for Human-Centered Artificial Intelligence (HAI)",
        "company_url": "https://www.linkedin.com/company/stanfordhai",
        "company_url_shorthand_name": "stanfordhai",
        "company_url_canonical_shorthand_name": "stanfordhai",
        "company_industry": "Higher Education",
        "company_website": "http://hai.stanford.edu",
        "company_employees_count": 191,
        "company_size": "11-50 employees",
        "date_from": "November 2023",
        "date_from_year": 2023,
        "date_from_month": 11,
        "date_to": "March 2025",
        "date_to_year": 2025,
        "date_to_month": 3,
        "is_current": 0,
        "duration": "1 year 5 months",
        "description": null,
        "order_in_profile": 4,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "1de4d451d29f0d204de6c5eb678fb57a",
        "title": "Product Development Intern",
        "location": null,
        "company_id": 6474848,
        "company_source_id": 163705,
        "company_name": "ETS",
        "company_url": "https://www.linkedin.com/company/educational-testing-service-ets",
        "company_url_shorthand_name": "educational-testing-service-ets",
        "company_url_canonical_shorthand_name": "educational-testing-service-ets",
        "company_industry": "Education Administration Programs",
        "company_website": "http://www.ets.org",
        "company_employees_count": 7995,
        "company_size": "1,001-5,000 employees",
        "date_from": "June 2024",
        "date_from_year": 2024,
        "date_from_month": 6,
        "date_to": "August 2024",
        "date_to_year": 2024,
        "date_to_month": 8,
        "is_current": 0,
        "duration": "3 months",
        "description": "<p class=\"show-more-less-text__text--less\">\n        Multimodal AI, Product Innovation &amp; Development\n<!---->      </p>",
        "order_in_profile": 5,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "2fa417583d35a3cc9899d3b8d44eb286",
        "title": "Data and Policy Analyst",
        "location": "Los Angeles, California, United States",
        "company_id": 8893407,
        "company_source_id": 343453,
        "company_name": "Acumen, LLC",
        "company_url": "https://www.linkedin.com/company/acumen-llc",
        "company_url_shorthand_name": "acumen-llc",
        "company_url_canonical_shorthand_name": "acumen-llc",
        "company_industry": "Public Policy Offices",
        "company_website": "http://www.acumenllc.com/",
        "company_employees_count": 615,
        "company_size": "501-1,000 employees",
        "date_from": "December 2022",
        "date_from_year": 2022,
        "date_from_month": 12,
        "date_to": "August 2023",
        "date_to_year": 2023,
        "date_to_month": 8,
        "is_current": 0,
        "duration": "9 months",
        "description": null,
        "order_in_profile": 6,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      },
      {
        "id": "71fb4d5960aeb23ba951f093ee34a60a",
        "title": "Research Assistant",
        "location": "Los Angeles, California, United States",
        "company_id": 2974443,
        "company_source_id": 2477,
        "company_name": "UCLA",
        "company_url": "https://www.linkedin.com/school/ucla",
        "company_url_shorthand_name": "ucla",
        "company_url_canonical_shorthand_name": "ucla",
        "company_industry": "Higher Education",
        "company_website": "http://ucla.edu",
        "company_employees_count": 28536,
        "company_size": "5,001-10,000 employees",
        "date_from": "May 2022",
        "date_from_year": 2022,
        "date_from_month": 5,
        "date_to": "October 2022",
        "date_to_year": 2022,
        "date_to_month": 10,
        "is_current": 0,
        "duration": "6 months",
        "description": null,
        "order_in_profile": 7,
        "deleted": 0,
        "created_at": "2025-09-16 19:19:14",
        "updated_at": "2025-09-16 19:19:14"
      }
    ],
    "groups": [],
    "interests": [],
    "languages": [],
    "organizations": [],
    "patents": [],
    "posts_see_more_urls": [],
    "projects": [],
    "publications": [],
    "recommendations": [],
    "similar_profiles": [],
    "others_named": [],
    "skills": [],
    "test_scores": [],
    "volunteering_cares": [],
    "volunteering_opportunities": [],
    "volunteering_positions": [],
    "volunteering_supports": [],
    "websites": [
      {
        "id": "2e40baf81c513bbaee307acc6130d692",
        "personal_website": "https://www.linkedin.com/redir/redirect?url=https://proximal-brownie-13e.notion.site/Hi-I-m-Yiling-Yilia-Zhao-66300788fc704c029c57804c89831c64&urlhash=3lis&trk=public_profile_topcard-website",
        "order_in_profile": 1,
        "deleted": 0,
        "created_at": "2024-01-21 01:14:42",
        "updated_at": "2025-09-16 19:19:14"
      }
    ],
    "course_suggestions": [],
    "activity": [],
    "hidden_details": []
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFetchingProfile(true);
    setError('');
    setAssessment(null);
    setProfileSummary(null);

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
          user_prompt: userPrompt || 'Provide a general professional assessment',
          weighted_requirements: weightedRequirements
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

  const addRequirement = () => {
    const currentTotal = weightedRequirements.reduce((sum, req) => sum + req.weight, 0);
    const canAddMore = currentTotal < 100 && weightedRequirements.length < 5;
    
    if (newRequirement.trim() && canAddMore) {
      setWeightedRequirements([...weightedRequirements, {
        id: Date.now(),
        text: newRequirement.trim(),
        weight: 0
      }]);
      setNewRequirement('');
    }
  };

  const removeRequirement = (id) => {
    setWeightedRequirements(weightedRequirements.filter(req => req.id !== id));
  };

  const updateRequirementWeight = (id, weight) => {
    // Calculate the total weight of other requirements (excluding current one)
    const otherRequirementsTotal = weightedRequirements
      .filter(req => req.id !== id)
      .reduce((sum, req) => sum + req.weight, 0);
    
    // Calculate the maximum allowed weight for this requirement
    const maxAllowedWeight = 100 - otherRequirementsTotal;
    
    // Ensure the weight doesn't exceed the maximum allowed
    const constrainedWeight = Math.min(weight, maxAllowedWeight);
    
    setWeightedRequirements(weightedRequirements.map(req => 
      req.id === id ? { ...req, weight: constrainedWeight } : req
    ));
  };

  const getGeneralFitWeight = () => {
    const totalUserWeight = weightedRequirements.reduce((sum, req) => sum + req.weight, 0);
    return Math.max(0, 100 - totalUserWeight);
  };

  const getMaxAllowedWeight = (requirementId) => {
    const otherRequirementsTotal = weightedRequirements
      .filter(req => req.id !== requirementId)
      .reduce((sum, req) => sum + req.weight, 0);
    return 100 - otherRequirementsTotal;
  };

  const handleTest = async () => {
    setLoading(true);
    setError('');
    setAssessment(null);
    setProfileSummary(null);

    try {
      console.log('Testing with dummy profile data...');
      
      // Use dummy profile data directly

      // Step 2: Assess the profile
      console.log('Assessing profile...');
      
      const assessResponse = await fetch('http://localhost:5001/assess-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile_data: dummyProfileData,
          user_prompt: userPrompt || 'Provide a general professional assessment',
          weighted_requirements: weightedRequirements
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
    }
  };

  const handleCsvFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'text/csv') {
      setCsvFile(file);
      setBatchMode(true);
    } else {
      setError('Please select a valid CSV file');
    }
  };

  const parseCsv = (csvText) => {
    console.log('Raw CSV text (first 500 chars):', csvText.substring(0, 500));
    
    const lines = csvText.split('\n').filter(line => line.trim());
    console.log('Number of lines:', lines.length);
    console.log('First few lines:', lines.slice(0, 3));
    
    // More robust CSV parsing that handles quoted fields with commas
    const parseCsvLine = (line) => {
      const result = [];
      let current = '';
      let inQuotes = false;
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      result.push(current.trim());
      return result;
    };
    
    const headers = parseCsvLine(lines[0]);
    console.log('Parsed headers:', headers);
    
    // Look for various possible column names
    const possibleUrlNames = ['profile url', 'profile_url', 'linkedin url', 'linkedin_url', 'url', 'profile', 'linkedin'];
    const profileUrlIndex = headers.findIndex(h => 
      possibleUrlNames.some(name => h.toLowerCase().includes(name))
    );
    
    const possibleFirstNameNames = ['first name', 'first_name', 'firstname', 'first', 'given name', 'given_name'];
    const firstNameIndex = headers.findIndex(h => 
      possibleFirstNameNames.some(name => h.toLowerCase().includes(name))
    );
    
    const possibleLastNameNames = ['last name', 'last_name', 'lastname', 'last', 'surname', 'family name', 'family_name'];
    const lastNameIndex = headers.findIndex(h => 
      possibleLastNameNames.some(name => h.toLowerCase().includes(name))
    );
    
    console.log('Profile URL column index:', profileUrlIndex);
    console.log('First Name column index:', firstNameIndex);
    console.log('Last Name column index:', lastNameIndex);
    console.log('All column names:', headers.map((h, i) => `${i}: "${h}"`));
    
    if (profileUrlIndex === -1) {
      throw new Error(`CSV file must contain a column with "Profile URL" or similar. Found columns: ${headers.join(', ')}`);
    }

    const candidates = [];
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line) {
        const columns = parseCsvLine(line);
        console.log(`Row ${i} (${columns.length} columns):`, columns);
        
        const url = columns[profileUrlIndex] ? columns[profileUrlIndex].replace(/"/g, '') : '';
        const firstName = columns[firstNameIndex] ? columns[firstNameIndex].replace(/"/g, '') : '';
        const lastName = columns[lastNameIndex] ? columns[lastNameIndex].replace(/"/g, '') : '';
        
        console.log(`Row ${i} data:`, { url, firstName, lastName });
        
        // Only add if it looks like a LinkedIn URL
        if (url.includes('linkedin.com') || url.startsWith('http')) {
          candidates.push({
            url: url,
            firstName: firstName,
            lastName: lastName,
            fullName: `${firstName} ${lastName}`.trim()
          });
        } else {
          console.log(`Skipping non-URL value: "${url}"`);
        }
      }
    }
    
    console.log('Final extracted candidates:', candidates);
    return candidates;
  };

  const handleBatchProcess = async () => {
    if (!csvFile) {
      setError('Please select a CSV file first');
      return;
    }

    setBatchLoading(true);
    setError('');
    setBatchResults([]);

    try {
      const csvText = await csvFile.text();
      const candidates = parseCsv(csvText);
      
      console.log(`Processing ${candidates.length} candidates...`);
      
      const response = await fetch('http://localhost:5001/batch-fetch-profiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          candidates: candidates
        }),
      });

      const data = await response.json();

      if (data.success) {
        setBatchResults(data.results);
        console.log('Batch processing complete:', data.summary);
      } else {
        setError(data.error || 'Failed to process batch');
      }
    } catch (err) {
      setError('Network error. Please make sure the Flask server is running on port 5001.');
      console.error('Error:', err);
    } finally {
      setBatchLoading(false);
    }
  };

  const resetToSingleMode = () => {
    setBatchMode(false);
    setCsvFile(null);
    setBatchResults([]);
    setBatchLoading(false);
  };

  const getScoreColor = (score) => {
    const numericScore = typeof score === 'number' ? score : parseFloat(score);
    if (isNaN(numericScore)) return '#6c757d';
    
    if (numericScore >= 8) return '#4CAF50'; // Green
    if (numericScore >= 6) return '#FF9800'; // Orange
    if (numericScore >= 4) return '#FFC107'; // Yellow
    return '#f44336'; // Red
  };

  const renderScoreBar = (score) => {
    const numericScore = typeof score === 'number' ? score : parseFloat(score);
    if (isNaN(numericScore)) return null;
    
    const percentage = (numericScore / 10) * 100;
    const color = getScoreColor(numericScore);

    return (
      <div className="score-container">
        <div className="score-bar">
          <div 
            className="score-fill" 
            style={{ 
              width: `${percentage}%`, 
              backgroundColor: color 
            }}
          ></div>
        </div>
        <span className="score-text">{numericScore}/10</span>
      </div>
    );
  };

  const renderWeightedScore = (score) => {
    const numericScore = typeof score === 'number' ? score : parseFloat(score);
    if (isNaN(numericScore)) return null;
    
    const color = getScoreColor(numericScore);
    
    return (
      <span className="weighted-score" style={{ color: color }}>
        {numericScore}/10
      </span>
    );
  };

  return (
    <div className="App">
      <div className="container">
        <h1>LinkedIn Profile AI Assessor</h1>
        <p className="description">
          {batchMode ? 'Upload a CSV file with LinkedIn URLs for batch assessment' : 'Enter a LinkedIn profile URL and get an AI-powered assessment'}
        </p>

        <div className="mode-toggle">
          <button 
            className={`mode-btn ${!batchMode ? 'active' : ''}`}
            onClick={() => setBatchMode(false)}
          >
            Single Profile
          </button>
          <button 
            className={`mode-btn ${batchMode ? 'active' : ''}`}
            onClick={() => setBatchMode(true)}
          >
            Batch Processing
          </button>
        </div>

        {!batchMode ? (
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
            <textarea
              id="userPrompt"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="e.g., 'Focus on leadership experience and technical skills' or 'Evaluate for senior developer role'"
              rows="3"
            />
          </div>

          <div className="form-group">
            <label>Weighted Requirements (Optional):</label>
            <div className="weighted-requirements">
              <div className="add-requirement">
                <input
                  type="text"
                  value={newRequirement}
                  onChange={(e) => setNewRequirement(e.target.value)}
                  placeholder="Enter a specific requirement (e.g., 'Startup experience')"
                  onKeyPress={(e) => e.key === 'Enter' && addRequirement()}
                />
                <button 
                  type="button" 
                  onClick={addRequirement}
                  disabled={!newRequirement.trim() || weightedRequirements.length >= 5 || weightedRequirements.reduce((sum, req) => sum + req.weight, 0) >= 100}
                  className="add-btn"
                >
                  Add
                </button>
              </div>
              
              {weightedRequirements.reduce((sum, req) => sum + req.weight, 0) >= 100 && (
                <div className="total-warning">
                  <span>⚠️ Total requirements reached 100%. Adjust existing requirements to add more.</span>
                </div>
              )}
              
              {weightedRequirements.map((req) => {
                const maxAllowedWeight = getMaxAllowedWeight(req.id);
                const isAtMax = req.weight >= maxAllowedWeight;
                
                return (
                  <div key={req.id} className="requirement-item">
                    <span className="requirement-text">{req.text}</span>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="0"
                        max={maxAllowedWeight}
                        value={req.weight}
                        onChange={(e) => updateRequirementWeight(req.id, parseInt(e.target.value))}
                        className={`weight-slider ${isAtMax ? 'at-max' : ''}`}
                      />
                      <span className={`weight-value ${isAtMax ? 'at-max' : ''}`}>
                        {req.weight}%
                        {isAtMax && <span className="max-indicator"> (max)</span>}
                        {maxAllowedWeight < 100 && <span className="max-allowed"> / {maxAllowedWeight}%</span>}
                      </span>
                      <button 
                        type="button" 
                        onClick={() => removeRequirement(req.id)}
                        className="remove-btn"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                );
              })}
              
              <div className="requirement-item general-fit">
                <span className="requirement-text">General Fit</span>
                <div className="slider-container">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={getGeneralFitWeight()}
                    disabled
                    className="weight-slider general-slider"
                  />
                  <span className="weight-value">{getGeneralFitWeight()}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="button-group">
            <button 
              type="submit" 
              className="submit-btn" 
              disabled={loading}
            >
              {fetchingProfile ? 'Fetching Profile...' : loading ? 'Analyzing Profile...' : 'Assess Profile'}
            </button>
            
            <button 
              type="button" 
              onClick={handleTest}
              className="test-btn" 
              disabled={loading}
            >
              {loading ? 'Testing...' : 'Test'}
            </button>
          </div>
        </form>
        ) : (
          <div className="batch-form">
            <div className="form-group">
              <label htmlFor="csvFile">Upload CSV File:</label>
              <input
                id="csvFile"
                type="file"
                accept=".csv"
                onChange={handleCsvFileChange}
                className="file-input"
              />
              <p className="file-help">
                CSV file must contain a "Profile URL" column with LinkedIn URLs. 
                Optional: "First Name" and "Last Name" columns for better display.
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="batchUserPrompt">Assessment Criteria (Optional):</label>
              <textarea
                id="batchUserPrompt"
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="e.g., 'Focus on leadership experience and technical skills' or 'Evaluate for senior developer role'"
                rows="3"
              />
            </div>

            <div className="form-group">
              <label>Weighted Requirements (Optional):</label>
              <div className="weighted-requirements">
                <div className="add-requirement">
                  <input
                    type="text"
                    value={newRequirement}
                    onChange={(e) => setNewRequirement(e.target.value)}
                    placeholder="Enter a specific requirement (e.g., 'Startup experience')"
                    onKeyPress={(e) => e.key === 'Enter' && addRequirement()}
                  />
                  <button 
                    type="button" 
                    onClick={addRequirement}
                    disabled={!newRequirement.trim() || weightedRequirements.length >= 5 || weightedRequirements.reduce((sum, req) => sum + req.weight, 0) >= 100}
                    className="add-btn"
                  >
                    Add
                  </button>
                </div>
                
                {weightedRequirements.reduce((sum, req) => sum + req.weight, 0) >= 100 && (
                  <div className="total-warning">
                    <span>⚠️ Total requirements reached 100%. Adjust existing requirements to add more.</span>
                  </div>
                )}
                
                {weightedRequirements.map((req) => {
                  const maxAllowedWeight = getMaxAllowedWeight(req.id);
                  const isAtMax = req.weight >= maxAllowedWeight;
                  
                  return (
                    <div key={req.id} className="requirement-item">
                      <span className="requirement-text">{req.text}</span>
                      <div className="slider-container">
                        <input
                          type="range"
                          min="0"
                          max={maxAllowedWeight}
                          value={req.weight}
                          onChange={(e) => updateRequirementWeight(req.id, parseInt(e.target.value))}
                          className={`weight-slider ${isAtMax ? 'at-max' : ''}`}
                        />
                        <span className={`weight-value ${isAtMax ? 'at-max' : ''}`}>
                          {req.weight}%
                          {isAtMax && <span className="max-indicator"> (max)</span>}
                          {maxAllowedWeight < 100 && <span className="max-allowed"> / {maxAllowedWeight}%</span>}
                        </span>
                        <button 
                          type="button" 
                          onClick={() => removeRequirement(req.id)}
                          className="remove-btn"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  );
                })}
                
                <div className="requirement-item general-fit">
                  <span className="requirement-text">General Fit</span>
                  <div className="slider-container">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={getGeneralFitWeight()}
                      disabled
                      className="weight-slider general-slider"
                    />
                    <span className="weight-value">{getGeneralFitWeight()}%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="button-group">
              <button 
                type="button" 
                onClick={handleBatchProcess}
                className="submit-btn" 
                disabled={!csvFile || batchLoading}
              >
                {batchLoading ? 'Processing...' : 'Process Batch'}
              </button>
              
              <button 
                type="button" 
                onClick={resetToSingleMode}
                className="test-btn"
              >
                Back to Single
              </button>
            </div>
          </div>
        )}

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
                {assessment.weighted_analysis && assessment.weighted_analysis.weighted_score !== undefined ? (
                  <div className="weighted-summary">
                    <h4>Weighted Final Score</h4>
                    {renderScoreBar(assessment.weighted_analysis.weighted_score)}
                  </div>
                ) : (
                  <div className="overall-summary">
                    <h4>Overall Profile Score</h4>
                    {renderScoreBar(assessment.overall_score)}
                  </div>
                )}
                {/* {assessment.weighted_analysis && assessment.weighted_analysis.weighted_score !== undefined && (
                  <div className={`recommendation ${assessment.weighted_analysis.weighted_score >= 6 ? 'recommend' : 'not-recommend'}`}>
                    <strong>Recommendation: </strong>
                    {assessment.weighted_analysis.weighted_score >= 6 ? '✅ RECOMMEND' : '❌ NOT RECOMMENDED'}
                  </div>
                )} */}
              </div>
            )}

{assessment.weighted_analysis && assessment.weighted_analysis.requirements && (
              <div className="section">
                <h3>Weighted Analysis</h3>
                <div className="weighted-analysis">
                  {assessment.weighted_analysis.requirements.map((req, index) => (
                    <div key={index} className="requirement-analysis">
                      <div className="requirement-header">
                        <h4>
                          <strong>{req.requirement}</strong> ({req.weight}%)
                        </h4>
                        <div className="requirement-score">
                          Score: {renderWeightedScore(req.score)}
                        </div>
                      </div>
                      <p className="requirement-text">{req.analysis}</p>
                    </div>
                  ))}
                  
                  {assessment.weighted_analysis.general_fit_weight > 0 && (
                    <div className="requirement-analysis general-fit-analysis">
                      <div className="requirement-header">
                        <h4>
                          <strong>General Fit</strong> ({assessment.weighted_analysis.general_fit_weight}%)
                        </h4>
                        <div className="requirement-score">
                          Score: {renderWeightedScore(assessment.weighted_analysis.general_fit_score)}
                        </div>
                      </div>
                      <p className="requirement-text">{assessment.weighted_analysis.general_fit_analysis}</p>
                    </div>
                  )}
                </div>
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


            {assessment.detailed_analysis && !assessment.weighted_analysis && (
              <div className="section">
                <h3>Detailed Analysis</h3>
                <div className="detailed-analysis">
                  {assessment.detailed_analysis}
                </div>
              </div>
            )}
          </div>
        )}

        {batchResults.length > 0 && (
          <div className="batch-results">
            <h2>Batch Processing Results ({batchResults.length} profiles)</h2>
            <div className="candidates-list">
              {batchResults.map((result, index) => (
                <div key={index} className="candidate-card">
                  <div className="candidate-header">
                    <div className="candidate-rank">
                      <span className="rank-number">#{index + 1}</span>
                    </div>
                    <div className="candidate-info">
                      <h3>{result.csv_name || result.profile_data?.profile_data?.full_name || 'Unknown Name'}</h3>
                      <div className="candidate-meta">
                        <span className="candidate-location">{result.profile_data?.profile_data?.location_raw_address || 'N/A'}</span>
                        <span className="candidate-headline">{result.profile_data?.profile_data?.headline || 'N/A'}</span>
                      </div>
                    </div>
                    <div className="candidate-status">
                      {result.success ? (
                        <div className="status-badge success">
                          ✅ Profile Found
                        </div>
                      ) : (
                        <div className="status-badge error">
                          ❌ Profile Not Found
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {result.success ? (
                    <div className="candidate-details">
                      <div className="candidate-summary">
                        <div><strong>Industry:</strong> {result.profile_data?.profile_data?.company_industry || 'N/A'}</div>
                        <div><strong>Connections:</strong> {result.profile_data?.profile_data?.connections_count || 'N/A'}</div>
                        <div><strong>Experience:</strong> {result.profile_data?.profile_data?.experience?.length || 'N/A'} positions</div>
                      </div>
                      
                      <div className="candidate-json">
                        <details>
                          <summary>View Raw Profile Data</summary>
                          <pre className="json-display">
                            {JSON.stringify(result.profile_data, null, 2)}
                          </pre>
                        </details>
                      </div>
                    </div>
                  ) : (
                    <div className="candidate-error">
                      <p><strong>Error:</strong> {result.error}</p>
                      <p>URL: {result.url}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;