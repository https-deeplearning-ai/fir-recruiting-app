// Content Script for LinkedIn Profile AI Assessor
// Runs on all LinkedIn pages to extract profile data and enable batch operations

console.log('[LinkedIn AI Assessor] Content script loaded');

// State management
let batchModeEnabled = false;
let selectedProfiles = new Set();

// Initialize content script
(function initialize() {
  // Check what type of LinkedIn page we're on
  const currentUrl = window.location.href;

  if (currentUrl.includes('/in/')) {
    // Profile page
    initProfilePage();
  } else if (currentUrl.includes('/search/')) {
    // Search results page
    initSearchPage();
  } else if (currentUrl.includes('/people/')) {
    // Company people page
    initCompanyPeoplePage();
  }

  // Listen for navigation changes (LinkedIn is a SPA)
  observeUrlChanges();
})();

// Initialize profile page features
function initProfilePage() {
  console.log('[LinkedIn AI Assessor] Profile page detected');

  // Add floating action button
  addFloatingActionButton();

  // Extract profile data when requested
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extractProfile') {
      const profileData = extractProfileData();
      sendResponse({ success: true, data: profileData });
    }
    return true; // Keep message channel open for async response
  });
}

// Initialize search results page
function initSearchPage() {
  console.log('[LinkedIn AI Assessor] Search page detected');

  // Listen for batch mode activation
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'enableBatchMode') {
      enableBatchMode();
      sendResponse({ success: true });
    }
    return true;
  });

  // Add batch selection UI
  addBatchSelectionUI();
}

// Initialize company people page
function initCompanyPeoplePage() {
  console.log('[LinkedIn AI Assessor] Company people page detected');

  // Similar to search page
  addBatchSelectionUI();
}

// Extract profile data from the page DOM
function extractProfileData() {
  const data = {
    linkedinUrl: window.location.href,
    shorthand: extractShorthand(),
    name: extractName(),
    headline: extractHeadline(),
    currentCompany: extractCurrentCompany(),
    currentTitle: extractCurrentTitle(),
    location: extractLocation(),
    about: extractAbout(),
    experience: extractExperience(),
    education: extractEducation(),
    skills: extractSkills()
  };

  console.log('[LinkedIn AI Assessor] Extracted profile data:', data);
  return data;
}

// Extract LinkedIn shorthand from URL
function extractShorthand() {
  const match = window.location.href.match(/\/in\/([^\/\?]+)/);
  return match ? match[1] : null;
}

// Extract profile name
function extractName() {
  // Try multiple selectors as LinkedIn changes them frequently
  const selectors = [
    'h1.text-heading-xlarge',
    'h1[class*="inline t-24"]',
    '.pv-top-card__title',
    'h1.pv-top-card-section__name'
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent) {
      return element.textContent.trim();
    }
  }

  return null;
}

// Extract headline
function extractHeadline() {
  const selectors = [
    '.text-body-medium.break-words',
    'div[class*="text-body-medium break-words"]',
    '.pv-top-card-section__headline',
    'h2.mt1.t-18'
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent) {
      return element.textContent.trim();
    }
  }

  return null;
}

// Extract current company
function extractCurrentCompany() {
  // Look for current position in experience section
  const experienceItem = document.querySelector('[data-view-name="profile-component-entity"]');
  if (experienceItem) {
    const companyElement = experienceItem.querySelector('span[aria-hidden="true"]');
    if (companyElement) {
      const text = companyElement.textContent.trim();
      // Extract company name from format "Title · Company · Duration"
      const parts = text.split('·');
      if (parts.length >= 2) {
        return parts[1].trim();
      }
    }
  }

  // Fallback: try to find in headline
  const headline = extractHeadline();
  if (headline && headline.includes(' at ')) {
    const atIndex = headline.lastIndexOf(' at ');
    return headline.substring(atIndex + 4).trim();
  }

  return null;
}

// Extract current title
function extractCurrentTitle() {
  const experienceItem = document.querySelector('[data-view-name="profile-component-entity"]');
  if (experienceItem) {
    const titleElement = experienceItem.querySelector('div.display-flex span[aria-hidden="true"]');
    if (titleElement) {
      const text = titleElement.textContent.trim();
      // Extract title from format "Title · Company · Duration"
      const parts = text.split('·');
      if (parts.length >= 1) {
        return parts[0].trim();
      }
    }
  }

  return null;
}

