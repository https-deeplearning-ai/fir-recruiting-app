// Background Service Worker for LinkedIn Profile AI Assessor
// Handles API communication, message passing, and background tasks

// Configuration
const config = {
  API_BASE_URL: 'http://localhost:5001',
  FRONTEND_URL: 'http://localhost:3000',
  STORAGE_KEYS: {
    AUTH_TOKEN: 'authToken',
    RECRUITER_NAME: 'recruiterName',
    DEFAULT_LIST: 'defaultListId',
    SETTINGS: 'extensionSettings',
    PROFILE_CACHE: 'profileCache'
  },
  CACHE_DURATION: 60 * 60 * 1000, // 1 hour in milliseconds
};

// State management
let profileQueue = [];
let isProcessingQueue = false;
let authToken = null;

// Initialize service worker
chrome.runtime.onInstalled.addListener((details) => {
  console.log('[LinkedIn AI Assessor] Extension installed/updated', details);

  // Set default settings on install
  if (details.reason === 'install') {
    chrome.storage.local.set({
      [config.STORAGE_KEYS.SETTINGS]: {
        autoAssess: false,
        batchSize: 10,
        apiUrl: config.API_BASE_URL,
        enableNotifications: true
      }
    });
  }

  // Create context menus
  createContextMenus();
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Service Worker] Received message:', message.action);

  switch (message.action) {
    case 'addToList':
      handleAddToList(message.data).then(sendResponse);
      break;

    case 'quickAssess':
      handleQuickAssess(message.data).then(sendResponse);
      break;

    case 'addNote':
      handleAddNote(message.data).then(sendResponse);
      break;

    case 'batchAdd':
      handleBatchAdd(message.data).then(sendResponse);
      break;

    case 'getAuthStatus':
      checkAuthStatus().then(sendResponse);
      break;

    case 'authenticate':
      authenticate(message.credentials).then(sendResponse);
      break;

    case 'getSettings':
      getSettings().then(sendResponse);
      break;

    case 'updateSettings':
      updateSettings(message.settings).then(sendResponse);
      break;

    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }

  return true; // Keep message channel open for async response
});

// Create context menus
function createContextMenus() {
  // Remove existing menus
  chrome.contextMenus.removeAll();

  // Add to List context menu
  chrome.contextMenus.create({
    id: 'add-to-list',
    title: 'Add to LinkedIn AI Assessor',
    contexts: ['link'],
    documentUrlPatterns: ['*://www.linkedin.com/*'],
    targetUrlPatterns: ['*://www.linkedin.com/in/*']
  });

  // Quick Assess context menu
  chrome.contextMenus.create({
    id: 'quick-assess',
    title: 'Quick Assess Profile',
    contexts: ['link'],
    documentUrlPatterns: ['*://www.linkedin.com/*'],
    targetUrlPatterns: ['*://www.linkedin.com/in/*']
  });
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const profileUrl = info.linkUrl;

  switch (info.menuItemId) {
    case 'add-to-list':
      await handleAddToListFromUrl(profileUrl, tab);
      break;

    case 'quick-assess':
      await handleQuickAssessFromUrl(profileUrl, tab);
      break;
  }
});

// API Communication Functions

// Handle adding profile to list
async function handleAddToList(profileData) {
  try {
    await ensureAuthenticated();

    const response = await fetch(`${config.API_BASE_URL}/extension/add-profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify(profileData)
    });

    if (response.ok) {
      const result = await response.json();

      // Cache the profile data
      await cacheProfile(profileData);

      // Show notification
      showNotification('Profile Added', `${profileData.name} was added to your list`);

      return { success: true, data: result };
    } else {
      const error = await response.json();
      return { success: false, error: error.message };
    }
  } catch (error) {
    console.error('Failed to add profile:', error);
    return { success: false, error: error.message };
  }
}

// Handle quick assessment
async function handleQuickAssess(profileData) {
  try {
    await ensureAuthenticated();

    // Check if profile data needs enrichment
    if (!profileData.experience || profileData.needsEnrichment) {
      // First fetch full profile from CoreSignal
      const fetchResponse = await fetch(`${config.API_BASE_URL}/fetch-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          linkedin_url: profileData.linkedinUrl,
          enrich_with_company_data: true
        })
      });

      if (fetchResponse.ok) {
        const fullProfile = await fetchResponse.json();
        profileData = { ...profileData, ...fullProfile };
      }
    }

    // Run assessment
    const response = await fetch(`${config.API_BASE_URL}/assess-profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        profile_data: profileData,
        assessment_requirements: await getDefaultRequirements()
      })
    });

    if (response.ok) {
      const assessment = await response.json();

      // Save assessment
      await saveAssessment(profileData, assessment);

      // Show notification with score
      showNotification(
        'Assessment Complete',
        `${profileData.name}: ${assessment.weighted_score}/100`
      );

      return { success: true, data: assessment };
    } else {
      const error = await response.json();
      return { success: false, error: error.message };
    }
  } catch (error) {
    console.error('Failed to assess profile:', error);
    return { success: false, error: error.message };
  }
}

// Handle adding note to profile
async function handleAddNote(data) {
  try {
    await ensureAuthenticated();

    const response = await fetch(`${config.API_BASE_URL}/save-feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        candidate_linkedin_url: data.linkedinUrl,
        feedback_text: data.note,
        feedback_type: 'note',
        recruiter_name: await getRecruiterName()
      })
    });

    if (response.ok) {
      showNotification('Note Saved', 'Your note has been saved');
      return { success: true };
    } else {
      const error = await response.json();
      return { success: false, error: error.message };
    }
  } catch (error) {
    console.error('Failed to save note:', error);
    return { success: false, error: error.message };
  }
}

