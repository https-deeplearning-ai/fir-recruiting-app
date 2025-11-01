// App.js
import React, { useState } from 'react';
import JsonView from '@uiw/react-json-view';
import { TbRefresh } from "react-icons/tb";
import WorkExperienceSection from './components/WorkExperienceSection';
import ListsView from './components/ListsView';
import CrunchbaseValidationModal from './components/CrunchbaseValidationModal';
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
  const [searchMode, setSearchMode] = useState(false);
  const [listsMode, setListsMode] = useState(false);
  const [searchPrompt, setSearchPrompt] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [profileCount, setProfileCount] = useState(20);
  const [singleProfileResults, setSingleProfileResults] = useState([]);
  const [savedAssessments, setSavedAssessments] = useState([]);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [savingAssessments, setSavingAssessments] = useState(false);
  const [showLoadingOverlay, setShowLoadingOverlay] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Processing...');
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  const [useRealtimeData, setUseRealtimeData] = useState(false); // Toggle for fresh data
  const [enrichCompanies, setEnrichCompanies] = useState(true); // Toggle for company enrichment (default: enabled)
  const [forceRefresh, setForceRefresh] = useState(false); // Toggle for forcing fresh data pull (bypasses storage)
  const [rawCoreSignalData, setRawCoreSignalData] = useState(null); // Store raw CoreSignal JSON
  const [showRawJSON, setShowRawJSON] = useState(false); // Toggle to show/hide raw JSON
  const [enrichmentSummary, setEnrichmentSummary] = useState(null); // Store company enrichment summary

  // Recruiter feedback state
  const [selectedRecruiter, setSelectedRecruiter] = useState(() => {
    // Load recruiter name from localStorage on initial load
    return localStorage.getItem('recruiterName') || '';
  });
  const [candidateFeedback, setCandidateFeedback] = useState({}); // Store feedback per candidate URL
  const [feedbackHistory, setFeedbackHistory] = useState({}); // Store all feedback history from DB
  const [isRecording, setIsRecording] = useState({}); // Track which candidate is being recorded
  const [showFeedbackInput, setShowFeedbackInput] = useState({}); // Track if input is visible per candidate
  const [hideAIAnalysis, setHideAIAnalysis] = useState({}); // Track if AI analysis sections are hidden per candidate
  const [drawerOpen, setDrawerOpen] = useState({}); // Track which candidate's feedback drawer is open
  const [activeCandidate, setActiveCandidate] = useState(null); // Track currently active candidate feedback
  const [openAccordionId, setOpenAccordionId] = useState(null); // Track which candidate's accordion is currently open (auto-collapse)
  const [candidateVisibility, setCandidateVisibility] = useState({}); // Track viewport visibility percentage for each candidate
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState({}); // Track AI analysis loading state per candidate
  const [autoGenerateAI, setAutoGenerateAI] = useState(false); // Toggle for automatic AI analysis after profile fetch

  // JD Analyzer state
  const [jdAnalyzerMode, setJdAnalyzerMode] = useState(false); // Toggle for JD Analyzer view
  const [jdText, setJdText] = useState(''); // Raw job description text
  const [jdAnalyzing, setJdAnalyzing] = useState(false); // Loading state during JD analysis

  // Company Research Agent state
  const [companyResearchMode, setCompanyResearchMode] = useState(false); // Toggle for Company Research view
  const [companyJdText, setCompanyJdText] = useState(''); // JD text for company research
  const [companyResearching, setCompanyResearching] = useState(false); // Loading state during research
  const [companySessionId, setCompanySessionId] = useState(null); // Current research session ID
  const [companyResearchStatus, setCompanyResearchStatus] = useState(null); // Session status
  const [companyResearchResults, setCompanyResearchResults] = useState(null); // Research results
  const [extractedRequirements, setExtractedRequirements] = useState([]); // AI-extracted requirements
  const [activeJD, setActiveJD] = useState(null); // Currently active JD {title, requirements, timestamp}
  const [jdTitle, setJdTitle] = useState(''); // User-provided title for the JD
  const [showWeightedRequirements, setShowWeightedRequirements] = useState(false); // Accordion toggle for weighted requirements
  const [jdSearching, setJdSearching] = useState(false); // Loading state during JD → CoreSignal search
  const [jdSearchResults, setJdSearchResults] = useState(null); // Search results from CoreSignal
  const [jdFullResults, setJdFullResults] = useState(null); // Full 100 candidates from "Search with model" button
  const [jdCsvData, setJdCsvData] = useState(null); // CSV data for optional download
  const [currentPage, setCurrentPage] = useState(1); // Pagination for full results
  const [hoveredProfile, setHoveredProfile] = useState(null); // For tooltip display
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 }); // Tooltip positioning

  // LLM comparison states - 3 separate states for independent loading
  const [claudeResult, setClaudeResult] = useState(null);
  const [gptResult, setGptResult] = useState(null);
  const [geminiResult, setGeminiResult] = useState(null);
  const [claudeLoading, setClaudeLoading] = useState(false);
  const [gptLoading, setGptLoading] = useState(false);
  const [geminiLoading, setGeminiLoading] = useState(false);
  const [selectedLlmQuery, setSelectedLlmQuery] = useState(null); // 'claude', 'gpt', or 'gemini'
  const [activeLlmTab, setActiveLlmTab] = useState('claude'); // Which tab is currently visible

  // Crunchbase URL validation state
  const [validationModalOpen, setValidationModalOpen] = useState(false);
  const [validationData, setValidationData] = useState(null); // {companyId, companyName, crunchbaseUrl, source}

  // Save recruiter name to localStorage whenever it changes
  React.useEffect(() => {
    if (selectedRecruiter) {
      localStorage.setItem('recruiterName', selectedRecruiter);
    }
  }, [selectedRecruiter]);

  // Load active JD from localStorage on mount
  React.useEffect(() => {
    const savedJD = localStorage.getItem('activeJD');
    if (savedJD) {
      try {
        const jdData = JSON.parse(savedJD);
        setActiveJD(jdData);
        setWeightedRequirements(jdData.requirements || []);
        setJdTitle(jdData.title || '');
        console.log('✓ Loaded active JD from localStorage:', jdData.title);
      } catch (e) {
        console.error('Error loading active JD:', e);
        localStorage.removeItem('activeJD');
      }
    }
  }, []);

  // Pre-made feedback reasons
  const likeReasons = [
    "✨ Relevant work experience",
    "📈 Strong growth trajectory",
    "🎯 Perfect skill match",
    "🏢 Top-tier companies",
    "🚀 Leadership potential"
  ];

  const passReasons = [
    "❌ Not a good fit for role",
    "🏢 Companies don't match",
    "📊 Lack of relevant experience",
    "🎯 Skills mismatch",
    "⏰ Other timing/reasons"
  ];

  // Notification function
  const showNotification = (message, type = 'success') => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: '' });
    }, 3000);
  };

  // Get the most visible candidate in viewport
  const getMostVisibleCandidate = () => {
    let maxVisibility = 0;
    let mostVisibleUrl = null;

    Object.entries(candidateVisibility).forEach(([url, visibilityRatio]) => {
      if (visibilityRatio > maxVisibility) {
        maxVisibility = visibilityRatio;
        mostVisibleUrl = url;
      }
    });

    return mostVisibleUrl;
  };

  // Set up Intersection Observer to track candidate visibility
  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const candidateUrl = entry.target.getAttribute('data-candidate-url');
          if (candidateUrl) {
            setCandidateVisibility(prev => ({
              ...prev,
              [candidateUrl]: entry.intersectionRatio
            }));
          }
        });
      },
      {
        threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        rootMargin: '-50px 0px -50px 0px' // Give some margin from top/bottom
      }
    );

    // Observe all candidate cards
    const candidateCards = document.querySelectorAll('.candidate-card[data-candidate-url]');
    candidateCards.forEach(card => observer.observe(card));

    return () => {
      candidateCards.forEach(card => observer.unobserve(card));
    };
  }, [singleProfileResults, batchResults, savedAssessments]); // Re-run when candidates change

  // Format CoreSignal freshness badge
  const formatFreshnessBadge = (checked_at) => {
    if (!checked_at) return null;

    try {
      const checkedDate = new Date(checked_at.replace(' ', 'T'));
      const now = new Date();
      const diffMs = now - checkedDate;
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      let badgeColor, badgeText, badgeEmoji;

      if (diffDays === 0) {
        badgeColor = '#10b981'; // Green
        badgeText = 'Today';
        badgeEmoji = '🟢';
      } else if (diffDays === 1) {
        badgeColor = '#10b981'; // Green
        badgeText = 'Yesterday';
        badgeEmoji = '🟢';
      } else if (diffDays < 7) {
        badgeColor = '#10b981'; // Green
        badgeText = `${diffDays}d ago`;
        badgeEmoji = '🟢';
      } else if (diffDays < 30) {
        badgeColor = '#f59e0b'; // Orange
        badgeText = `${Math.floor(diffDays / 7)}w ago`;
        badgeEmoji = '🟡';
      } else if (diffDays < 90) {
        badgeColor = '#f59e0b'; // Orange
        badgeText = `${Math.floor(diffDays / 30)}mo ago`;
        badgeEmoji = '🟡';
      } else {
        badgeColor = '#ef4444'; // Red
        badgeText = `${Math.floor(diffDays / 30)}mo ago`;
        badgeEmoji = '🔴';
      }

      return { badgeColor, badgeText, badgeEmoji, diffDays };
    } catch (error) {
      return null;
    }
  };

  // Save recruiter feedback with debounce
  const saveFeedback = async (linkedinUrl, feedbackType, feedbackText = '') => {
    try {
      const response = await fetch('/save-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          linkedin_url: linkedinUrl,
          feedback_type: feedbackType,
          feedback_text: feedbackText,
          recruiter_name: selectedRecruiter
        })
      });

      const data = await response.json();
      if (data.success) {
        console.log(`✅ Saved ${feedbackType} from ${selectedRecruiter}`);
        return true;
      } else {
        console.error('Failed to save feedback:', data.error);
        return false;
      }
    } catch (error) {
      console.error('Error saving feedback:', error);
      return false;
    }
  };

  // Debounced note saver (2 second delay)
  // Use useRef to maintain debounce timeout across re-renders
  const debounceTimeouts = React.useRef({});

  // Handle note text change (with debounced auto-save)
  const handleNoteChange = (linkedinUrl, noteText) => {
    // Update local state immediately
    setCandidateFeedback(prev => ({
      ...prev,
      [linkedinUrl]: {
        ...prev[linkedinUrl],
        note: noteText
      }
    }));

    // Clear any existing timeout for this candidate
    if (debounceTimeouts.current[linkedinUrl]) {
      clearTimeout(debounceTimeouts.current[linkedinUrl]);
    }

    // Set new timeout for auto-save (2 seconds after typing stops)
    debounceTimeouts.current[linkedinUrl] = setTimeout(async () => {
      if (noteText && noteText.trim()) {
        await saveFeedback(linkedinUrl, 'note', noteText);
        showNotification('Feedback auto-saved');
      }
      // Clean up timeout reference
      delete debounceTimeouts.current[linkedinUrl];
    }, 2000);
  };

  // Handle note blur - cancel debounce and save immediately
  const handleNoteBlur = async (linkedinUrl, noteText) => {
    // Cancel any pending debounced save
    if (debounceTimeouts.current[linkedinUrl]) {
      clearTimeout(debounceTimeouts.current[linkedinUrl]);
      delete debounceTimeouts.current[linkedinUrl];
    }

    // Save immediately on blur if there's text
    if (noteText && noteText.trim()) {
      await saveFeedback(linkedinUrl, 'note', noteText);
      showNotification('Feedback saved');
    }
  };

  // Handle like/dislike button clicks
  const handleFeedbackClick = async (linkedinUrl, feedbackType) => {
    await saveFeedback(linkedinUrl, feedbackType);

    // Update local state to show which button was clicked
    setCandidateFeedback(prev => ({
      ...prev,
      [linkedinUrl]: {
        ...prev[linkedinUrl],
        [feedbackType]: true
      }
    }));
  };

  // Voice-to-text recording
  const startVoiceRecording = (linkedinUrl) => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Voice input not supported in your browser. Please use Chrome.');
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      setIsRecording(prev => ({ ...prev, [linkedinUrl]: true }));
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) {
        const currentNote = candidateFeedback[linkedinUrl]?.note || '';
        const newNote = currentNote + finalTranscript;
        handleNoteChange(linkedinUrl, newNote);
      }
    };

    recognition.onerror = () => {
      setIsRecording(prev => ({ ...prev, [linkedinUrl]: false }));
    };

    recognition.onend = () => {
      setIsRecording(prev => ({ ...prev, [linkedinUrl]: false }));
    };

    recognition.start();

    // Store recognition object to stop it later
    setCandidateFeedback(prev => ({
      ...prev,
      [linkedinUrl]: {
        ...prev[linkedinUrl],
        recognition
      }
    }));
  };

  const stopVoiceRecording = (linkedinUrl) => {
    const recognition = candidateFeedback[linkedinUrl]?.recognition;
    if (recognition) {
      recognition.stop();
    }
    setIsRecording(prev => ({ ...prev, [linkedinUrl]: false }));
  };

  // Toggle accordion (work experience details)
  const toggleAccordion = (candidateUrl) => {
    const isCurrentlyOpen = openAccordionId === candidateUrl;

    if (isCurrentlyOpen) {
      // Closing this accordion
      setOpenAccordionId(null);
      // Also close feedback drawer if it's open for this candidate
      if (drawerOpen[candidateUrl]) {
        handleDrawerCollapse(candidateUrl);
        setDrawerOpen(prev => ({
          ...prev,
          [candidateUrl]: false
        }));
        setActiveCandidate(null);
      }
    } else {
      // Opening this accordion
      // If a feedback drawer is active, auto-collapse other accordions
      if (activeCandidate && activeCandidate !== candidateUrl) {
        // Don't allow opening different accordion when feedback is active elsewhere
        return;
      }
      setOpenAccordionId(candidateUrl);
    }
  };

  // Toggle feedback drawer
  const toggleDrawer = async (linkedinUrl, candidateName) => {
    // Determine which candidate to open feedback for
    let targetUrl = linkedinUrl;

    // If no specific URL provided or if opening from a closed state,
    // use the most visible candidate in viewport
    if (!linkedinUrl || !drawerOpen[linkedinUrl]) {
      const mostVisible = getMostVisibleCandidate();
      if (mostVisible && (!linkedinUrl || mostVisible !== linkedinUrl)) {
        console.log(`🎯 Opening feedback for most visible candidate: ${mostVisible}`);
        targetUrl = mostVisible;
      }
    }

    // If opening new drawer while another is open, save previous
    if (activeCandidate && activeCandidate !== targetUrl && drawerOpen[activeCandidate]) {
      await handleDrawerCollapse(activeCandidate);
    }

    setDrawerOpen(prev => ({
      ...prev,
      [targetUrl]: !prev[targetUrl]
    }));

    if (!drawerOpen[targetUrl]) {
      setActiveCandidate(targetUrl);
      // When opening feedback drawer, auto-collapse other accordions
      setOpenAccordionId(targetUrl);
      // Load feedback history when opening drawer
      await loadFeedbackHistory(targetUrl);
    } else {
      setActiveCandidate(null);
    }
  };

  // Auto-save and collapse drawer
  const handleDrawerCollapse = async (linkedinUrl) => {
    // Cancel any pending debounced save
    if (debounceTimeouts.current[linkedinUrl]) {
      clearTimeout(debounceTimeouts.current[linkedinUrl]);
      delete debounceTimeouts.current[linkedinUrl];
    }

    // Save immediately if there's a note
    const note = candidateFeedback[linkedinUrl]?.note;
    if (note && note.trim()) {
      await saveFeedback(linkedinUrl, 'note', note);
      showNotification('Feedback saved');
    }
    setDrawerOpen(prev => ({ ...prev, [linkedinUrl]: false }));
  };

  // Clear current recruiter's feedback
  const clearMyFeedback = async (linkedinUrl, candidateName) => {
    if (!window.confirm(`Clear all your feedback for ${candidateName}?`)) {
      return;
    }

    try {
      const response = await fetch('/clear-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          linkedin_url: linkedinUrl,
          recruiter_name: selectedRecruiter
        })
      });

      const data = await response.json();
      if (data.success) {
        // Clear local state
        setCandidateFeedback(prev => ({
          ...prev,
          [linkedinUrl]: { note: '' }
        }));
        // Reload feedback history
        await loadFeedbackHistory(linkedinUrl);
        showNotification(`Cleared feedback for ${candidateName}`);
      } else {
        showNotification('Failed to clear feedback', 'error');
      }
    } catch (error) {
      console.error('Error clearing feedback:', error);
      showNotification('Error clearing feedback', 'error');
    }
  };

  // Load feedback history for a candidate
  const loadFeedbackHistory = async (linkedinUrl) => {
    try {
      const response = await fetch(`/get-feedback/${encodeURIComponent(linkedinUrl)}`);
      const data = await response.json();
      if (data.success) {
        setFeedbackHistory(prev => ({
          ...prev,
          [linkedinUrl]: data.feedback
        }));
      }
    } catch (error) {
      console.error('Error loading feedback:', error);
    }
  };

  // Handle quick reason button click
  const handleQuickFeedback = async (linkedinUrl, feedbackType, reason) => {
    await saveFeedback(linkedinUrl, feedbackType, reason);

    // Don't hide input - allow multiple selections
    // Just reload feedback history to show the new feedback
    await loadFeedbackHistory(linkedinUrl);

    showNotification(`Feedback saved: ${reason}`);
  };

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

  // Handler for Crunchbase link clicks
  const handleCrunchbaseClick = async (clickData) => {
    const { companyId, companyName, crunchbaseUrl, source } = clickData;

    // Trusted sources (no modal needed): auto-verified or user-verified
    const trustedSources = ['coresignal', 'websearch_validated', 'user_verified'];

    if (trustedSources.includes(source)) {
      // Silent auto-verification in background
      try {
        const response = await fetch('/verify-crunchbase-url', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            companyId,
            isCorrect: true,
            verificationStatus: 'verified',
            correctedUrl: null,
            crunchbaseUrl  // Pass URL so backend can save it to company_data
          }),
        });

        if (response.ok) {
          console.log(`✅ Auto-verified ${source} URL for ${companyName}`);
        } else {
          console.error('Failed to auto-verify URL');
        }
      } catch (error) {
        console.error('Error auto-verifying URL:', error);
      }
      return; // Exit - no modal needed for trusted sources
    }

    // Uncertain sources: show validation modal for user review
    setValidationData({
      companyId,
      companyName,
      crunchbaseUrl,
      source,
      onRegenerate: () => handleRegenerateCrunchbaseUrl(companyName, companyId, crunchbaseUrl),
    });
    setValidationModalOpen(true);
  };

  // Handler for validation submission
  const handleValidation = async (validationPayload) => {
    try {
      const response = await fetch('/verify-crunchbase-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validationPayload),
      });

      if (!response.ok) {
        throw new Error('Failed to save verification');
      }

      const result = await response.json();
      console.log('✅ Verification saved:', result);

      // Update UI to reflect verification
      const companyId = validationPayload.companyId;
      const isCorrect = validationPayload.isCorrect;
      const newSource = isCorrect ? 'user_verified' : validationPayload.verificationStatus;

      // Update all candidate profiles that have this company
      const updateCompanySource = (candidates) => {
        return candidates.map(candidate => {
          if (!candidate.profileSummary?.experiences) return candidate;

          const updatedExperiences = candidate.profileSummary.experiences.map(exp => {
            if (exp.company_id === companyId && exp.company_enriched) {
              return {
                ...exp,
                company_enriched: {
                  ...exp.company_enriched,
                  crunchbase_source: newSource,
                  user_verified: isCorrect
                }
              };
            }
            return exp;
          });

          return {
            ...candidate,
            profileSummary: {
              ...candidate.profileSummary,
              experiences: updatedExperiences
            }
          };
        });
      };

      // Update all result arrays
      setSingleProfileResults(prev => updateCompanySource(prev));
      setBatchResults(prev => updateCompanySource(prev));
      setSavedAssessments(prev => updateCompanySource(prev));

      showNotification('Thank you for your feedback!', 'success');
    } catch (error) {
      console.error('Error saving verification:', error);
      showNotification('Failed to save verification', 'error');
      throw error;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFetchingProfile(true);
    setShowLoadingOverlay(true);
    setLoadingMessage('Processing profile...');
    setError('');
    setAssessment(null);
    setProfileSummary(null);

    try {
      // Clean the LinkedIn URL - remove trailing slash if present
      const cleanedUrl = linkedinUrl.trim().replace(/\/$/, '');
      
      // Step 1: Fetch profile data from CoreSignal API
      console.log('Fetching profile data for:', cleanedUrl);
      
      const fetchResponse = await fetch('/fetch-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          linkedin_url: cleanedUrl,
          use_realtime: useRealtimeData,
          enrich_companies: enrichCompanies,
          force_refresh: forceRefresh
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

      // Store raw CoreSignal JSON for inspection
      setRawCoreSignalData(fetchData);

      // Store enrichment summary if available
      if (fetchData.enrichment_summary) {
        setEnrichmentSummary(fetchData.enrichment_summary);
        console.log('Company enrichment summary:', fetchData.enrichment_summary);
      }

      setFetchingProfile(false);

      // Store profile WITHOUT AI analysis (on-demand only)
      const singleProfileResult = {
        type: 'single',
        name: fetchData.profile_summary?.full_name || 'Single Profile Assessment',
        headline: fetchData.profile_summary?.headline || 'N/A',
        score: 0, // No score yet, will be updated when AI analysis runs
        assessment: null, // No assessment yet, will be loaded on-demand
        profileSummary: fetchData.profile_summary,
        profile_data: { profile_data: fetchData.profile_data }, // Store raw profile data for work experience
        checked_at: fetchData.profile_summary?.checked_at,  // CoreSignal's last scrape
        last_fetched: fetchData.last_fetched,  // When WE cached this data (null if fresh from API)
        is_cached: !!fetchData.last_fetched,  // Flag if from cache
        success: true,
        url: cleanedUrl,
        timestamp: new Date().toISOString()
      };

      setSingleProfileResults(prev => [...prev, singleProfileResult]);
      setProfileSummary(fetchData.profile_summary);

      // If auto-generate is enabled, trigger AI analysis immediately
      if (autoGenerateAI) {
        handleGenerateAIAnalysis(cleanedUrl, fetchData.profile_data);
      }
    } catch (err) {
      setError('Network error. Please make sure the Flask server is running on port 5001.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
      setFetchingProfile(false);
      setShowLoadingOverlay(false);
    }
  };

  // On-demand AI Analysis (triggered when user opens accordion)
  const handleGenerateAIAnalysis = async (linkedinUrl, profileData) => {
    console.log('Generating AI analysis for:', linkedinUrl);

    // Mark as loading
    setAiAnalysisLoading(prev => ({ ...prev, [linkedinUrl]: true }));

    try {
      const response = await fetch('/assess-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile_data: profileData,
          user_prompt: userPrompt || 'Provide a general professional assessment',
          weighted_requirements: weightedRequirements
        })
      });

      const data = await response.json();

      if (data.success) {
        // Update the candidate with assessment data
        setSingleProfileResults(prev =>
          prev.map(c => c.url === linkedinUrl
            ? {
                ...c,
                assessment: data.assessment,
                score: data.assessment?.weighted_analysis?.weighted_score !== undefined
                  ? (typeof data.assessment.weighted_analysis.weighted_score === 'number' ? data.assessment.weighted_analysis.weighted_score : 0)
                  : (typeof data.assessment?.overall_score === 'number' ? data.assessment.overall_score : 0)
              }
            : c
          )
        );

        // Show success notification
        showNotification('✅ AI analysis ready!', 'success');
      } else {
        showNotification('❌ Failed to generate AI analysis', 'error');
        console.error('AI analysis error:', data.error);
      }
    } catch (error) {
      showNotification('❌ Network error while generating analysis', 'error');
      console.error('AI analysis network error:', error);
    } finally {
      // Clear loading state
      setAiAnalysisLoading(prev => ({ ...prev, [linkedinUrl]: false }));
    }
  };

  // Force refresh a profile from CoreSignal (uses API credits)
  const handleRefreshProfile = async (linkedinUrl) => {
    try {
      setShowLoadingOverlay(true);
      setLoadingMessage('Refreshing profile data from CoreSignal...\n\n(This will use 1 API credit)');

      const response = await fetch('/fetch-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          linkedin_url: linkedinUrl,
          force_refresh: true,  // Force fresh fetch
          enrich_companies: true
        })
      });

      const data = await response.json();

      if (data.success) {
        // Update the candidate in the results array
        setSingleProfileResults(prev => prev.map(candidate =>
          candidate.url === linkedinUrl
            ? {
                ...candidate,
                profileSummary: data.profile_summary,
                profile_data: { profile_data: data.profile_data },
                checked_at: data.profile_summary?.checked_at,
                last_fetched: null, // Fresh from API (not cached)
                is_cached: false,
                timestamp: new Date().toISOString()
              }
            : candidate
        ));

        showNotification('✅ Profile refreshed from CoreSignal!', 'success');
      } else {
        showNotification('❌ Failed to refresh profile', 'error');
      }
    } catch (error) {
      showNotification('❌ Network error during refresh', 'error');
    } finally {
      setShowLoadingOverlay(false);
    }
  };

  const handleRegenerateCrunchbaseUrl = async (companyName, companyId, currentUrl) => {
    try {
      // Don't show loading overlay - let the button handle its own loading state
      const response = await fetch('/regenerate-crunchbase-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: companyName,
          company_id: companyId,
          current_url: currentUrl
        })
      });

      const data = await response.json();

      if (data.success) {
        const newUrl = data.crunchbase_url;
        const newSource = data.crunchbase_source;
        const newConfidence = data.crunchbase_confidence;

        // Update all candidate profiles that have this company
        const updateCompanyUrl = (candidates) => {
          return candidates.map(candidate => {
            if (!candidate.profileSummary?.experiences) return candidate;

            const updatedExperiences = candidate.profileSummary.experiences.map(exp => {
              if (exp.company_id === companyId && exp.company_enriched) {
                return {
                  ...exp,
                  company_enriched: {
                    ...exp.company_enriched,
                    crunchbase_company_url: newUrl,
                    crunchbase_source: newSource,
                    crunchbase_confidence: newConfidence
                  }
                };
              }
              return exp;
            });

            return {
              ...candidate,
              profileSummary: {
                ...candidate.profileSummary,
                experiences: updatedExperiences
              }
            };
          });
        };

        // Update all result arrays
        setSingleProfileResults(prev => updateCompanyUrl(prev));
        setBatchResults(prev => updateCompanyUrl(prev));
        setSavedAssessments(prev => updateCompanyUrl(prev));

        const changeMessage = currentUrl !== newUrl
          ? `\n\nOld: ${currentUrl}\nNew: ${newUrl}`
          : '\n\n(URL unchanged, but validated!)';

        showNotification(
          `✅ Crunchbase URL updated for ${companyName}!${changeMessage}`,
          'success',
          8000  // Show for 8 seconds
        );
      } else {
        showNotification(`❌ Failed to regenerate URL: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error regenerating URL:', error);
      showNotification('❌ Network error during URL regeneration', 'error');
    }
    // No finally block - let CompanyTooltip handle its own loading state
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
    setShowLoadingOverlay(true);
    setLoadingMessage('Testing with sample profile...');
    setError('');
    setAssessment(null);
    setProfileSummary(null);

    try {
      console.log('Testing with dummy profile data...');
      
      // Use dummy profile data directly

      // Step 2: Assess the profile
      console.log('Assessing profile...');
      
      const assessResponse = await fetch('/assess-profile', {
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
        // Add the test profile result to the array instead of replacing
        const testProfileResult = {
          type: 'single',
          name: assessData.profile_summary?.full_name || 'Test Profile Assessment',
          headline: assessData.profile_summary?.headline || 'N/A',
          score: assessData.assessment?.weighted_analysis?.weighted_score !== undefined 
            ? (typeof assessData.assessment.weighted_analysis.weighted_score === 'number' ? assessData.assessment.weighted_analysis.weighted_score : 0)
            : (typeof assessData.assessment?.overall_score === 'number' ? assessData.assessment.overall_score : 0),
          assessment: assessData.assessment,
          profileSummary: assessData.profile_summary,
          success: true,
          url: 'Test Profile',
          timestamp: new Date().toISOString()
        };
        
        setSingleProfileResults(prev => [...prev, testProfileResult]);
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
      setShowLoadingOverlay(false);
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
          // Clean the URL - remove trailing slash if present
          const cleanedUrl = url.trim().replace(/\/$/, '');
          candidates.push({
            url: cleanedUrl,
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
    setShowLoadingOverlay(true);
    setError('');
    setBatchResults([]);

    try {
      const csvText = await csvFile.text();
      const candidates = parseCsv(csvText);
      
      const numCandidates = candidates.length;
      console.log(`🚀 Starting background assessment for ${numCandidates} candidates...`);
      
      setLoadingMessage(
        `Processing ${numCandidates} candidates...\n` +
        `Using high-concurrency processing for faster results`
      );
      
      // Process batch assessment directly with high concurrency
      const response = await fetch('/batch-assess-profiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          candidates: candidates,
          user_prompt: userPrompt || 'Provide a general professional assessment',
          weighted_requirements: weightedRequirements
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to process assessment: ${errorText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to process assessment');
      }

      const results = data.results;
      const summary = data.summary;
      
      console.log(`🎉 Assessment complete! Results: ${summary.successful}/${summary.total} successful, ${summary.failed} failed`);
      
      setBatchResults(results);
      
      if (summary.failed > 0) {
        showNotification(
          `Completed ${summary.successful}/${summary.total} assessments. ${summary.failed} failed.`,
          'warning'
        );
      } else {
        showNotification(
          `Successfully completed all ${summary.total} assessments!`,
          'success'
        );
      }
      
    } catch (err) {
      setError(`Error processing CSV: ${err.message}`);
      console.error('Error:', err);
    } finally {
      setBatchLoading(false);
      setShowLoadingOverlay(false);
    }
  };

  const resetToSingleMode = () => {
    setBatchMode(false);
    setSearchMode(false);
    setCsvFile(null);
    setBatchResults([]);
    setBatchLoading(false);
  };

  const handleProfileSearch = async () => {
    if (!searchPrompt.trim()) {
      setError('Please enter a search description');
      return;
    }

    setSearchLoading(true);
    setShowLoadingOverlay(true);
    setLoadingMessage('Searching for profiles...');
    setError('');

    try {
      console.log(`Searching for ${profileCount} profiles with prompt:`, searchPrompt);
      
      const response = await fetch('/search-profiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_prompt: searchPrompt,
          limit: profileCount
        }),
      });

      const data = await response.json();

      if (data.success) {
        console.log(`✅ Found ${data.total_found} profiles`);
        
        // Create a blob from the CSV data
        const blob = new Blob([data.csv_data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        // Create a download link and trigger it
        const link = document.createElement('a');
        link.href = url;
        link.download = `linkedin_search_results_${new Date().getTime()}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        showNotification(`Downloaded ${data.total_found} profiles as CSV!`, 'success');
      } else {
        setError(data.error || 'Failed to search profiles');
      }
    } catch (err) {
      setError('Network error. Please make sure the Flask server is running on port 5001.');
      console.error('Error:', err);
    } finally {
      setSearchLoading(false);
      setShowLoadingOverlay(false);
    }
  };

  const clearAllResults = () => {
    setSingleProfileResults([]);
    setBatchResults([]);
    setAssessment(null);
    setProfileSummary(null);
    setSavedAssessments([]);
  };

  const loadSavedAssessments = async () => {
    setLoadingSaved(true);
    try {
      const response = await fetch('/load-assessments?limit=100');
      const data = await response.json();
      
      if (data.success) {
        // Clear current session data and replace with database data
        setSingleProfileResults([]);
        setBatchResults([]);
        setSavedAssessments(data.assessments);
        console.log(`✅ Loaded ${data.count} saved assessments from database`);
      } else {
        setError(data.error || 'Failed to load saved assessments');
      }
    } catch (err) {
      setError('Network error loading saved assessments');
      console.error('Error:', err);
    } finally {
      setLoadingSaved(false);
    }
  };

  const saveCurrentAssessments = async () => {
    const allCurrentAssessments = [];
    
    // Add single profile results
    singleProfileResults.forEach(result => {
      allCurrentAssessments.push({
        linkedin_url: result.url,
        full_name: result.name,
        headline: result.headline,
        profile_data: result.profileSummary,
        assessment_data: result.assessment,
        assessment_type: 'single'
      });
    });
    
    // Add batch results
    batchResults.forEach(result => {
      if (result.assessment) {
        allCurrentAssessments.push({
          linkedin_url: result.url,
          full_name: result.csv_name || result.profile_data?.profile_data?.full_name || 'Unknown',
          headline: result.profile_data?.profile_data?.headline || 'N/A',
          profile_data: result.profile_data?.profile_data,
          assessment_data: result.assessment,
          assessment_type: 'batch'
        });
      }
    });
    
    if (allCurrentAssessments.length === 0) {
      setError('No assessments to save');
      return;
    }
    
    setSavingAssessments(true);
    try {
      // Save each assessment
      const savePromises = allCurrentAssessments.map(assessment => 
        fetch('/save-assessment', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(assessment)
        })
      );
      
      const results = await Promise.all(savePromises);
      const allSuccessful = results.every(result => result.ok);
      
      if (allSuccessful) {
        console.log(`✅ Saved ${allCurrentAssessments.length} assessments to database`);
        showNotification(`Saved ${allCurrentAssessments.length} assessment${allCurrentAssessments.length !== 1 ? 's' : ''} successfully!`, 'success');
        // Reload saved assessments to show the newly saved ones
        // loadSavedAssessments();
      } else {
        setError('Some assessments failed to save');
        showNotification('Failed to save some assessments', 'error');
      }
    } catch (err) {
      setError('Network error saving assessments');
      console.error('Error:', err);
      showNotification('Network error saving assessments', 'error');
    } finally {
      setSavingAssessments(false);
    }
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
        <div className="app-header">
          <h1>LinkedIn Profile AI Assessor</h1>
          <div className="recruiter-input-wrapper">
            <label htmlFor="recruiter-name">Recruiter:</label>
            <input
              id="recruiter-name"
              type="text"
              value={selectedRecruiter}
              onChange={(e) => setSelectedRecruiter(e.target.value)}
              placeholder="Enter your name..."
              className="recruiter-name-input"
            />
          </div>
        </div>
        <p className="description">
          {listsMode
            ? 'View and manage candidate lists created from the Chrome extension'
            : searchMode
            ? 'Search for LinkedIn profiles using natural language and download results as CSV'
            : batchMode
            ? 'Upload a CSV file with LinkedIn URLs for batch assessment'
            : 'Enter a LinkedIn profile URL and get an AI-powered assessment'}
        </p>

        <div className="mode-toggle">
          <button
            className={`mode-btn ${!batchMode && !searchMode && !listsMode && !jdAnalyzerMode && !companyResearchMode ? 'active' : ''}`}
            onClick={() => {
              setBatchMode(false);
              setSearchMode(false);
              setListsMode(false);
              setJdAnalyzerMode(false);
              setCompanyResearchMode(false);
            }}
          >
            Single Profile
          </button>
          <button
            className={`mode-btn ${searchMode ? 'active' : ''}`}
            onClick={() => {
              setSearchMode(true);
              setBatchMode(false);
              setListsMode(false);
              setJdAnalyzerMode(false);
              setCompanyResearchMode(false);
            }}
          >
            Profile Search
          </button>
          <button
            className={`mode-btn ${jdAnalyzerMode ? 'active' : ''}`}
            onClick={() => {
              setJdAnalyzerMode(true);
              setSearchMode(false);
              setBatchMode(false);
              setListsMode(false);
              setCompanyResearchMode(false);
            }}
          >
            JD Analyzer {activeJD && '(Active)'}
          </button>
          <button
            className={`mode-btn ${companyResearchMode ? 'active' : ''}`}
            onClick={() => {
              setCompanyResearchMode(true);
              setJdAnalyzerMode(false);
              setSearchMode(false);
              setBatchMode(false);
              setListsMode(false);
            }}
          >
            Company Research
          </button>
          <button
            className={`mode-btn ${batchMode && !searchMode ? 'active' : ''}`}
            onClick={() => {
              setBatchMode(true);
              setSearchMode(false);
              setListsMode(false);
              setJdAnalyzerMode(false);
              setCompanyResearchMode(false);
            }}
          >
            Batch Processing
          </button>
          <button
            className={`mode-btn ${listsMode ? 'active' : ''}`}
            onClick={() => {
              setListsMode(true);
              setBatchMode(false);
              setSearchMode(false);
              setJdAnalyzerMode(false);
              setCompanyResearchMode(false);
            }}
          >
            Lists
          </button>
        </div>

        {listsMode ? (
          <ListsView
            recruiterName={selectedRecruiter}
            showNotification={showNotification}
          />
        ) : jdAnalyzerMode ? (
          <div className="jd-analyzer-container">
            <div className="jd-analyzer-header">
              <h2>📋 JD Analyzer</h2>
              <p className="jd-analyzer-description">
                Transform job descriptions into weighted assessment criteria
              </p>
            </div>

            {/* Step 1: Input JD */}
            <div className="jd-input-section">
              <h3>Step 1: Paste Job Description</h3>
              <textarea
                className="jd-textarea"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the full job description here..."
                rows="12"
                disabled={jdAnalyzing}
              />
              <button
                className="jd-analyze-btn"
                onClick={async () => {
                  if (!jdText.trim()) {
                    showNotification('Please paste a job description', 'error');
                    return;
                  }

                  setJdAnalyzing(true);
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
                      setExtractedRequirements(data.weighted_requirements);
                      showNotification('Requirements extracted successfully!', 'success');
                    } else {
                      showNotification(`Error: ${data.error}`, 'error');
                    }
                  } catch (error) {
                    console.error('Error analyzing JD:', error);
                    showNotification('Failed to analyze job description', 'error');
                  } finally {
                    setJdAnalyzing(false);
                  }
                }}
                disabled={jdAnalyzing || !jdText.trim()}
              >
                {jdAnalyzing ? 'Analyzing...' : 'Analyze JD'}
              </button>

              <button
                className="llm-compare-btn"
                onClick={async () => {
                  if (!jdText.trim()) {
                    showNotification('Please paste a job description first', 'error');
                    return;
                  }

                  // Reset all results
                  setClaudeResult(null);
                  setGptResult(null);
                  setGeminiResult(null);
                  setSelectedLlmQuery(null);

                  // Set loading states immediately so button text changes
                  setClaudeLoading(true);
                  setGptLoading(true);
                  setGeminiLoading(true);

                  try {
                    // First, parse JD to get structured requirements
                    const parseResponse = await fetch('http://localhost:5001/api/jd/parse', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ jd_text: jdText })
                    });

                    const parseData = await parseResponse.json();

                    if (!parseData.success) {
                      showNotification(`Error parsing JD: ${parseData.error}`, 'error');
                      // Reset loading states on error
                      setClaudeLoading(false);
                      setGptLoading(false);
                      setGeminiLoading(false);
                      return;
                    }

                    const requestBody = {
                      jd_requirements: parseData.requirements,
                      preview_limit: 20
                    };

                    // Fire all 3 LLM API calls in parallel - each updates independently

                    // Claude
                    setClaudeLoading(true);
                    fetch('http://localhost:5001/api/jd/generate-query-claude', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(requestBody)
                    })
                      .then(res => res.json())
                      .then(data => {
                        if (data.success) setClaudeResult(data);
                      })
                      .catch(err => {
                        console.error('Claude error:', err);
                        setClaudeResult({
                          success: true,
                          model: 'Claude Haiku 4.5',
                          error: err.message,
                          query: null,
                          preview_profiles: [],
                          total_found: 0
                        });
                      })
                      .finally(() => setClaudeLoading(false));

                    // GPT
                    setGptLoading(true);
                    fetch('http://localhost:5001/api/jd/generate-query-gpt', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(requestBody)
                    })
                      .then(res => res.json())
                      .then(data => {
                        if (data.success) setGptResult(data);
                      })
                      .catch(err => {
                        console.error('GPT error:', err);
                        setGptResult({
                          success: true,
                          model: 'GPT-4o',
                          error: err.message,
                          query: null,
                          preview_profiles: [],
                          total_found: 0
                        });
                      })
                      .finally(() => setGptLoading(false));

                    // Gemini
                    setGeminiLoading(true);
                    fetch('http://localhost:5001/api/jd/generate-query-gemini', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(requestBody)
                    })
                      .then(res => res.json())
                      .then(data => {
                        if (data.success) setGeminiResult(data);
                      })
                      .catch(err => {
                        console.error('Gemini error:', err);
                        setGeminiResult({
                          success: true,
                          model: 'Gemini 2.0 Flash',
                          error: err.message,
                          query: null,
                          preview_profiles: [],
                          total_found: 0
                        });
                      })
                      .finally(() => setGeminiLoading(false));

                    showNotification('Generating queries from Claude Haiku, GPT-4o, and Gemini...', 'success');
                  } catch (error) {
                    console.error('Error comparing LLM queries:', error);
                    showNotification('Failed to start LLM comparison', 'error');
                    // Reset loading states on error
                    setClaudeLoading(false);
                    setGptLoading(false);
                    setGeminiLoading(false);
                  }
                }}
                disabled={claudeLoading || gptLoading || geminiLoading || !jdText.trim()}
              >
                {(claudeLoading || gptLoading || geminiLoading) ? 'Generating...' : 'Generate & Preview Queries (20 candidates each)'}
              </button>
            </div>

            {/* LLM Comparison Results - Tabbed Interface */}
            {(claudeResult || gptResult || geminiResult || claudeLoading || gptLoading || geminiLoading) && (
              <div className="llm-comparison-section">
                <h3>LLM Query Comparison</h3>
                <p className="section-description">
                  Compare queries generated by Claude Haiku 4.5, GPT-4o, and Gemini 2.0 Flash. Click tabs to switch models.
                </p>

                <div className="llm-comparison-grid">
                  {/* Horizontal Tab Headers */}
                  <div className="llm-tabs-header">
                    <button
                      className={`llm-tab-button ${activeLlmTab === 'claude' ? 'active' : ''}`}
                      onClick={() => setActiveLlmTab('claude')}
                    >
                      <span>Claude Haiku 4.5</span>
                      <span className="tab-badge claude">Anthropic</span>
                      {claudeLoading && <span className="loading-indicator"></span>}
                      {claudeResult && !claudeLoading && (
                        <span className="candidate-count">
                          {claudeResult.total_found || 0} candidates
                        </span>
                      )}
                    </button>

                    <button
                      className={`llm-tab-button ${activeLlmTab === 'gpt' ? 'active' : ''}`}
                      onClick={() => setActiveLlmTab('gpt')}
                    >
                      <span>GPT-4o</span>
                      <span className="tab-badge openai">OpenAI</span>
                      {gptLoading && <span className="loading-indicator"></span>}
                      {gptResult && !gptLoading && (
                        <span className="candidate-count">
                          {gptResult.total_found || 0} candidates
                        </span>
                      )}
                    </button>

                    <button
                      className={`llm-tab-button ${activeLlmTab === 'gemini' ? 'active' : ''}`}
                      onClick={() => setActiveLlmTab('gemini')}
                    >
                      <span>Gemini 2.0 Flash</span>
                      <span className="tab-badge google">Google</span>
                      {geminiLoading && <span className="loading-indicator"></span>}
                      {geminiResult && !geminiLoading && (
                        <span className="candidate-count">
                          {geminiResult.total_found || 0} candidates
                        </span>
                      )}
                    </button>
                  </div>

                  {/* Claude Card */}
                  {activeLlmTab === 'claude' && (
                    <div className={`llm-card ${selectedLlmQuery === 'claude' ? 'selected' : ''}`}>
                      {claudeLoading ? (
                        <div className="llm-loading">
                          <div className="spinner"></div>
                          <p>Claude Haiku 4.5 generating query...</p>
                        </div>
                      ) : claudeResult ? (
                        <>
                          {claudeResult.error && (
                            <div className="llm-error">
                              ❌ Error: {claudeResult.error}
                            </div>
                          )}

                          {claudeResult.query && (
                            <>
                              <div className="llm-stats">
                                <span className="stat-item">
                                  <strong>{claudeResult.total_found || 0}</strong> candidates found
                                </span>
                              </div>

                              <div className="llm-reasoning">
                                <strong>Strategy:</strong> {claudeResult.reasoning}
                              </div>

                              <details className="llm-query-details">
                                <summary>View Query JSON</summary>
                                <pre className="query-json">
                                  {JSON.stringify(claudeResult.query, null, 2)}
                                </pre>
                              </details>

                              {claudeResult.preview_profiles && claudeResult.preview_profiles.length > 0 && (
                                <div className="llm-preview-candidates">
                                  <strong>Preview (First {claudeResult.preview_profiles.length}):</strong>
                                  <div className="preview-list">
                                    {claudeResult.preview_profiles.map((profile, pIndex) => {
                                      const linkedinUrl = profile.linkedin_url || profile.professional_network_url || '';
                                      const headline = profile.headline || profile.generated_headline || 'No headline';
                                      const location = profile.location || profile.location_full || 'Location N/A';

                                      return (
                                        <div key={pIndex} className="preview-candidate">
                                          <div className="preview-name">
                                            {linkedinUrl ? (
                                              <a href={linkedinUrl} target="_blank" rel="noopener noreferrer" className="candidate-link">
                                                🔗 {profile.full_name}
                                              </a>
                                            ) : (
                                              <span className="no-link">❌ {profile.full_name}</span>
                                            )}
                                          </div>
                                          <div className="preview-headline">{headline}</div>
                                          <div className="preview-meta">
                                            📍 {location}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              <button
                                className={`select-query-btn ${selectedLlmQuery === 'claude' ? 'selected' : ''}`}
                                onClick={() => setSelectedLlmQuery('claude')}
                              >
                                {selectedLlmQuery === 'claude' ? 'Selected for Search' : 'Select This Query'}
                              </button>
                            </>
                          )}
                        </>
                      ) : (
                        <p style={{textAlign: 'center', color: '#999', padding: '40px'}}>
                          Click "Compare LLM Queries" to generate...
                        </p>
                      )}
                    </div>
                  )}

                  {/* GPT Card */}
                  {activeLlmTab === 'gpt' && (
                    <div className={`llm-card ${selectedLlmQuery === 'gpt' ? 'selected' : ''}`}>
                      {gptLoading ? (
                        <div className="llm-loading">
                          <div className="spinner"></div>
                          <p>GPT-4o generating query...</p>
                        </div>
                      ) : gptResult ? (
                        <>
                          {gptResult.error && (
                            <div className="llm-error">
                              ❌ Error: {gptResult.error}
                            </div>
                          )}

                          {gptResult.query && (
                            <>
                              <div className="llm-stats">
                                <span className="stat-item">
                                  <strong>{gptResult.total_found || 0}</strong> candidates found
                                </span>
                              </div>

                              <div className="llm-reasoning">
                                <strong>Strategy:</strong> {gptResult.reasoning}
                              </div>

                              <details className="llm-query-details">
                                <summary>View Query JSON</summary>
                                <pre className="query-json">
                                  {JSON.stringify(gptResult.query, null, 2)}
                                </pre>
                              </details>

                              {gptResult.preview_profiles && gptResult.preview_profiles.length > 0 && (
                                <div className="llm-preview-candidates">
                                  <strong>Preview (First {gptResult.preview_profiles.length}):</strong>
                                  <div className="preview-list">
                                    {gptResult.preview_profiles.map((profile, pIndex) => {
                                      const linkedinUrl = profile.linkedin_url || profile.professional_network_url || '';
                                      const headline = profile.headline || profile.generated_headline || 'No headline';
                                      const location = profile.location || profile.location_full || 'Location N/A';

                                      return (
                                        <div key={pIndex} className="preview-candidate">
                                          <div className="preview-name">
                                            {linkedinUrl ? (
                                              <a href={linkedinUrl} target="_blank" rel="noopener noreferrer" className="candidate-link">
                                                🔗 {profile.full_name}
                                              </a>
                                            ) : (
                                              <span className="no-link">❌ {profile.full_name}</span>
                                            )}
                                          </div>
                                          <div className="preview-headline">{headline}</div>
                                          <div className="preview-meta">
                                            📍 {location}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              <button
                                className={`select-query-btn ${selectedLlmQuery === 'gpt' ? 'selected' : ''}`}
                                onClick={() => setSelectedLlmQuery('gpt')}
                              >
                                {selectedLlmQuery === 'gpt' ? 'Selected for Search' : 'Select This Query'}
                              </button>
                            </>
                          )}
                        </>
                      ) : (
                        <p style={{textAlign: 'center', color: '#999', padding: '40px'}}>
                          Click "Compare LLM Queries" to generate...
                        </p>
                      )}
                    </div>
                  )}

                  {/* Gemini Card */}
                  {activeLlmTab === 'gemini' && (
                    <div className={`llm-card ${selectedLlmQuery === 'gemini' ? 'selected' : ''}`}>
                      {geminiLoading ? (
                        <div className="llm-loading">
                          <div className="spinner"></div>
                          <p>Gemini 2.0 Flash generating query...</p>
                        </div>
                      ) : geminiResult ? (
                        <>
                          {geminiResult.error && (
                            <div className="llm-error">
                              ❌ Error: {geminiResult.error}
                            </div>
                          )}

                          {geminiResult.query && (
                            <>
                              <div className="llm-stats">
                                <span className="stat-item">
                                  <strong>{geminiResult.total_found || 0}</strong> candidates found
                                </span>
                              </div>

                              <div className="llm-reasoning">
                                <strong>Strategy:</strong> {geminiResult.reasoning}
                              </div>

                              <details className="llm-query-details">
                                <summary>View Query JSON</summary>
                                <pre className="query-json">
                                  {JSON.stringify(geminiResult.query, null, 2)}
                                </pre>
                              </details>

                              {geminiResult.preview_profiles && geminiResult.preview_profiles.length > 0 && (
                                <div className="llm-preview-candidates">
                                  <strong>Preview (First {geminiResult.preview_profiles.length}):</strong>
                                  <div className="preview-list">
                                    {geminiResult.preview_profiles.map((profile, pIndex) => {
                                      const linkedinUrl = profile.linkedin_url || profile.professional_network_url || '';
                                      const headline = profile.headline || profile.generated_headline || 'No headline';
                                      const location = profile.location || profile.location_full || 'Location N/A';

                                      return (
                                        <div key={pIndex} className="preview-candidate">
                                          <div className="preview-name">
                                            {linkedinUrl ? (
                                              <a href={linkedinUrl} target="_blank" rel="noopener noreferrer" className="candidate-link">
                                                🔗 {profile.full_name}
                                              </a>
                                            ) : (
                                              <span className="no-link">❌ {profile.full_name}</span>
                                            )}
                                          </div>
                                          <div className="preview-headline">{headline}</div>
                                          <div className="preview-meta">
                                            📍 {location}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              <button
                                className={`select-query-btn ${selectedLlmQuery === 'gemini' ? 'selected' : ''}`}
                                onClick={() => setSelectedLlmQuery('gemini')}
                              >
                                {selectedLlmQuery === 'gemini' ? 'Selected for Search' : 'Select This Query'}
                              </button>
                            </>
                          )}
                        </>
                      ) : (
                        <p style={{textAlign: 'center', color: '#999', padding: '40px'}}>
                          Click "Compare LLM Queries" to generate...
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Search with selected query button */}
                {selectedLlmQuery && (
                  <div className="llm-action-section">
                    <button
                      className="search-with-selected-btn"
                      onClick={async () => {
                        const selectedResult = selectedLlmQuery === 'claude' ? claudeResult :
                                               selectedLlmQuery === 'gpt' ? gptResult : geminiResult;

                        setJdSearching(true);
                        try {
                          const response = await fetch(`http://localhost:5001/api/jd/search-candidates`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              query: selectedResult.query,
                              max_results: 100
                            })
                          });

                          const data = await response.json();
                          if (data.success) {
                            // Store results for in-app display
                            setJdFullResults(data.profiles);
                            setJdCsvData(data.csv_data);
                            setCurrentPage(1); // Reset to first page
                            showNotification(`Found ${data.total_found} candidates from ${selectedResult.model}!`, 'success');
                          } else {
                            showNotification(data.error || 'Failed to search candidates', 'error');
                          }
                        } catch (error) {
                          console.error('Error searching with selected query:', error);
                          showNotification('Failed to search with selected query', 'error');
                        } finally {
                          setJdSearching(false);
                        }
                      }}
                      disabled={jdSearching}
                    >
                      {jdSearching ? 'Fetching candidates...' : `Fetch All 100 Candidates (${selectedLlmQuery === 'claude' ? claudeResult?.model : selectedLlmQuery === 'gpt' ? gptResult?.model : geminiResult?.model})`}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Full Search Results Section */}
            {jdFullResults && jdFullResults.length > 0 && (
              <div className="jd-full-results-section">
                <div className="results-header">
                  <h3>Search Results ({jdFullResults.length} candidates)</h3>
                  <div className="results-actions">
                    <button
                      className="download-csv-btn"
                      onClick={() => {
                        if (jdCsvData) {
                          const blob = new Blob([jdCsvData], { type: 'text/csv' });
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          const selectedResult = selectedLlmQuery === 'claude' ? claudeResult :
                                                 selectedLlmQuery === 'gpt' ? gptResult : geminiResult;
                          a.download = `${selectedResult?.model || 'candidates'}_${Date.now()}.csv`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          window.URL.revokeObjectURL(url);
                          showNotification('CSV downloaded successfully!', 'success');
                        }
                      }}
                    >
                      Download CSV
                    </button>
                    <button
                      className="clear-results-btn"
                      onClick={() => {
                        setJdFullResults(null);
                        setJdCsvData(null);
                        setCurrentPage(1); // Reset page
                      }}
                    >
                      Clear Results
                    </button>
                  </div>
                </div>

                {/* Pagination Controls */}
                <div className="pagination-controls">
                  <div className="pagination-info">
                    Showing {Math.min((currentPage - 1) * 20 + 1, jdFullResults.length)} - {Math.min(currentPage * 20, jdFullResults.length)} of {jdFullResults.length} candidates
                  </div>
                  <div className="pagination-buttons">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="pagination-btn"
                    >
                      ← Previous
                    </button>
                    <span className="pagination-pages">
                      Page {currentPage} of {Math.ceil(jdFullResults.length / 20)}
                    </span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(Math.ceil(jdFullResults.length / 20), prev + 1))}
                      disabled={currentPage >= Math.ceil(jdFullResults.length / 20)}
                      className="pagination-btn"
                    >
                      Next →
                    </button>
                  </div>
                </div>

                <div className="results-grid">
                  {jdFullResults
                    .slice((currentPage - 1) * 20, currentPage * 20)
                    .map((profile, idx) => {
                      const linkedinUrl = profile.linkedin_url || profile.professional_network_url || '';
                      const headline = profile.headline || profile.generated_headline || 'No headline';
                      const location = profile.location || profile.location_full || 'Location N/A';
                      const currentTitle = profile.current_title || profile.active_experience_title || '';
                      const company = profile.company_name || profile.active_experience_company || '';
                      const globalIdx = (currentPage - 1) * 20 + idx;

                      return (
                        <div
                          key={globalIdx}
                          className="result-candidate-card"
                          onMouseEnter={(e) => {
                            setHoveredProfile(profile);
                            const rect = e.currentTarget.getBoundingClientRect();
                            setTooltipPosition({
                              x: rect.right + 10,
                              y: rect.top
                            });
                          }}
                          onMouseLeave={() => setHoveredProfile(null)}
                        >
                          <div className="result-candidate-header">
                            {linkedinUrl ? (
                              <a
                                href={linkedinUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="result-candidate-name"
                              >
                                🔗 {profile.full_name || 'Unknown'}
                              </a>
                            ) : (
                              <span className="result-candidate-name no-link">❌ {profile.full_name || 'Unknown'}</span>
                            )}
                          </div>
                          <div className="result-candidate-headline">{headline}</div>
                          <div className="result-candidate-meta">
                            📍 {location}
                          </div>
                          {currentTitle && (
                            <div className="result-candidate-title">
                              💼 {currentTitle}{company ? ` at ${company}` : ''}
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>

                {/* Tooltip */}
                {hoveredProfile && (
                  <div
                    className="profile-tooltip"
                    style={{
                      position: 'fixed',
                      left: `${tooltipPosition.x}px`,
                      top: `${tooltipPosition.y}px`,
                      zIndex: 10000
                    }}
                  >
                    <div className="tooltip-header">
                      <strong>{hoveredProfile.full_name || 'Unknown'}</strong>
                    </div>
                    <div className="tooltip-body">
                      <div className="tooltip-section">
                        <div className="tooltip-label">Current Role:</div>
                        <div className="tooltip-value">
                          {hoveredProfile.active_experience_title || hoveredProfile.current_title || 'N/A'}
                        </div>
                      </div>
                      <div className="tooltip-section">
                        <div className="tooltip-label">Company:</div>
                        <div className="tooltip-value">
                          {hoveredProfile.company_name || hoveredProfile.active_experience_company || 'N/A'}
                        </div>
                      </div>
                      <div className="tooltip-section">
                        <div className="tooltip-label">Location:</div>
                        <div className="tooltip-value">
                          {hoveredProfile.location_full || hoveredProfile.location || 'N/A'}
                        </div>
                      </div>
                      {hoveredProfile.active_experience_industry && (
                        <div className="tooltip-section">
                          <div className="tooltip-label">Industry:</div>
                          <div className="tooltip-value">{hoveredProfile.active_experience_industry}</div>
                        </div>
                      )}
                      {hoveredProfile.management_level && (
                        <div className="tooltip-section">
                          <div className="tooltip-label">Management Level:</div>
                          <div className="tooltip-value">{hoveredProfile.management_level}</div>
                        </div>
                      )}
                      {hoveredProfile.inferred_skills && hoveredProfile.inferred_skills.length > 0 && (
                        <div className="tooltip-section">
                          <div className="tooltip-label">Skills:</div>
                          <div className="tooltip-value">
                            {hoveredProfile.inferred_skills.slice(0, 5).join(', ')}
                            {hoveredProfile.inferred_skills.length > 5 && '...'}
                          </div>
                        </div>
                      )}
                      {hoveredProfile.connection_count && (
                        <div className="tooltip-section">
                          <div className="tooltip-label">Connections:</div>
                          <div className="tooltip-value">{hoveredProfile.connection_count.toLocaleString()}</div>
                        </div>
                      )}
                      {hoveredProfile.follower_count && (
                        <div className="tooltip-section">
                          <div className="tooltip-label">Followers:</div>
                          <div className="tooltip-value">{hoveredProfile.follower_count.toLocaleString()}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 2: Review & Edit Requirements */}
            {extractedRequirements.length > 0 && (
              <div className="jd-requirements-section">
                <h3>Step 2: Review & Adjust Requirements</h3>
                <p className="section-description">
                  AI extracted {extractedRequirements.length} requirements. Adjust weights as needed.
                </p>

                <div className="requirements-list">
                  {extractedRequirements.map((req, index) => (
                    <div key={index} className="requirement-card">
                      <div className="requirement-header">
                        <span className="requirement-number">{index + 1}.</span>
                        <input
                          type="text"
                          className="requirement-name"
                          value={req.requirement}
                          onChange={(e) => {
                            const newReqs = [...extractedRequirements];
                            newReqs[index].requirement = e.target.value;
                            setExtractedRequirements(newReqs);
                          }}
                        />
                        <input
                          type="number"
                          className="requirement-weight"
                          value={req.weight}
                          min="0"
                          max="100"
                          onChange={(e) => {
                            const newReqs = [...extractedRequirements];
                            newReqs[index].weight = parseInt(e.target.value) || 0;
                            setExtractedRequirements(newReqs);
                          }}
                        />
                        <span className="weight-label">%</span>
                        <button
                          className="remove-req-btn"
                          onClick={() => {
                            setExtractedRequirements(extractedRequirements.filter((_, i) => i !== index));
                          }}
                        >
                          ×
                        </button>
                      </div>
                      {req.description && (
                        <p className="requirement-description">{req.description}</p>
                      )}
                    </div>
                  ))}

                  <div className="requirement-card general-fit">
                    <div className="requirement-header">
                      <span className="requirement-number">⚪</span>
                      <span className="requirement-name">General Fit (auto-calculated)</span>
                      <span className="requirement-weight">
                        {100 - extractedRequirements.reduce((sum, req) => sum + (req.weight || 0), 0)}
                      </span>
                      <span className="weight-label">%</span>
                    </div>
                    <p className="requirement-description">
                      Overall alignment with role, cultural fit, communication skills
                    </p>
                  </div>
                </div>

                <div className="total-weight">
                  Total: {extractedRequirements.reduce((sum, req) => sum + (req.weight || 0), 0) +
                    (100 - extractedRequirements.reduce((sum, req) => sum + (req.weight || 0), 0))}%
                  {extractedRequirements.reduce((sum, req) => sum + (req.weight || 0), 0) === 100 ?
                    ' (Warning: No room for General Fit)' : ''}
                </div>
              </div>
            )}

            {/* Step 3: Activate */}
            {extractedRequirements.length > 0 && (
              <div className="jd-activate-section">
                <h3>Step 3: Name & Activate</h3>
                <div className="jd-title-input">
                  <label htmlFor="jdTitle">JD Title (optional):</label>
                  <input
                    id="jdTitle"
                    type="text"
                    value={jdTitle}
                    onChange={(e) => setJdTitle(e.target.value)}
                    placeholder="e.g., Senior PM - Fintech"
                  />
                </div>

                <div className="jd-actions">
                  <button
                    className="activate-jd-btn"
                    onClick={() => {
                      const jdData = {
                        title: jdTitle || 'Untitled JD',
                        requirements: extractedRequirements.map(req => ({
                          id: Date.now() + Math.random(),
                          text: req.requirement,
                          weight: req.weight,
                          description: req.description,
                          scoring_criteria: req.scoring_criteria
                        })),
                        timestamp: Date.now()
                      };

                      setActiveJD(jdData);
                      setWeightedRequirements(jdData.requirements);
                      localStorage.setItem('activeJD', JSON.stringify(jdData));
                      showNotification(`JD "${jdData.title}" activated for all assessments!`, 'success');
                    }}
                  >
                    Set as Active JD
                  </button>

                  <button
                    className="search-candidates-btn"
                    onClick={async () => {
                      if (!jdText.trim()) {
                        showNotification('Please provide a job description first', 'error');
                        return;
                      }

                      setJdSearching(true);
                      try {
                        // First, parse JD to get structured requirements
                        const parseResponse = await fetch('http://localhost:5001/api/jd/parse', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ jd_text: jdText })
                        });

                        const parseData = await parseResponse.json();

                        if (!parseData.success) {
                          showNotification(`Error parsing JD: ${parseData.error}`, 'error');
                          return;
                        }

                        // Now search CoreSignal with parsed requirements
                        const searchResponse = await fetch('http://localhost:5001/api/jd/search-candidates', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            jd_requirements: parseData.requirements,
                            max_results: 100
                          })
                        });

                        const searchData = await searchResponse.json();

                        if (searchData.success) {
                          setJdSearchResults(searchData);

                          // Download CSV
                          const blob = new Blob([searchData.csv_data], { type: 'text/csv' });
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `jd_search_${jdTitle || 'results'}_${Date.now()}.csv`;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          window.URL.revokeObjectURL(url);

                          showNotification(`Found ${searchData.total_found} matching candidates! CSV downloaded.`, 'success');
                        } else {
                          showNotification(`Error: ${searchData.error}`, 'error');
                        }
                      } catch (error) {
                        console.error('Error searching candidates:', error);
                        showNotification('Failed to search for candidates', 'error');
                      } finally {
                        setJdSearching(false);
                      }
                    }}
                    disabled={jdSearching || !jdText.trim()}
                  >
                    {jdSearching ? 'Searching CoreSignal...' : 'Search Candidates'}
                  </button>

                  <button
                    className="clear-jd-btn"
                    onClick={() => {
                      setJdText('');
                      setExtractedRequirements([]);
                      setJdTitle('');
                      setJdSearchResults(null);
                    }}
                  >
                    Clear
                  </button>
                </div>

                <p className="activation-note">
                  💡 Once activated, these requirements will be used for all profile assessments
                  in Single Profile and Batch modes until you clear or change them.
                </p>
              </div>
            )}
          </div>
        ) : companyResearchMode ? (
          <div className="company-research-container">
            <div className="company-research-header">
              <h2>🏢 Company Research Agent</h2>
              <p className="company-research-description">
                Discover companies where the best candidates for your role currently work
              </p>
            </div>

            {/* Step 1: Input JD */}
            <div className="company-jd-input-section">
              <h3>Step 1: Paste Job Description</h3>
              <textarea
                className="company-jd-textarea"
                value={companyJdText}
                onChange={(e) => setCompanyJdText(e.target.value)}
                placeholder="Paste the full job description here..."
                rows="12"
                disabled={companyResearching}
              />
              <button
                className="company-research-btn"
                onClick={async () => {
                  if (!companyJdText.trim()) {
                    showNotification('Please paste a job description', 'error');
                    return;
                  }

                  setCompanyResearching(true);
                  try {
                    // Step 1: Parse JD to extract structured requirements
                    showNotification('Analyzing job description...', 'info');

                    const parseResponse = await fetch('http://localhost:5001/api/jd/parse', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ jd_text: companyJdText })
                    });

                    if (!parseResponse.ok) {
                      throw new Error('Failed to parse job description');
                    }

                    const parseData = await parseResponse.json();
                    console.log('Parsed JD:', parseData);

                    // Step 2: Extract company mentions from JD text
                    // More robust extraction: find ALL capitalized names that look like companies
                    const mentionedCompanies = [];

                    // Pattern 1: After trigger phrases like "companies like X, Y, and Z"
                    const triggerPhrases = [
                      /(?:companies like|similar to|work at|admire companies|companies such as|examples include)\s+([^.]+)/gi,
                      /(?:experience at)\s+([A-Z][a-z]+(?:[A-Z][a-z]+)?)/g
                    ];

                    triggerPhrases.forEach(regex => {
                      let match;
                      while ((match = regex.exec(companyJdText)) !== null) {
                        const phrase = match[1];
                        // Extract individual company names from comma/and-separated list
                        const companyNames = phrase.split(/,|\s+and\s+|\s+or\s+/)
                          .map(s => s.trim())
                          .filter(s => s.length > 0 && /^[A-Z]/.test(s))  // Must start with capital
                          .map(s => s.replace(/[^a-zA-Z\s]/g, '').trim())  // Remove punctuation
                          .filter(s => s.length > 2);  // At least 3 chars

                        mentionedCompanies.push(...companyNames);
                      }
                    });

                    // Deduplicate and clean
                    const uniqueCompanies = [...new Set(mentionedCompanies)]
                      .filter(c => c && c.length >= 3)
                      .slice(0, 10);  // Limit to 10 companies

                    // Step 3: Build structured research request
                    // Note: For competitive intelligence, we don't filter by company stage
                    // We want ALL competitors regardless of funding stage
                    const jdData = {
                      title: parseData.role_title || "Engineering Role",
                      company: "YourCompany",
                      company_stage: parseData.company_stage || "",  // Use actual company stage from JD, not seniority level
                      industries: parseData.domain_expertise && parseData.domain_expertise.length > 0
                                  ? parseData.domain_expertise
                                  : ["tech"],
                      requirements: {
                        technical_skills: parseData.technical_skills || [],
                        domain: parseData.domain_expertise && parseData.domain_expertise[0]
                                ? parseData.domain_expertise[0]
                                : "technology"
                      },
                      target_companies: {
                        mentioned_companies: uniqueCompanies.length > 0
                                            ? uniqueCompanies
                                            : [],
                        industry_context: parseData.domain_expertise
                                          ? parseData.domain_expertise.join(" ")
                                          : "tech"
                      }
                    };

                    console.log('Research request:', jdData);
                    showNotification('Starting company research...', 'info');

                    // Step 4: Start company research
                    const response = await fetch('http://localhost:5001/research-companies', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        jd_data: jdData,
                        config: {
                          max_companies: 50,
                          min_relevance_score: 5.0,
                          use_gpt5_deep_research: true
                        }
                      })
                    });

                    const data = await response.json();

                    if (data.success) {
                      setCompanySessionId(data.session_id);
                      setCompanyResearchStatus({ status: 'running', progress_percentage: 0 });
                      showNotification('Company research started!', 'success');

                      // Use Server-Sent Events for real-time streaming
                      const eventSource = new EventSource(`http://localhost:5001/research-companies/${data.session_id}/stream`);

                      eventSource.onmessage = async (event) => {
                        const streamData = JSON.parse(event.data);

                        if (streamData.error) {
                          console.error('Stream error:', streamData.error);
                          eventSource.close();
                          showNotification('Stream error: ' + streamData.error, 'error');
                          setCompanyResearching(false);
                          return;
                        }

                        if (streamData.success && streamData.session) {
                          setCompanyResearchStatus(streamData.session);

                          if (streamData.session.status === 'completed') {
                            eventSource.close();
                            // Fetch results
                            const resultsResponse = await fetch(`http://localhost:5001/research-companies/${data.session_id}/results`);
                            const resultsData = await resultsResponse.json();

                            if (resultsData.success) {
                              setCompanyResearchResults(resultsData.results);
                              showNotification('Research completed!', 'success');
                            }
                            setCompanyResearching(false);
                          } else if (streamData.session.status === 'failed') {
                            eventSource.close();
                            showNotification('Research failed: ' + streamData.session.error_message, 'error');
                            setCompanyResearching(false);
                          }
                        }
                      };

                      eventSource.onerror = (error) => {
                        console.error('EventSource error:', error);
                        eventSource.close();
                        showNotification('Connection error. Please try again.', 'error');
                        setCompanyResearching(false);
                      };
                    } else {
                      showNotification('Failed to start research: ' + data.error, 'error');
                      setCompanyResearching(false);
                    }
                  } catch (error) {
                    showNotification('Error: ' + error.message, 'error');
                    setCompanyResearching(false);
                  }
                }}
                disabled={companyResearching || !companyJdText.trim()}
              >
                {companyResearching ? 'Researching...' : 'Start Research'}
              </button>
            </div>

            {/* Progress Indicator */}
            {companyResearchStatus && (
              <div className="research-status-section">
                <h3>Research Progress</h3>

                {/* Phase Indicators */}
                <div className="phase-indicators">
                  <div className={`phase-item ${
                    companyResearchStatus.search_config?.current_phase === 'discovery' ? 'active' :
                    ['screening', 'deep_research'].includes(companyResearchStatus.search_config?.current_phase) ? 'completed' : ''
                  }`}>
                    <span className="phase-icon">{
                      ['screening', 'deep_research'].includes(companyResearchStatus.search_config?.current_phase) ? '✓' : '1'
                    }</span>
                    <span className="phase-label">Discovery</span>
                  </div>
                  <div className="phase-divider"></div>
                  <div className={`phase-item ${
                    companyResearchStatus.search_config?.current_phase === 'screening' ? 'active' :
                    companyResearchStatus.search_config?.current_phase === 'deep_research' ? 'completed' : ''
                  }`}>
                    <span className="phase-icon">{
                      companyResearchStatus.search_config?.current_phase === 'deep_research' ? '✓' : '2'
                    }</span>
                    <span className="phase-label">Screening</span>
                  </div>
                  <div className="phase-divider"></div>
                  <div className={`phase-item ${
                    companyResearchStatus.search_config?.current_phase === 'deep_research' ? 'active' : ''
                  }`}>
                    <span className="phase-icon">3</span>
                    <span className="phase-label">Deep Research</span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${companyResearchStatus.progress_percentage || 0}%` }}
                  />
                </div>

                {/* Current Action */}
                {companyResearchStatus.search_config?.current_action && (
                  <div className="current-action">
                    <span className="spinner"></span>
                    <span>{companyResearchStatus.search_config.current_action}</span>
                  </div>
                )}

                {/* Metrics */}
                <div className="research-metrics">
                  {companyResearchStatus.total_discovered > 0 && (
                    <span className="metric">
                      <strong>Discovered:</strong> {companyResearchStatus.total_discovered}
                    </span>
                  )}
                  {companyResearchStatus.total_evaluated > 0 && (
                    <span className="metric">
                      <strong>Evaluated:</strong> {companyResearchStatus.total_evaluated}
                    </span>
                  )}
                  {companyResearchStatus.total_selected > 0 && (
                    <span className="metric">
                      <strong>Selected:</strong> {companyResearchStatus.total_selected}
                    </span>
                  )}
                </div>

                {/* Discovered Companies List */}
                {companyResearchStatus.search_config?.discovered_companies &&
                 companyResearchStatus.search_config.discovered_companies.length > 0 && (
                  <div className="discovered-companies">
                    <h4>Companies Found:</h4>
                    <div className="company-chips">
                      {companyResearchStatus.search_config.discovered_companies.slice(0, 15).map((name, idx) => (
                        <span key={idx} className="company-chip">{name}</span>
                      ))}
                      {companyResearchStatus.search_config.discovered_companies.length > 15 && (
                        <span className="company-chip more">
                          +{companyResearchStatus.search_config.discovered_companies.length - 15} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Results Display */}
            {companyResearchResults && (
              <div className="research-results-section">
                <div className="results-header">
                  <h3>Research Results</h3>
                  <button
                    className="export-csv-btn"
                    onClick={async () => {
                      const response = await fetch(`http://localhost:5001/research-companies/${companySessionId}/export-csv`);
                      const data = await response.json();
                      if (data.success) {
                        const blob = new Blob([data.csv_data], { type: 'text/csv' });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = data.filename;
                        a.click();
                        showNotification('CSV exported!', 'success');
                      }
                    }}
                  >
                    Export CSV
                  </button>
                </div>

                <div className="results-summary">
                  <p>Total Companies: {companyResearchResults.summary.total_companies}</p>
                  <p>Average Score: {companyResearchResults.summary.avg_relevance_score}</p>
                  <p>Top Company: {companyResearchResults.summary.top_company}</p>
                </div>

                {Object.entries(companyResearchResults.companies_by_category).map(([category, companies]) => (
                  companies.length > 0 && (
                    <div key={category} className="category-section">
                      <h4>{category.replace('_', ' ').toUpperCase()} ({companies.length})</h4>
                      <div className="company-cards">
                        {companies.map((company, idx) => (
                          <div key={idx} className="company-card">
                            <div className="company-header">
                              <h5>{company.company_name}</h5>
                              <span className="score-badge">{company.relevance_score}/10</span>
                            </div>
                            <p className="reasoning">{company.relevance_reasoning}</p>
                            <div className="company-meta">
                              <span>{company.industry}</span>
                              {company.employee_count && <span>{company.employee_count} employees</span>}
                              {company.funding_stage && <span>{company.funding_stage}</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                ))}
              </div>
            )}
          </div>
        ) : searchMode ? (
          <div className="search-form">
            <div className="form-group">
              <label htmlFor="searchPrompt">Describe the candidate you're looking for:</label>
              <textarea
                id="searchPrompt"
                value={searchPrompt}
                onChange={(e) => setSearchPrompt(e.target.value)}
                placeholder="e.g., 'Find me a technical leader with AI/ML experience based in the United States' or 'Looking for a sales director in healthcare based in New York'"
                rows="4"
                required
              />
              <p className="file-help">
                Use natural language to describe the role, location, industry, skills, or experience you're looking for. 
                The AI will find matching profiles and download them as a CSV file.
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="profileCount">Number of profiles:</label>
              <input
                id="profileCount"
                type="number"
                min="20"
                max="100"
                step="20"
                value={profileCount}
                onChange={(e) => setProfileCount(Math.min(100, parseInt(e.target.value) || 20))}
                className="profile-count-input"
              />
              <p className="file-help">
                Enter 20, 40, 60, 80, or 100 profiles.
              </p>
            </div>

            <div className="button-group">
              <button 
                type="button" 
                onClick={handleProfileSearch}
                className="submit-btn search-btn-text" 
                disabled={searchLoading || !searchPrompt.trim()}
              >
                {searchLoading ? 'Searching...' : (
                  <>
                    <span>Search Profiles</span>
                    <span className="btn-subtitle">(Download CSV)</span>
                  </>
                )}
              </button>
              
            </div>
          </div>
        ) : !batchMode ? (
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
            </div>

          <div className="form-group">
            <label htmlFor="userPrompt">Assessment Criteria (Optional):</label>
            <textarea
              id="userPrompt"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Describe the role, ideal candidate profile, and any must-have skills or experiences (e.g., domain knowledge, fundraising, product strategy)"
              rows="5"
            />
          </div>

          <div className="form-group">
            <div className="accordion-header" onClick={() => setShowWeightedRequirements(!showWeightedRequirements)}>
              <label>Advanced: Custom Weighted Requirements</label>
              <span className="accordion-toggle">{showWeightedRequirements ? '−' : '+'}</span>
            </div>
            {showWeightedRequirements && (
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
            )}
          </div>

          {/* HIDDEN: Company Enrichment Toggle - Keep code for future use */}
          {false && (
          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={enrichCompanies}
                onChange={(e) => setEnrichCompanies(e.target.checked)}
                className="enrichment-checkbox"
              />
              <span className="checkbox-text">
                <strong>🏢 Enable Deep Dive Company Research</strong>
                <span className="checkbox-description">
                  Fetch detailed company data (funding, stage, growth signals) for each experience.
                  {enrichCompanies && <span className="cost-note"> +{enrichCompanies ? '~5-10 credits per profile' : ''}</span>}
                </span>
              </span>
            </label>
          </div>
          )}

          {/* Force Refresh Toggle */}
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
                className="enrichment-checkbox"
              />
              <span className="checkbox-text">
                <strong>
                  <TbRefresh style={{marginRight: '8px', verticalAlign: 'middle'}} size={16} />
                  Force Refresh Data
                </strong>
                <span className="checkbox-description">
                  Bypass stored data and fetch fresh profile from CoreSignal (uses 1 credit even if stored).
                  {forceRefresh && <span className="cost-note"> ⚠️ Will use API credits</span>}
                </span>
              </span>
            </label>
          </div>

          {/* HIDDEN: Auto-Generate AI Analysis Toggle - Keep code for future use */}
          {false && (
          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={autoGenerateAI}
                onChange={(e) => setAutoGenerateAI(e.target.checked)}
                className="enrichment-checkbox"
              />
              <span className="checkbox-text">
                <strong>🤖 Auto-Generate AI Analysis</strong>
                <span className="checkbox-description">
                  Automatically run AI analysis after fetching profile (adds 10-15 seconds).
                  {autoGenerateAI && <span className="cost-note"> ⚠️ +$0.01-0.02 per profile</span>}
                </span>
              </span>
            </label>
          </div>
          )}

          <div className="button-group">
            <button
              type="submit"
              className="submit-btn"
              disabled={loading || !linkedinUrl.trim()}
            >
              {fetchingProfile ? 'Fetching Profile...' : loading ? 'Analyzing Profile...' : autoGenerateAI ? 'Fetch & Analyze Profile' : 'Fetch Profile'}
            </button>

            {rawCoreSignalData && (
              <button
                type="button"
                onClick={() => setShowRawJSON(!showRawJSON)}
                className="secondary-btn"
              >
                {showRawJSON ? 'Hide Raw JSON' : 'View Raw CoreSignal JSON'}
              </button>
            )}
          </div>

          {/* Company Enrichment Summary */}
          {enrichmentSummary && (
            <div className="enrichment-summary">
              <h4>🏢 Company Intelligence Summary</h4>
              <div className="enrichment-stats">
                <div className="enrichment-stat">
                  <strong>Total Companies:</strong>
                  <span className="enrichment-stat-value">{enrichmentSummary.total_experiences}</span>
                </div>
                <div className="enrichment-stat">
                  <strong>Enriched:</strong>
                  <span className="enrichment-stat-value">{enrichmentSummary.companies_enriched}</span>
                </div>
                <div className="enrichment-stat">
                  <strong>API Calls:</strong>
                  <span className="enrichment-stat-value">{enrichmentSummary.api_calls_made}</span>
                </div>
                <div className="enrichment-stat">
                  <strong>From Cache:</strong>
                  <span className="enrichment-stat-value">{enrichmentSummary.companies_cached}</span>
                </div>
                {enrichmentSummary.companies_failed > 0 && (
                  <div className="enrichment-stat">
                    <strong>Failed:</strong>
                    <span className="enrichment-stat-value" style={{color: '#d32f2f'}}>{enrichmentSummary.companies_failed}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Raw JSON Display */}
          {showRawJSON && rawCoreSignalData && (
            <div style={{
              marginTop: '20px',
              padding: '20px',
              backgroundColor: '#fff',
              borderRadius: '8px',
              border: '2px solid #4a90e2',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{
                marginTop: 0,
                marginBottom: '15px',
                color: '#2c3e50',
                fontSize: '18px',
                fontWeight: '600'
              }}>
                CoreSignal API Response
              </h3>
              <JsonView
                value={rawCoreSignalData}
                collapsed={1}
                displayDataTypes={false}
                style={{
                  backgroundColor: '#f8f9fa',
                  borderRadius: '6px',
                  padding: '15px',
                  fontSize: '13px',
                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                  maxHeight: '600px',
                  overflow: 'auto'
                }}
              />
            </div>
          )}
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
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="batchUserPrompt">Assessment Criteria (Optional):</label>
              <textarea
                id="batchUserPrompt"
                value={userPrompt}
                onChange={(e) => setUserPrompt(e.target.value)}
                placeholder="Describe the role, ideal candidate profile, and any must-have skills or experiences (e.g., domain knowledge, fundraising, product strategy)"
                rows="5"
              />
            </div>

            <div className="form-group">
              <div className="accordion-header" onClick={() => setShowWeightedRequirements(!showWeightedRequirements)}>
                <label>Advanced: Custom Weighted Requirements</label>
                <span className="accordion-toggle">{showWeightedRequirements ? '−' : '+'}</span>
              </div>
              {showWeightedRequirements && (
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
              )}
            </div>

            <div className="button-group">
              <button 
                type="button" 
                onClick={handleBatchProcess}
                className="submit-btn" 
                disabled={!csvFile || batchLoading}
              >
                {batchLoading ? 'Assessing Candidates...' : 'Assess Candidates'}
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


        {/* Combined Results Panel - Always Visible */}
        {(() => {
          // Create unified list of all candidates and sort by weighted score
          const allCandidates = [];
          
          // Add all single profile results
          singleProfileResults.forEach((result, index) => {
            allCandidates.push({
              ...result,
              rank: 0, // Will be updated after sorting
              originalIndex: index,
              checked_at: result.profileSummary?.checked_at  // Extract freshness timestamp for badge
            });
          });
          
          // Add batch results
          batchResults.forEach((result, index) => {
            const batchScore = result.assessment?.weighted_analysis?.weighted_score !== undefined 
              ? (typeof result.assessment.weighted_analysis.weighted_score === 'number' ? result.assessment.weighted_analysis.weighted_score : 0)
              : (typeof result.assessment?.overall_score === 'number' ? result.assessment.overall_score : 0);
            
            allCandidates.push({
              type: 'batch',
              rank: 0, // Will be updated after sorting
              name: result.csv_name || result.profile_data?.profile_data?.full_name || 'Unknown Name',
              headline: result.profile_data?.profile_data?.headline || 'N/A',
              score: batchScore,
              assessment: result.assessment,
              profileSummary: null,
              checked_at: result.profile_data?.profile_data?.checked_at,
              success: result.success,
              url: result.url,
              originalIndex: index
            });
          });

          // Add saved assessments
          savedAssessments.forEach((result, index) => {
            const savedScore = result.weighted_score !== null 
              ? result.weighted_score 
              : (result.overall_score !== null ? result.overall_score : 0);
            
            allCandidates.push({
              type: 'saved',
              rank: 0, // Will be updated after sorting
              name: result.full_name || 'Unknown Name',
              headline: result.headline || 'N/A',
              score: savedScore,
              assessment: result.assessment_data,
              profileSummary: result.profile_data,
              checked_at: result.profile_data?.checked_at,
              success: true,
              url: result.linkedin_url,
              created_at: result.created_at,
              assessment_type: result.assessment_type,
              originalIndex: index
            });
          });
          
          // Sort by score in descending order
          allCandidates.sort((a, b) => b.score - a.score);
          
          // Update ranks
          allCandidates.forEach((candidate, index) => {
            candidate.rank = index + 1;
          });
          
          return (
            <div className="results-panel">
              <div className="button-group">
                {(singleProfileResults.length > 0 || batchResults.length > 0) && (
                  <button 
                    className="mode-btn save-btn"
                    onClick={saveCurrentAssessments}
                    disabled={savingAssessments}
                  >
                    {savingAssessments ? 'Saving...' : 'Save Current Assessments'}
                  </button>
                )}
                <button 
                  className="mode-btn load-btn"
                  onClick={loadSavedAssessments}
                  disabled={loadingSaved}
                >
                  {loadingSaved ? 'Loading...' : 'Load from Database'}
                </button>
                {(singleProfileResults.length > 0 || batchResults.length > 0 || savedAssessments.length > 0) && (
                  <button 
                    className="mode-btn clear-btn"
                    onClick={clearAllResults}
                  >
                    Clear All Results
                  </button>
            )}
          </div>
              <h2>
                Assessment Results ({allCandidates.length} candidate{allCandidates.length !== 1 ? 's' : ''})
              </h2>
              {allCandidates.length === 0 ? (
                <div className="empty-state">
                  <p>No assessments found. Process some profiles or load from database to see results.</p>
                </div>
              ) : (
            <div className="candidates-list">
                  {allCandidates.map((candidate, index) => (
                  <div
                    key={`${candidate.type}-${candidate.originalIndex || 0}`}
                    className={`candidate-card ${drawerOpen[candidate.url] ? 'feedback-active' : ''}`}
                    data-candidate-url={candidate.url}
                  >
                  <div className="candidate-header">
                    <div className="candidate-rank">
                        <span className="rank-number">#{candidate.rank}</span>
                    </div>
                    <div className="candidate-info">
                      <div className="candidate-name-row">
                        <h3>{candidate.name}</h3>
                        {candidate.url && candidate.url !== 'Test Profile' && (
                          <a 
                            href={candidate.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="linkedin-icon"
                            title="View LinkedIn Profile"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#0077b5">
                              <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                            </svg>
                          </a>
                        )}
                      </div>
                      <div className="candidate-meta">
                          <span className="candidate-headline">{candidate.headline}</span>
                      </div>

                      {/* Data Freshness - Compact Design */}
                      <div className="data-freshness-box">
                        <div className="freshness-row">
                          <div className="freshness-info">
                            {candidate.checked_at && (
                              <div className="freshness-item">
                                <span className="freshness-label">Data fetched from CoreSignal:</span>
                                <span className="freshness-date">
                                  {new Date(candidate.checked_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                </span>
                              </div>
                            )}
                            {candidate.last_fetched ? (
                              <div className="freshness-item">
                                <span className="freshness-label">Stored in database:</span>
                                <span className="freshness-date">
                                  {new Date(candidate.last_fetched).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                </span>
                                <span className="freshness-age">
                                  ({Math.floor((new Date() - new Date(candidate.last_fetched)) / (1000 * 60 * 60 * 24))}d ago)
                                </span>
                              </div>
                            ) : (
                              <div className="freshness-item">
                                <span className="freshness-fresh">✨ Fresh from API</span>
                              </div>
                            )}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm(
                                `Refresh ${candidate.name}'s profile?\n\n` +
                                `This will use 1 CoreSignal API credit.`
                              )) {
                                handleRefreshProfile(candidate.url);
                              }
                            }}
                            className="refresh-profile-button"
                            title="Refresh from CoreSignal (1 API credit)"
                          >
                            <TbRefresh size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="candidate-score">
                        {candidate.assessment && (
                        <div className="final-score">
                            {candidate.assessment.weighted_analysis && candidate.assessment.weighted_analysis.weighted_score !== undefined ? (
                            <div className="score-display">
                              <span className="score-label">Weighted Score</span>
                              <span className="score-value">
                                  {candidate.assessment.weighted_analysis.weighted_score === 'N/A' ? 'N/A' : `${candidate.assessment.weighted_analysis.weighted_score}/10`}
                              </span>
                            </div>
                            ) : candidate.assessment.overall_score ? (
                            <div className="score-display">
                              <span className="score-label">Overall Score</span>
                              <span className="score-value">
                                  {candidate.assessment.overall_score === 'N/A' ? 'N/A' : `${candidate.assessment.overall_score}/10`}
                              </span>
                            </div>
                          ) : (
                            <div className="score-display">
                              <span className="score-label">Score</span>
                              <span className="score-value">N/A</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                  <div className="candidate-details">
                    <details
                      className="assessment-details"
                      open={openAccordionId === candidate.url}
                    >
                      <summary
                        className="details-summary"
                        onClick={(e) => {
                          // Prevent summary click if clicking feedback drawer
                          if (e.target.closest('.feedback-drawer')) {
                            e.stopPropagation();
                            e.preventDefault();
                            return;
                          }
                          // Prevent default browser toggle behavior
                          e.preventDefault();
                          // Use our controlled toggle instead
                          toggleAccordion(candidate.url);
                        }}
                      >View Detailed Work Experience</summary>

                      <div className="details-content">

                          {/* Sliding Feedback Drawer - Inside Accordion */}
                          {candidate.url && candidate.url !== 'Test Profile' && (
                            <div className="feedback-drawer">
                              {/* Collapsed Tab - Always Visible */}
                              <div
                                className="feedback-tab"
                                onClick={() => toggleDrawer(candidate.url, candidate.name)}
                                title={drawerOpen[candidate.url] ? "Close feedback panel" : "Open feedback panel"}
                              >
                                <div className="feedback-tab-content">
                                  <div className={`feedback-status-dot ${(feedbackHistory[candidate.url] || []).length > 0 ? 'has-feedback' : ''}`}></div>
                                  <span className="feedback-tab-label">Feedback</span>
                                  {(feedbackHistory[candidate.url] || []).length > 0 && (
                                    <span className="feedback-count">{(feedbackHistory[candidate.url] || []).length}</span>
                                  )}
                                  <span className="feedback-arrow">{drawerOpen[candidate.url] ? '▶' : '◀'}</span>
                                </div>
                              </div>

                              {/* Expanded Panel */}
                              <div className={`feedback-panel ${drawerOpen[candidate.url] ? 'expanded' : ''}`}>
                                {/* Candidate Header - Sticky */}
                                <div className="feedback-candidate-header">
                                  <div className="feedback-candidate-name">{candidate.name}</div>
                                  <div className="feedback-candidate-headline">{candidate.headline}</div>
                                  <div className="feedback-context-reminder">Feedback for this candidate</div>
                                </div>

                                {/* Feedback History */}
                                {(() => {
                                  const history = feedbackHistory[candidate.url] || [];
                                  return history.length > 0 ? (
                                    <details open className="feedback-history-section">
                                      <summary className="feedback-history-title">
                                        💬 Previous Feedback ({history.length})
                                      </summary>
                                      <div className="feedback-history-list">
                                        {history.map((fb, idx) => (
                                          <div key={idx} className={`feedback-history-item ${fb.feedback_type}`}>
                                            <div className="feedback-history-header">
                                              <span>{fb.feedback_type === 'like' ? '👍' : fb.feedback_type === 'dislike' ? '👎' : '📝'} {fb.recruiter_name}</span>
                                              <span className="feedback-history-date">{new Date(fb.created_at).toLocaleDateString()}</span>
                                            </div>
                                            {fb.feedback_text && <div className="feedback-history-text">{fb.feedback_text}</div>}
                                          </div>
                                        ))}
                                      </div>
                                    </details>
                                  ) : null;
                                })()}

                                {/* HIDDEN: Quick Feedback Buttons - Keep code for future use */}
                                {false && (
                                <>
                                <div className="feedback-section">
                                  <div className="feedback-section-title">👍 Why do you like this candidate?</div>
                                  <div className="feedback-buttons">
                                    {likeReasons.map((reason, idx) => (
                                      <button
                                        key={idx}
                                        className="feedback-button like-button"
                                        onClick={() => handleQuickFeedback(candidate.url, 'like', reason)}
                                      >
                                        {reason}
                                      </button>
                                    ))}
                                  </div>
                                </div>

                                <div className="feedback-section">
                                  <div className="feedback-section-title dislike">👎 Why pass on this candidate?</div>
                                  <div className="feedback-buttons">
                                    {passReasons.map((reason, idx) => (
                                      <button
                                        key={idx}
                                        className="feedback-button dislike-button"
                                        onClick={() => handleQuickFeedback(candidate.url, 'dislike', reason)}
                                      >
                                        {reason}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                                </>
                                )}

                                {/* Custom Notes */}
                                <div className="feedback-section">
                                  <div className="feedback-section-title">✍️ Custom Notes</div>
                                  <div className="feedback-note-container">
                                    <textarea
                                      className="feedback-note-textarea"
                                      value={candidateFeedback[candidate.url]?.note || ''}
                                      onChange={(e) => handleNoteChange(candidate.url, e.target.value)}
                                      onBlur={(e) => handleNoteBlur(candidate.url, e.target.value)}
                                      placeholder="Type your feedback or click the microphone..."
                                    />
                                    <button
                                      className={`feedback-mic-button ${isRecording[candidate.url] ? 'recording' : ''}`}
                                      onClick={() => isRecording[candidate.url] ? stopVoiceRecording(candidate.url) : startVoiceRecording(candidate.url)}
                                      title={isRecording[candidate.url] ? 'Stop recording' : 'Start voice input (Chrome only)'}
                                    >
                                      {isRecording[candidate.url] ? '⏹' : '🎤'}
                                    </button>
                                  </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="feedback-actions">
                                  <button
                                    className="feedback-clear-button"
                                    onClick={() => clearMyFeedback(candidate.url, candidate.name)}
                                  >
                                    Clear My Feedback
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* HIDDEN: Assessment Scores - Keep code for future use */}
                          {false && candidate.assessment && (
                            <div className="assessment-scores">
                                {candidate.assessment.weighted_analysis && candidate.assessment.weighted_analysis.weighted_score !== undefined ? (
                                <div className="score-section">
                                  <h4>Weighted Final Score</h4>
                                    {renderScoreBar(candidate.assessment.weighted_analysis.weighted_score)}
                                </div>
                                ) : candidate.assessment.overall_score ? (
                                <div className="score-section">
                                  <h4>Overall Score</h4>
                                    {renderScoreBar(candidate.assessment.overall_score)}
                                </div>
                              ) : null}
                            </div>
                          )}

                          {/* HIDDEN: Weighted Analysis - Keep code for future use */}
                            {false && candidate.assessment && candidate.assessment.weighted_analysis && candidate.assessment.weighted_analysis.requirements && candidate.assessment.weighted_analysis.requirements.length > 0 && (
                            <div className="weighted-analysis-section">
                              <h4>Weighted Analysis</h4>
                              <div className="weighted-requirements">
                                  {candidate.assessment.weighted_analysis.requirements.map((req, reqIdx) => (
                                  <div key={reqIdx} className="requirement-item">
                                    <div className="requirement-header">
                                      <span className="requirement-text">{req.requirement} ({req.weight}%)</span>
                                      <span className="requirement-score">{renderWeightedScore(req.score)}</span>
                                    </div>
                                    <p className="requirement-analysis">{req.analysis}</p>
                                  </div>
                                ))}

                                  {candidate.assessment.weighted_analysis.general_fit_weight > 0 && (
                                  <div className="requirement-item general-fit">
                                    <div className="requirement-header">
                                        <span className="requirement-text">General Fit ({candidate.assessment.weighted_analysis.general_fit_weight}%)</span>
                                        <span className="requirement-score">{renderWeightedScore(candidate.assessment.weighted_analysis.general_fit_score)}</span>
                                    </div>
                                      <p className="requirement-analysis">{candidate.assessment.weighted_analysis.general_fit_analysis}</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* HIDDEN: AI Analysis Accordion - Keep code for future use */}
                          {false && (
                          <div className="ai-analysis-accordion">
                            <details
                              className="ai-analysis-details"
                              onToggle={(e) => {
                                // Only trigger if opening AND assessment doesn't exist yet
                                if (e.target.open && !candidate.assessment && !aiAnalysisLoading[candidate.url]) {
                                  // Pass the RAW profile_data, not the extracted summary
                                  const rawProfileData = candidate.profile_data?.profile_data;
                                  if (rawProfileData) {
                                    handleGenerateAIAnalysis(candidate.url, rawProfileData);
                                  }
                                }
                              }}
                            >
                              <summary className="ai-analysis-summary">
                                <span className="ai-analysis-title">🤖 AI Analysis</span>
                                <span className="ai-analysis-disclaimer">
                                  {candidate.assessment
                                    ? '(Click to expand)'
                                    : '(Click to generate - may take 10-15 seconds)'
                                  }
                                </span>
                              </summary>

                              <div className="ai-analysis-content">
                                {/* Loading State */}
                                {aiAnalysisLoading[candidate.url] && (
                                  <div className="ai-loading">
                                    <div className="spinner"></div>
                                    <p>Generating AI analysis...</p>
                                    <p className="loading-subtext">This may take 10-15 seconds</p>
                                  </div>
                                )}

                                {/* Placeholder when no assessment */}
                                {!candidate.assessment && !aiAnalysisLoading[candidate.url] && (
                                  <div className="ai-placeholder">
                                    <p>Click the accordion header to generate AI-powered analysis</p>
                                  </div>
                                )}

                                {/* Show Results when loaded */}
                                {candidate.assessment && !aiAnalysisLoading[candidate.url] && (
                                  <>
                                    <div className="ai-disclaimer-banner">
                                      ⚠️ This AI analysis is experimental and still being refined. Please use your professional judgment and provide feedback to help us improve.
                                    </div>

                                    {/* Key Strengths and Weaknesses */}
                                    <div className="assessment-summary">
                                      {candidate.assessment.strengths && candidate.assessment.strengths.length > 0 && (
                                        <div className="strengths-section">
                                          <h4>Key Strengths</h4>
                                          <ul>
                                            {candidate.assessment.strengths.map((strength, idx) => (
                                              <li key={idx}>{strength}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}

                                      {candidate.assessment.weaknesses && candidate.assessment.weaknesses.length > 0 && (
                                        <div className="weaknesses-section">
                                          <h4>Key Weaknesses</h4>
                                          <ul>
                                            {candidate.assessment.weaknesses.map((weakness, idx) => (
                                              <li key={idx}>{weakness}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </div>

                                    {/* Career Trajectory */}
                                    {candidate.assessment.career_trajectory && candidate.assessment.career_trajectory !== 'Profile not found in CoreSignal database' && (
                                      <div className="career-trajectory-section">
                                        <h4>Career Trajectory</h4>
                                        <p>{candidate.assessment.career_trajectory}</p>
                                      </div>
                                    )}
                                  </>
                                )}
                              </div>
                            </details>
                          </div>
                          )}

                          {/* Work Experience with Company Intelligence */}
                          <WorkExperienceSection
                            profileData={candidate.profileSummary || (candidate.type === 'batch' ? candidate.profile_data?.profile_data : null)}
                            profileSummary={candidate.profileSummary}
                            onRegenerateUrl={handleRegenerateCrunchbaseUrl}
                            onCrunchbaseClick={handleCrunchbaseClick}
                          />

                            {/* Profile Not Found Message - only for batch results */}
                            {candidate.type === 'batch' && !candidate.success && (
                            <div className="profile-not-found-section">
                              <h4>Profile Not Found</h4>
                              <p>This LinkedIn profile was not found in our database. Assessment could not be completed.</p>
                                <p><strong>URL:</strong> {candidate.url}</p>
                            </div>
                          )}
                        </div>
                      </details>
                    </div>
                </div>
              ))}
                </div>
              )}
            </div>
          );
        })()}

      </div>

      {/* Loading Overlay */}
      {showLoadingOverlay && (
        <div className="loading-overlay">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>{loadingMessage}</p>
            </div>
          </div>
        )}

      {/* Notification */}
      {notification.show && (
        <div className={`notification ${notification.type}`}>
          {notification.type === 'success' ? '✅' : notification.type === 'info' ? 'ℹ️' : '❌'} {notification.message}
      </div>
      )}

      {/* Crunchbase Validation Modal */}
      {validationModalOpen && validationData && (
        <CrunchbaseValidationModal
          isOpen={validationModalOpen}
          onClose={() => setValidationModalOpen(false)}
          companyName={validationData.companyName}
          crunchbaseUrl={validationData.crunchbaseUrl}
          companyId={validationData.companyId}
          onValidate={handleValidation}
          onRegenerate={validationData.onRegenerate}
        />
      )}
    </div>
  );
}

export default App;