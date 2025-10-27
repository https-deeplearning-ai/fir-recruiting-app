// Options Page JavaScript for LinkedIn Profile AI Assessor

// Default settings
const defaultSettings = {
  apiUrl: 'http://localhost:5001',
  authToken: '',
  recruiterName: '',
  defaultList: '',
  autoAssess: false,
  enrichWithCompany: true,
  batchSize: 10,
  enableNotifications: true,
  soundEnabled: false,
  debugMode: false,
  cacheExpiry: 24,
  defaultRequirements: [
    { requirement: 'Relevant technical skills and experience', weight: 40 },
    { requirement: 'Leadership and team collaboration', weight: 30 },
    { requirement: 'Industry knowledge and domain expertise', weight: 30 }
  ]
};

// Initialize options page
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  attachEventListeners();
  loadLists();
});

// Load settings from storage
async function loadSettings() {
  try {
    const settings = await chrome.storage.local.get('extensionSettings');
    const currentSettings = { ...defaultSettings, ...settings.extensionSettings };

    // Populate form fields
    document.getElementById('apiUrl').value = currentSettings.apiUrl;
    document.getElementById('authToken').value = currentSettings.authToken || '';
    document.getElementById('recruiterName').value = currentSettings.recruiterName || '';
    document.getElementById('defaultList').value = currentSettings.defaultList || '';
    document.getElementById('autoAssess').checked = currentSettings.autoAssess;
    document.getElementById('enrichWithCompany').checked = currentSettings.enrichWithCompany;
    document.getElementById('batchSize').value = currentSettings.batchSize;
    document.getElementById('enableNotifications').checked = currentSettings.enableNotifications;
    document.getElementById('soundEnabled').checked = currentSettings.soundEnabled;
    document.getElementById('debugMode').checked = currentSettings.debugMode;
    document.getElementById('cacheExpiry').value = currentSettings.cacheExpiry;

    // Load requirements
    loadRequirements(currentSettings.defaultRequirements);
  } catch (error) {
    console.error('Failed to load settings:', error);
    showStatus('Failed to load settings', 'error');
  }
}

// Load requirements list
function loadRequirements(requirements) {
  const container = document.getElementById('requirementsList');
  container.innerHTML = '';

  requirements.forEach(req => {
    addRequirementRow(req.requirement, req.weight);
  });

  updateWeightTotal();
}

// Add requirement row
function addRequirementRow(requirement = '', weight = 0) {
  const container = document.getElementById('requirementsList');
  const row = document.createElement('div');
  row.className = 'requirement-item';

  row.innerHTML = `
    <input type="text" placeholder="Requirement description" value="${requirement}">
    <input type="number" placeholder="Weight %" min="0" max="100" value="${weight}">
    <button class="remove-btn">Remove</button>
  `;

  // Add remove handler
  row.querySelector('.remove-btn').addEventListener('click', () => {
    row.remove();
    updateWeightTotal();
  });

  // Add weight change handler
  row.querySelector('input[type="number"]').addEventListener('input', updateWeightTotal);

  container.appendChild(row);
}

// Update weight total
function updateWeightTotal() {
  const weights = document.querySelectorAll('.requirement-item input[type="number"]');
  let total = 0;

  weights.forEach(input => {
    total += parseInt(input.value) || 0;
  });

  const totalElement = document.getElementById('totalWeight');
  totalElement.textContent = total + '%';

  if (total === 100) {
    totalElement.className = 'weight-value valid';
  } else {
    totalElement.className = 'weight-value invalid';
  }
}