// Handle batch add
async function handleBatchAdd(profiles) {
  try {
    await ensureAuthenticated();

    // Add profiles to queue
    profileQueue.push(...profiles);

    // Start processing if not already running
    if (!isProcessingQueue) {
      processQueue();
    }

    return { success: true, message: `Adding ${profiles.length} profiles to queue` };
  } catch (error) {
    console.error('Failed to batch add:', error);
    return { success: false, error: error.message };
  }
}

// Process profile queue
async function processQueue() {
  if (isProcessingQueue || profileQueue.length === 0) {
    return;
  }

  isProcessingQueue = true;
  const settings = await getSettings();
  const batchSize = settings.batchSize || 10;

  while (profileQueue.length > 0) {
    const batch = profileQueue.splice(0, batchSize);

    // Process batch in parallel
    const promises = batch.map(profile => handleAddToList(profile));
    const results = await Promise.allSettled(promises);

    // Count successes and failures
    const succeeded = results.filter(r => r.status === 'fulfilled' && r.value.success).length;
    const failed = results.length - succeeded;

    // Update badge with progress
    chrome.action.setBadgeText({ text: profileQueue.length.toString() });
    chrome.action.setBadgeBackgroundColor({ color: '#667eea' });

    // Show progress notification
    if (profileQueue.length > 0) {
      showNotification(
        'Batch Processing',
        `Processed ${succeeded}/${batch.length}. ${profileQueue.length} remaining.`
      );
    }

    // Delay between batches to avoid rate limiting
    if (profileQueue.length > 0) {
      await delay(2000);
    }
  }

  // Clear badge when done
  chrome.action.setBadgeText({ text: '' });

  showNotification('Batch Complete', 'All profiles have been processed');
  isProcessingQueue = false;
}

// Handle adding from URL (context menu)
async function handleAddToListFromUrl(profileUrl, tab) {
  try {
    // Inject content script to extract profile data
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractProfileFromUrl,
      args: [profileUrl]
    });

    if (results && results[0] && results[0].result) {
      const profileData = results[0].result;
      const response = await handleAddToList(profileData);

      if (response.success) {
        showNotification('Profile Added', `Profile added from ${profileUrl}`);
      } else {
        showNotification('Failed to Add', response.error, 'error');
      }
    }
  } catch (error) {
    console.error('Failed to add from URL:', error);
    showNotification('Error', 'Failed to extract profile data', 'error');
  }
}

// Handle quick assess from URL (context menu)
async function handleQuickAssessFromUrl(profileUrl, tab) {
  try {
    // Navigate to the profile URL first
    await chrome.tabs.update(tab.id, { url: profileUrl });

    // Wait for page to load
    await waitForTabLoad(tab.id);

    // Inject content script to extract profile data
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractProfileFromUrl,
      args: [profileUrl]
    });

    if (results && results[0] && results[0].result) {
      const profileData = results[0].result;
      const response = await handleQuickAssess(profileData);

      if (response.success) {
        // Open results in new tab
        chrome.tabs.create({
          url: `${config.FRONTEND_URL}?highlight=${encodeURIComponent(profileUrl)}`
        });
      } else {
        showNotification('Assessment Failed', response.error, 'error');
      }
    }
  } catch (error) {
    console.error('Failed to assess from URL:', error);
    showNotification('Error', 'Failed to assess profile', 'error');
  }
}

// Authentication Functions

// Ensure authenticated
async function ensureAuthenticated() {
  if (!authToken) {
    const stored = await chrome.storage.local.get(config.STORAGE_KEYS.AUTH_TOKEN);
    authToken = stored[config.STORAGE_KEYS.AUTH_TOKEN];

    if (!authToken) {
      throw new Error('Not authenticated. Please log in first.');
    }
  }

  return authToken;
}

