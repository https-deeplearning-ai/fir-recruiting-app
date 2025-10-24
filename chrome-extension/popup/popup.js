// Popup JavaScript for LinkedIn Profile AI Assessor Extension

// Configuration
const API_BASE_URL = 'http://localhost:5001'; // Will be configurable in options

// State management
let currentProfile = null;
let selectedProfiles = new Set();
let lists = [];
let templates = [];

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await initializePopup();
  attachEventListeners();
});

async function initializePopup() {
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (tab.url && tab.url.includes('linkedin.com')) {
      // Check if we're on a profile page or search results
      if (tab.url.includes('/in/')) {
        await loadProfileData(tab);
      } else if (tab.url.includes('/search/')) {
        showBatchMode();
      }

      updateStatus('Ready', 'success');
    } else {
      showMessage('Please navigate to LinkedIn to use this extension', 'info');
      updateStatus('Not on LinkedIn', 'error');
    }

    // Load user lists and templates
    await loadUserLists();
    await loadJobTemplates();

  } catch (error) {
    console.error('Initialization error:', error);
    updateStatus('Error', 'error');
    showMessage('Failed to initialize extension', 'error');
  }
}

// Load profile data from current page
async function loadProfileData(tab) {
  updateStatus('Loading profile...', 'loading');

  try {
    // Send message to content script to extract profile data
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'extractProfile'
    });

    if (response && response.success) {
      currentProfile = response.data;
      displayProfile(currentProfile);
      document.getElementById('currentProfile').style.display = 'block';
    }
  } catch (error) {
    console.error('Failed to extract profile:', error);
    // Fallback: try to get basic info from URL
    const urlMatch = tab.url.match(/\/in\/([^\/]+)/);
    if (urlMatch) {
      currentProfile = {
        linkedinUrl: tab.url,
        shorthand: urlMatch[1],
        name: 'Profile data pending...'
      };
      displayProfile(currentProfile);
    }
  }
}

// Display profile information
function displayProfile(profile) {
  document.getElementById('profileName').textContent = profile.name || 'Unknown';
  document.getElementById('profileHeadline').textContent = profile.headline || 'No headline';
  document.getElementById('profileCompany').textContent = profile.currentCompany || 'No company info';
}

// Load user's lists from backend
async function loadUserLists() {
  try {
    const response = await fetch(`${API_BASE_URL}/extension/lists`, {
      headers: {
        'Authorization': `Bearer ${await getAuthToken()}`
      }
    });

    if (response.ok) {
      lists = await response.json();
      populateListDropdown(lists);
    }
  } catch (error) {
    console.error('Failed to load lists:', error);
  }
}

// Load job templates
async function loadJobTemplates() {
  try {
    const response = await fetch(`${API_BASE_URL}/jobs/list`, {
      headers: {
        'Authorization': `Bearer ${await getAuthToken()}`
      }
    });

    if (response.ok) {
      templates = await response.json();
      populateTemplateDropdown(templates);
    }
  } catch (error) {
    console.error('Failed to load templates:', error);
  }
}

// Populate list dropdown
function populateListDropdown(lists) {
  const select = document.getElementById('listSelect');

  // Clear existing options except first two
  while (select.options.length > 2) {
    select.remove(2);
  }

  // Add lists
  lists.forEach(list => {
    const option = new Option(
      `${list.list_name} (${list.profile_count} profiles)`,
      list.id
    );
    select.add(option);
  });

  // Select default list if available
  const defaultList = localStorage.getItem('defaultListId');
  if (defaultList && lists.find(l => l.id === defaultList)) {
    select.value = defaultList;
    updateListStats(defaultList);
  }
}

// Populate template dropdown
function populateTemplateDropdown(templates) {
  const select = document.getElementById('templateSelect');

  // Clear existing options except first two
  while (select.options.length > 2) {
    select.remove(2);
  }

  // Add templates
  templates.forEach(template => {
    const option = new Option(
      `${template.title} (${template.department})`,
      template.id
    );
    select.add(option);
  });
}

// Event Listeners
function attachEventListeners() {
  // Add to List button
  document.getElementById('addToListBtn').addEventListener('click', async () => {
    await addToList();
  });

  // Quick Assess button
  document.getElementById('quickAssessBtn').addEventListener('click', async () => {
    await quickAssess();
  });

  // List selection change
  document.getElementById('listSelect').addEventListener('change', async (e) => {
    if (e.target.value === 'new') {
      await createNewList();
    } else if (e.target.value) {
      localStorage.setItem('defaultListId', e.target.value);
      updateListStats(e.target.value);
    }
  });

  // Template selection change
  document.getElementById('templateSelect').addEventListener('change', async (e) => {
    if (e.target.value === 'new') {
      await createFromJobDescription();
    }
  });

  // Open Dashboard link
  document.getElementById('openDashboard').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:3000' });
  });

  // Open Options link
  document.getElementById('openOptions').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });
}