// Extract location
function extractLocation() {
  const selectors = [
    '.text-body-small.inline.t-black--light.break-words',
    'span[class*="text-body-small inline"]',
    '.pv-top-card-section__location',
    'h3.t-16.t-black.t-normal'
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent && !element.textContent.includes('follower')) {
      return element.textContent.trim();
    }
  }

  return null;
}

// Extract about section
function extractAbout() {
  const aboutSection = document.querySelector('#about');
  if (aboutSection) {
    const textElement = aboutSection.parentElement.querySelector('.display-flex.full-width span[aria-hidden="true"]');
    if (textElement) {
      return textElement.textContent.trim();
    }
  }

  return null;
}

// Extract work experience
function extractExperience() {
  const experiences = [];
  const experienceSection = document.querySelector('#experience');

  if (experienceSection) {
    const experienceItems = experienceSection.parentElement.querySelectorAll('[data-view-name="profile-component-entity"]');

    experienceItems.forEach(item => {
      const titleElement = item.querySelector('div.display-flex span[aria-hidden="true"]');
      const companyElement = item.querySelector('span.t-14.t-normal span[aria-hidden="true"]');
      const durationElement = item.querySelector('span.t-14.t-normal.t-black--light span[aria-hidden="true"]');

      if (titleElement) {
        experiences.push({
          title: titleElement.textContent.trim(),
          company: companyElement ? companyElement.textContent.trim() : null,
          duration: durationElement ? durationElement.textContent.trim() : null
        });
      }
    });
  }

  return experiences;
}

// Extract education
function extractEducation() {
  const education = [];
  const educationSection = document.querySelector('#education');

  if (educationSection) {
    const educationItems = educationSection.parentElement.querySelectorAll('[data-view-name="profile-component-entity"]');

    educationItems.forEach(item => {
      const schoolElement = item.querySelector('div.display-flex span[aria-hidden="true"]');
      const degreeElement = item.querySelector('span.t-14.t-normal span[aria-hidden="true"]');

      if (schoolElement) {
        education.push({
          school: schoolElement.textContent.trim(),
          degree: degreeElement ? degreeElement.textContent.trim() : null
        });
      }
    });
  }

  return education;
}

// Extract skills
function extractSkills() {
  const skills = [];
  const skillsSection = document.querySelector('#skills');

  if (skillsSection) {
    const skillItems = skillsSection.parentElement.querySelectorAll('[data-view-name="profile-component-entity"]');

    skillItems.forEach(item => {
      const skillElement = item.querySelector('div.display-flex span[aria-hidden="true"]');
      if (skillElement) {
        skills.push(skillElement.textContent.trim());
      }
    });
  }

  return skills;
}