// Check authentication status
async function checkAuthStatus() {
  try {
    await ensureAuthenticated();

    const response = await fetch(`${config.API_BASE_URL}/extension/auth`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    return { authenticated: response.ok };
  } catch (error) {
    return { authenticated: false };
  }
}

// Authenticate with credentials
async function authenticate(credentials) {
  try {
    // In production, this would be a real auth endpoint
    // For now, we'll store a demo token
    authToken = 'demo-token-' + Date.now();

    await chrome.storage.local.set({
      [config.STORAGE_KEYS.AUTH_TOKEN]: authToken,
      [config.STORAGE_KEYS.RECRUITER_NAME]: credentials.name || 'Unknown Recruiter'
    });

    return { success: true, token: authToken };
  } catch (error) {
    console.error('Authentication failed:', error);
    return { success: false, error: error.message };
  }
}

// Settings Functions

// Get extension settings
async function getSettings() {
  const stored = await chrome.storage.local.get(config.STORAGE_KEYS.SETTINGS);
  return stored[config.STORAGE_KEYS.SETTINGS] || {};
}

// Update extension settings
async function updateSettings(newSettings) {
  const current = await getSettings();
  const updated = { ...current, ...newSettings };

  await chrome.storage.local.set({
    [config.STORAGE_KEYS.SETTINGS]: updated
  });

  return { success: true, settings: updated };
}

// Get default assessment requirements
async function getDefaultRequirements() {
  const settings = await getSettings();

  return settings.defaultRequirements || [
    {
      requirement: "Relevant technical skills and experience",
      weight: 40
    },
    {
      requirement: "Leadership and team collaboration",
      weight: 30
    },
    {
      requirement: "Industry knowledge and domain expertise",
      weight: 30
    }
  ];
}

// Helper Functions

// Cache profile data
async function cacheProfile(profileData) {
  const cache = await chrome.storage.local.get(config.STORAGE_KEYS.PROFILE_CACHE) || {};
  const profileCache = cache[config.STORAGE_KEYS.PROFILE_CACHE] || {};

  profileCache[profileData.linkedinUrl] = {
    data: profileData,
    timestamp: Date.now()
  };

  // Clean old cache entries
  const now = Date.now();
  Object.keys(profileCache).forEach(url => {
    if (now - profileCache[url].timestamp > config.CACHE_DURATION) {
      delete profileCache[url];
    }
  });

  await chrome.storage.local.set({
    [config.STORAGE_KEYS.PROFILE_CACHE]: profileCache
  });
}

// Get cached profile
async function getCachedProfile(linkedinUrl) {
  const cache = await chrome.storage.local.get(config.STORAGE_KEYS.PROFILE_CACHE);
  const profileCache = cache[config.STORAGE_KEYS.PROFILE_CACHE] || {};

  const cached = profileCache[linkedinUrl];
  if (cached && Date.now() - cached.timestamp < config.CACHE_DURATION) {
    return cached.data;
  }

  return null;
}

// Save assessment result
async function saveAssessment(profileData, assessment) {
  try {
    const response = await fetch(`${config.API_BASE_URL}/save-assessment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        linkedin_url: profileData.linkedinUrl,
        full_name: profileData.name,
        headline: profileData.headline,
        profile_data: profileData,
        assessment_data: assessment,
        weighted_score: assessment.weighted_score,
        overall_score: assessment.overall_score,
        assessment_type: 'extension'
      })
    });

    return response.ok;
  } catch (error) {
    console.error('Failed to save assessment:', error);
    return false;
  }
}

// Get recruiter name
async function getRecruiterName() {
  const stored = await chrome.storage.local.get(config.STORAGE_KEYS.RECRUITER_NAME);
  return stored[config.STORAGE_KEYS.RECRUITER_NAME] || 'Unknown Recruiter';
}

// Show notification
function showNotification(title, message, type = 'basic') {
  const settings = chrome.storage.local.get(config.STORAGE_KEYS.SETTINGS);

  if (settings.enableNotifications !== false) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon128.png',
      title: title,
      message: message,
      priority: 2
    });
  }
}

// Wait for tab to load
function waitForTabLoad(tabId) {
  return new Promise((resolve) => {
    chrome.tabs.onUpdated.addListener(function listener(id, info) {
      if (id === tabId && info.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    });
  });
}

// Delay function
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Function to inject into page for extracting profile
function extractProfileFromUrl(url) {
  // This function runs in the page context
  // Try to extract basic info from the page
  const data = {
    linkedinUrl: url,
    name: document.querySelector('h1')?.textContent?.trim() || 'Unknown',
    headline: document.querySelector('.text-body-medium.break-words')?.textContent?.trim() || '',
    needsEnrichment: true
  };

  return data;
}

// Log service worker startup
console.log('[LinkedIn AI Assessor] Service worker started');