// Add current profile to selected list
async function addToList() {
  const listId = document.getElementById('listSelect').value;

  if (!listId) {
    showMessage('Please select a list first', 'error');
    return;
  }

  if (!currentProfile) {
    showMessage('No profile data available', 'error');
    return;
  }

  const button = document.getElementById('addToListBtn');
  button.classList.add('loading');
  button.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/extension/add-profile`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        linkedin_url: currentProfile.linkedinUrl,
        name: currentProfile.name,
        headline: currentProfile.headline,
        current_company: currentProfile.currentCompany,
        current_title: currentProfile.currentTitle,
        location: currentProfile.location,
        list_id: listId
      })
    });

    if (response.ok) {
      showMessage('Profile added successfully!', 'success');
      updateListStats(listId);

      // Update tab icon to show profile was added
      const currentTab = await getCurrentTab();
      chrome.action.setBadgeText({ text: '✓', tabId: currentTab.id });
      chrome.action.setBadgeBackgroundColor({ color: '#10b981' });

      // Clear badge after 3 seconds
      setTimeout(() => {
        chrome.action.setBadgeText({ text: '', tabId: currentTab.id });
      }, 3000);
    } else {
      const error = await response.json();
      showMessage(error.message || 'Failed to add profile', 'error');
    }
  } catch (error) {
    console.error('Failed to add profile:', error);
    showMessage('Network error. Please try again.', 'error');
  } finally {
    button.classList.remove('loading');
    button.disabled = false;
  }
}

// Quick assess current profile
async function quickAssess() {
  if (!currentProfile) {
    showMessage('No profile data available', 'error');
    return;
  }

  const templateId = document.getElementById('templateSelect').value;
  const button = document.getElementById('quickAssessBtn');

  button.classList.add('loading');
  button.disabled = true;
  updateStatus('Running assessment...', 'loading');

  try {
    const response = await fetch(`${API_BASE_URL}/extension/quick-assess`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        linkedin_url: currentProfile.linkedinUrl,
        profile_data: currentProfile,
        template_id: templateId || null
      })
    });

    if (response.ok) {
      const result = await response.json();
      showMessage(`Assessment complete! Score: ${result.weighted_score}/100`, 'success');

      // Open results in new tab
      const resultsUrl = `http://localhost:3000?highlight=${encodeURIComponent(currentProfile.linkedinUrl)}`;
      chrome.tabs.create({ url: resultsUrl });
    } else {
      const error = await response.json();
      showMessage(error.message || 'Assessment failed', 'error');
    }
  } catch (error) {
    console.error('Failed to assess profile:', error);
    showMessage('Network error. Please try again.', 'error');
  } finally {
    button.classList.remove('loading');
    button.disabled = false;
    updateStatus('Ready', 'success');
  }
}

// Create new list
async function createNewList() {
  const listName = prompt('Enter name for new list:');

  if (!listName) {
    document.getElementById('listSelect').value = '';
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/extension/create-list`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        list_name: listName,
        recruiter_name: await getRecruiterName()
      })
    });

    if (response.ok) {
      const newList = await response.json();
      await loadUserLists();
      document.getElementById('listSelect').value = newList.id;
      showMessage('List created successfully!', 'success');
    } else {
      showMessage('Failed to create list', 'error');
    }
  } catch (error) {
    console.error('Failed to create list:', error);
    showMessage('Network error. Please try again.', 'error');
  }
}

// Create template from job description
async function createFromJobDescription() {
  // Open a new tab with job template creator
  chrome.tabs.create({
    url: 'http://localhost:3000/templates/new'
  });
}

// Update list statistics
function updateListStats(listId) {
  const list = lists.find(l => l.id === listId);
  if (list) {
    document.getElementById('listCount').textContent = list.profile_count || 0;
    document.getElementById('assessedCount').textContent = list.assessed_count || 0;
    document.getElementById('listStats').style.display = 'flex';
  }
}

// Show batch mode for search results
function showBatchMode() {
  document.getElementById('batchSection').style.display = 'block';
  document.getElementById('batchAddBtn').style.display = 'block';

  // Initialize batch operations
  initBatchOperations();
}

// Initialize batch operations for search results
async function initBatchOperations() {
  // Send message to content script to enable batch selection
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  chrome.tabs.sendMessage(tab.id, {
    action: 'enableBatchMode'
  });

  // Listen for selection updates
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'selectionUpdate') {
      selectedProfiles = new Set(message.selected);
      document.getElementById('selectedCount').textContent = selectedProfiles.size;
      document.getElementById('batchAddBtn').textContent = `Batch Add (${selectedProfiles.size})`;
    }
  });
}

// Utility Functions

// Get current tab
async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Get auth token (from storage or generate)
async function getAuthToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get('authToken', (data) => {
      resolve(data.authToken || 'demo-token'); // In production, implement proper auth
    });
  });
}

// Get recruiter name
async function getRecruiterName() {
  return new Promise((resolve) => {
    chrome.storage.local.get('recruiterName', (data) => {
      resolve(data.recruiterName || 'Unknown Recruiter');
    });
  });
}

// Update status indicator
function updateStatus(text, state) {
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  statusText.textContent = text;
  statusDot.className = 'status-dot';

  if (state === 'error') {
    statusDot.classList.add('error');
  } else if (state === 'loading') {
    statusDot.classList.add('loading');
  }
}

// Show message
function showMessage(text, type) {
  const messageDiv = document.getElementById('message');
  messageDiv.textContent = text;
  messageDiv.className = `message ${type}`;
  messageDiv.style.display = 'block';

  // Auto-hide after 5 seconds
  setTimeout(() => {
    messageDiv.style.display = 'none';
  }, 5000);
}