// Load available lists
async function loadLists() {
  try {
    const settings = await chrome.storage.local.get('extensionSettings');
    const apiUrl = settings.extensionSettings?.apiUrl || defaultSettings.apiUrl;
    const authToken = settings.extensionSettings?.authToken;

    if (!authToken) {
      return; // No auth token, can't load lists
    }

    const response = await fetch(`${apiUrl}/extension/lists`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (response.ok) {
      const lists = await response.json();
      const select = document.getElementById('defaultList');

      // Clear existing options except first
      while (select.options.length > 1) {
        select.remove(1);
      }

      // Add lists
      lists.forEach(list => {
        const option = new Option(
          `${list.list_name} (${list.profile_count} profiles)`,
          list.id
        );
        select.add(option);
      });

      // Select current default if exists
      const currentDefault = settings.extensionSettings?.defaultList;
      if (currentDefault) {
        select.value = currentDefault;
      }
    }
  } catch (error) {
    console.error('Failed to load lists:', error);
  }
}

// Attach event listeners
function attachEventListeners() {
  // Save settings button
  document.getElementById('saveSettings').addEventListener('click', saveSettings);

  // Reset settings button
  document.getElementById('resetSettings').addEventListener('click', resetSettings);

  // Clear cache button
  document.getElementById('clearCache').addEventListener('click', clearCache);

  // Add requirement button
  document.getElementById('addRequirement').addEventListener('click', () => {
    addRequirementRow();
    updateWeightTotal();
  });

  // Open dashboard link
  document.getElementById('openDashboard').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:3000' });
  });

  // Report issue link
  document.getElementById('reportIssue').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'https://github.com/your-repo/issues' });
  });

  // API URL change - reload lists
  document.getElementById('apiUrl').addEventListener('change', loadLists);
  document.getElementById('authToken').addEventListener('change', loadLists);
}

// Save settings
async function saveSettings() {
  try {
    // Validate weights
    const weights = document.querySelectorAll('.requirement-item input[type="number"]');
    let total = 0;
    weights.forEach(input => {
      total += parseInt(input.value) || 0;
    });

    if (total !== 100) {
      showStatus('Requirements weights must total 100%', 'error');
      return;
    }

    // Collect requirements
    const requirements = [];
    document.querySelectorAll('.requirement-item').forEach(item => {
      const requirement = item.querySelector('input[type="text"]').value;
      const weight = parseInt(item.querySelector('input[type="number"]').value) || 0;

      if (requirement && weight > 0) {
        requirements.push({ requirement, weight });
      }
    });

    // Collect all settings
    const settings = {
      apiUrl: document.getElementById('apiUrl').value,
      authToken: document.getElementById('authToken').value,
      recruiterName: document.getElementById('recruiterName').value,
      defaultList: document.getElementById('defaultList').value,
      autoAssess: document.getElementById('autoAssess').checked,
      enrichWithCompany: document.getElementById('enrichWithCompany').checked,
      batchSize: parseInt(document.getElementById('batchSize').value),
      enableNotifications: document.getElementById('enableNotifications').checked,
      soundEnabled: document.getElementById('soundEnabled').checked,
      debugMode: document.getElementById('debugMode').checked,
      cacheExpiry: parseInt(document.getElementById('cacheExpiry').value),
      defaultRequirements: requirements
    };

    // Save to storage
    await chrome.storage.local.set({
      extensionSettings: settings,
      authToken: settings.authToken,
      recruiterName: settings.recruiterName,
      defaultListId: settings.defaultList
    });

    showStatus('Settings saved successfully!', 'success');

    // If debug mode changed, log it
    if (settings.debugMode) {
      console.log('Debug mode enabled. Settings:', settings);
    }

  } catch (error) {
    console.error('Failed to save settings:', error);
    showStatus('Failed to save settings', 'error');
  }
}

// Reset settings to defaults
async function resetSettings() {
  if (!confirm('Are you sure you want to reset all settings to defaults?')) {
    return;
  }

  try {
    await chrome.storage.local.set({
      extensionSettings: defaultSettings
    });

    loadSettings();
    showStatus('Settings reset to defaults', 'success');
  } catch (error) {
    console.error('Failed to reset settings:', error);
    showStatus('Failed to reset settings', 'error');
  }
}

// Clear cache
async function clearCache() {
  if (!confirm('Are you sure you want to clear all cached data?')) {
    return;
  }

  try {
    await chrome.storage.local.remove(['profileCache', 'listCache']);
    showStatus('Cache cleared successfully', 'success');
  } catch (error) {
    console.error('Failed to clear cache:', error);
    showStatus('Failed to clear cache', 'error');
  }
}

// Show status message
function showStatus(message, type) {
  const statusDiv = document.getElementById('statusMessage');
  statusDiv.textContent = message;
  statusDiv.className = `status-message ${type}`;
  statusDiv.style.display = 'block';

  // Auto-hide after 5 seconds
  setTimeout(() => {
    statusDiv.style.display = 'none';
  }, 5000);
}

// Handle keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Cmd/Ctrl + S to save
  if ((e.metaKey || e.ctrlKey) && e.key === 's') {
    e.preventDefault();
    saveSettings();
  }
});