// Add floating action button to profile pages
function addFloatingActionButton() {
  // Check if button already exists
  if (document.getElementById('linkedin-assessor-fab')) {
    return;
  }

  const fab = document.createElement('div');
  fab.id = 'linkedin-assessor-fab';
  fab.innerHTML = `
    <button class="assessor-fab-button" title="Add to LinkedIn AI Assessor">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/>
      </svg>
    </button>
    <div class="assessor-fab-menu" style="display: none;">
      <button class="assessor-fab-menu-item" data-action="add-to-list">
        <span>Add to List</span>
      </button>
      <button class="assessor-fab-menu-item" data-action="quick-assess">
        <span>Quick Assess</span>
      </button>
      <button class="assessor-fab-menu-item" data-action="add-note">
        <span>Add Note</span>
      </button>
    </div>
  `;

  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    #linkedin-assessor-fab {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
    }

    .assessor-fab-button {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .assessor-fab-button:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    .assessor-fab-menu {
      position: absolute;
      bottom: 70px;
      right: 0;
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      overflow: hidden;
      min-width: 180px;
    }

    .assessor-fab-menu-item {
      width: 100%;
      padding: 12px 16px;
      border: none;
      background: white;
      text-align: left;
      cursor: pointer;
      font-size: 14px;
      color: #333;
      transition: background 0.2s;
    }

    .assessor-fab-menu-item:hover {
      background: #f5f5f5;
    }

    .assessor-fab-menu-item:not(:last-child) {
      border-bottom: 1px solid #e5e7eb;
    }
  `;

  document.head.appendChild(style);
  document.body.appendChild(fab);

  // Add event listeners
  const button = fab.querySelector('.assessor-fab-button');
  const menu = fab.querySelector('.assessor-fab-menu');

  button.addEventListener('click', () => {
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!fab.contains(e.target)) {
      menu.style.display = 'none';
    }
  });

  // Handle menu item clicks
  fab.querySelectorAll('.assessor-fab-menu-item').forEach(item => {
    item.addEventListener('click', (e) => {
      const action = e.currentTarget.dataset.action;
      handleFabAction(action);
      menu.style.display = 'none';
    });
  });
}

// Handle floating action button actions
function handleFabAction(action) {
  const profileData = extractProfileData();

  switch (action) {
    case 'add-to-list':
      chrome.runtime.sendMessage({
        action: 'addToList',
        data: profileData
      });
      showNotification('Profile added to list!');
      break;

    case 'quick-assess':
      chrome.runtime.sendMessage({
        action: 'quickAssess',
        data: profileData
      });
      showNotification('Running assessment...');
      break;

    case 'add-note':
      const note = prompt('Add a note for this profile:');
      if (note) {
        chrome.runtime.sendMessage({
          action: 'addNote',
          data: { ...profileData, note }
        });
        showNotification('Note saved!');
      }
      break;
  }
}

// Add batch selection UI to search/people pages
function addBatchSelectionUI() {
  // Add checkboxes to each search result
  const observer = new MutationObserver(() => {
    addCheckboxesToResults();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  // Initial run
  addCheckboxesToResults();
}

// Add checkboxes to search results
function addCheckboxesToResults() {
  const resultCards = document.querySelectorAll('.entity-result__item, .org-people-profile-card');

  resultCards.forEach(card => {
    // Skip if checkbox already added
    if (card.querySelector('.assessor-checkbox')) {
      return;
    }

    const profileLink = card.querySelector('a[href*="/in/"]');
    if (!profileLink) {
      return;
    }

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'assessor-checkbox';
    checkbox.dataset.profileUrl = profileLink.href;

    // Style the checkbox
    checkbox.style.cssText = `
      position: absolute;
      top: 12px;
      right: 12px;
      width: 20px;
      height: 20px;
      cursor: pointer;
      z-index: 10;
    `;

    // Make card position relative if not already
    if (getComputedStyle(card).position === 'static') {
      card.style.position = 'relative';
    }

    card.appendChild(checkbox);

    // Handle checkbox changes
    checkbox.addEventListener('change', (e) => {
      const url = e.target.dataset.profileUrl;

      if (e.target.checked) {
        selectedProfiles.add(url);
      } else {
        selectedProfiles.delete(url);
      }

      // Notify popup of selection change
      chrome.runtime.sendMessage({
        action: 'selectionUpdate',
        selected: Array.from(selectedProfiles)
      });
    });
  });
}

// Enable batch mode
function enableBatchMode() {
  batchModeEnabled = true;

  // Show all checkboxes
  document.querySelectorAll('.assessor-checkbox').forEach(checkbox => {
    checkbox.style.display = 'block';
  });

  showNotification('Batch mode enabled. Select profiles to add.');
}

// Show notification
function showNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'assessor-notification';
  notification.textContent = message;

  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;

  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);

  document.body.appendChild(notification);

  // Remove after 3 seconds
  setTimeout(() => {
    notification.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

// Observe URL changes (LinkedIn is a SPA)
function observeUrlChanges() {
  let lastUrl = location.href;

  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      console.log('[LinkedIn AI Assessor] URL changed:', url);

      // Re-initialize based on new URL
      if (url.includes('/in/')) {
        initProfilePage();
      } else if (url.includes('/search/')) {
        initSearchPage();
      } else if (url.includes('/people/')) {
        initCompanyPeoplePage();
      }
    }
  }).observe(document, { subtree: true, childList: true });
}

console.log('[LinkedIn AI Assessor] Content script initialized');