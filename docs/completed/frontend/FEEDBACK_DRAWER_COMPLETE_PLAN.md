# Feedback Drawer Fix - Complete Implementation Plan

**Date:** 2025-11-06
**Goal:** Fix feedback drawer to viewport right edge while preserving smart viewport tracking

---

## ✅ Current System (WORKING - Keep This Logic!)

### Intersection Observer Tracking
```javascript
// Lines 223-249: Tracks which candidate is most visible
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    const candidateUrl = entry.target.getAttribute('data-candidate-url');
    setCandidateVisibility(prev => ({
      ...prev,
      [candidateUrl]: entry.intersectionRatio  // 0-1 visibility
    }));
  });
}, {
  threshold: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
  rootMargin: '-50px 0px -50px 0px'
});
```

### Smart Drawer Switching
```javascript
// Lines 474-510: Opens feedback for most visible candidate
const toggleDrawer = async (linkedinUrl) => {
  const mostVisible = getMostVisibleCandidate();
  if (mostVisible) {
    targetUrl = mostVisible;  // Auto-switch!
  }

  // Save previous feedback before switching
  if (activeCandidate && activeCandidate !== targetUrl) {
    await handleDrawerCollapse(activeCandidate);
  }

  setDrawerOpen({ [targetUrl]: true });
  setActiveCandidate(targetUrl);
  await loadFeedbackHistory(targetUrl);
};
```

**Key Insight:** The drawer ALREADY knows which candidate to show based on scroll position. We just need to move it to viewport-fixed positioning!

---

## 🎯 The Fix: Move Drawer to Portal + Fixed Positioning

### Current Structure (BAD)
```
<candidate-card>
  <details> (accordion)
    <summary>View Details</summary>
    <div className="details-content">
      <div className="feedback-drawer">  ❌ Inside accordion!
        <div className="feedback-tab">...</div>
        <div className="feedback-panel">...</div>
      </div>
    </div>
  </details>
</candidate-card>
```

**Problems:**
- Drawer is inside accordion (constrained by parent)
- Each candidate has its own drawer instance (inefficient)
- Can't use `position: fixed` effectively

### New Structure (GOOD)
```
<candidate-card data-candidate-url="...">
  <details> (accordion)
    <summary>View Details</summary>
    <div className="details-content">
      <!-- Drawer removed from here -->
    </div>
  </details>
</candidate-card>

<!-- Single global drawer at document.body level -->
{ReactDOM.createPortal(
  <div className="feedback-drawer-container">
    <div className="feedback-tab">...</div>
    <div className="feedback-panel">
      {/* Content for activeCandidate */}
    </div>
  </div>,
  document.body
)}
```

**Benefits:**
- ✅ Single drawer instance (efficient)
- ✅ position: fixed works perfectly
- ✅ No parent constraints
- ✅ Still shows correct candidate based on `activeCandidate` state

---

## 📝 Implementation Steps

### Step 1: Remove Drawer from Accordion (App.js line ~5240)

**FIND THIS CODE:**
```jsx
<div className="details-content">
  {/* Sliding Feedback Drawer - Inside Accordion */}
  {candidate.url && candidate.url !== 'Test Profile' && (
    <div className="feedback-drawer">
      <div className="feedback-tab" onClick={() => toggleDrawer(candidate.url, candidate.name)}>
        ...
      </div>
      <div className={`feedback-panel ${drawerOpen[candidate.url] ? 'expanded' : ''}`}>
        ...
      </div>
    </div>
  )}
```

**REMOVE IT COMPLETELY** (lines 5238-5356)

---

### Step 2: Add Single Global Drawer with Portal

**ADD THIS AFTER ALL CANDIDATE CARDS** (around line 5500+):

```jsx
{/* Global Feedback Drawer - Rendered at document.body via Portal */}
{activeCandidate && ReactDOM.createPortal(
  <div className="feedback-drawer-container">
    {/* Collapsed Tab - Always Visible */}
    <div
      className="feedback-tab"
      onClick={() => toggleDrawer(activeCandidate)}
      title={drawerOpen[activeCandidate] ? "Close feedback panel" : "Open feedback panel"}
    >
      <div className="feedback-tab-content">
        <div className={`feedback-status-dot ${(feedbackHistory[activeCandidate] || []).length > 0 ? 'has-feedback' : ''}`}></div>
        <span className="feedback-tab-label">Feedback</span>
        {(feedbackHistory[activeCandidate] || []).length > 0 && (
          <span className="feedback-count">{(feedbackHistory[activeCandidate] || []).length}</span>
        )}
        <span className="feedback-arrow">{drawerOpen[activeCandidate] ? '▶' : '◀'}</span>
      </div>
    </div>

    {/* Expanded Panel */}
    <div className={`feedback-panel ${drawerOpen[activeCandidate] ? 'expanded' : ''}`}>
      {(() => {
        // Find the active candidate data
        const allCandidates = [
          ...singleProfileResults,
          ...batchResults,
          ...savedAssessments
        ];
        const candidate = allCandidates.find(c => c.url === activeCandidate);

        if (!candidate) return null;

        return (
          <>
            {/* Candidate Header - Sticky */}
            <div className="feedback-candidate-header">
              <div className="feedback-candidate-name">{candidate.name}</div>
              <div className="feedback-candidate-headline">{candidate.headline}</div>
              <div className="feedback-context-reminder">Feedback for this candidate</div>
            </div>

            {/* Feedback History */}
            {(() => {
              const history = feedbackHistory[activeCandidate] || [];
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

            {/* Custom Notes */}
            <div className="feedback-section">
              <div className="feedback-section-title">✍️ Custom Notes</div>
              <div className="feedback-note-container">
                <textarea
                  className="feedback-note-textarea"
                  value={candidateFeedback[activeCandidate]?.note || ''}
                  onChange={(e) => handleNoteChange(activeCandidate, e.target.value)}
                  onBlur={(e) => handleNoteBlur(activeCandidate, e.target.value)}
                  placeholder="Type your feedback or click the microphone..."
                />
                <button
                  className={`feedback-mic-button ${isRecording[activeCandidate] ? 'recording' : ''}`}
                  onClick={() => isRecording[activeCandidate] ? stopVoiceRecording(activeCandidate) : startVoiceRecording(activeCandidate)}
                  title={isRecording[activeCandidate] ? 'Stop recording' : 'Start voice input (Chrome only)'}
                >
                  {isRecording[activeCandidate] ? '⏹' : '🎤'}
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="feedback-actions">
              <button
                className="feedback-clear-button"
                onClick={() => clearMyFeedback(activeCandidate, candidate.name)}
              >
                Clear My Feedback
              </button>
            </div>
          </>
        );
      })()}
    </div>
  </div>,
  document.body
)}
```

---

### Step 3: Update toggleDrawer Logic

**MODIFY** `toggleDrawer` function (line ~474) to handle viewport-fixed drawer:

```javascript
const toggleDrawer = async (linkedinUrl, candidateName) => {
  // Determine which candidate to open feedback for
  let targetUrl = linkedinUrl;

  // If no specific URL or opening from closed state,
  // use the most visible candidate in viewport
  if (!linkedinUrl || !drawerOpen[linkedinUrl]) {
    const mostVisible = getMostVisibleCandidate();
    if (mostVisible && (!linkedinUrl || mostVisible !== linkedinUrl)) {
      console.log(`🎯 Opening feedback for most visible candidate: ${mostVisible}`);
      targetUrl = mostVisible;
    }
  }

  // If we're toggling the currently open drawer, close it
  if (drawerOpen[targetUrl]) {
    await handleDrawerCollapse(targetUrl);
    setDrawerOpen(prev => ({
      ...prev,
      [targetUrl]: false
    }));
    setActiveCandidate(null);  // Clear active candidate
    return;
  }

  // If opening new drawer while another is open, save previous
  if (activeCandidate && activeCandidate !== targetUrl && drawerOpen[activeCandidate]) {
    await handleDrawerCollapse(activeCandidate);
  }

  // Open drawer for new candidate
  setDrawerOpen(prev => ({
    ...prev,
    [targetUrl]: true
  }));
  setActiveCandidate(targetUrl);

  // Load feedback history
  await loadFeedbackHistory(targetUrl);

  // Optional: Scroll the candidate card into view
  const cardElement = document.querySelector(`.candidate-card[data-candidate-url="${targetUrl}"]`);
  if (cardElement) {
    cardElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};
```

---

### Step 4: Add Viewport-Fixed CSS

**CREATE:** `frontend/src/styles/components/feedback-drawer.css`

```css
/* ========================================
   FEEDBACK DRAWER - VIEWPORT FIXED
   ======================================== */

.feedback-drawer-container {
  position: fixed;
  right: 0;
  top: 120px;
  height: calc(100vh - 140px);
  z-index: 2000;
  pointer-events: none; /* Allow clicks through container */
}

/* Collapsed Tab - Always Visible */
.feedback-tab {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 48px;
  height: 120px;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  border-radius: 12px 0 0 12px;
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.3s ease;
  box-shadow: -4px 0 12px rgba(124, 58, 237, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.feedback-tab:hover {
  transform: translateY(-50%) translateX(-4px);
  box-shadow: -6px 0 16px rgba(124, 58, 237, 0.4);
}

.feedback-tab-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  color: white;
}

.feedback-tab-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
}

.feedback-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.feedback-status-dot.has-feedback {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.feedback-count {
  background: white;
  color: #7c3aed;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

.feedback-arrow {
  font-size: 16px;
  transition: transform 0.3s ease;
}

/* Expanded Panel */
.feedback-panel {
  position: absolute;
  right: 48px;
  top: 0;
  width: 450px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.15);
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: auto;
  overflow-y: auto;
  overflow-x: hidden;
  border-radius: 12px 0 0 12px;
  z-index: 0;
}

.feedback-panel.expanded {
  transform: translateX(0);
}

/* Candidate Header - Sticky */
.feedback-candidate-header {
  position: sticky;
  top: 0;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: white;
  padding: 20px;
  border-radius: 12px 0 0 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.feedback-candidate-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}

.feedback-candidate-headline {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.feedback-context-reminder {
  font-size: 11px;
  opacity: 0.8;
  font-style: italic;
}

/* Feedback Content */
.feedback-section {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.feedback-section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #1f2937;
}

/* Textarea */
.feedback-note-container {
  position: relative;
}

.feedback-note-textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  padding-right: 50px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.feedback-note-textarea:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
}

.feedback-mic-button {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border: none;
  background: #f3f4f6;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.feedback-mic-button:hover {
  background: #e5e7eb;
  transform: scale(1.1);
}

.feedback-mic-button.recording {
  background: #ef4444;
  color: white;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}

/* Feedback History */
.feedback-history-section {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.feedback-history-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  cursor: pointer;
  list-style: none;
}

.feedback-history-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-history-item {
  padding: 12px;
  border-radius: 8px;
  background: #f9fafb;
  border-left: 3px solid #9ca3af;
}

.feedback-history-item.like {
  border-left-color: #10b981;
  background: #f0fdf4;
}

.feedback-history-item.dislike {
  border-left-color: #ef4444;
  background: #fef2f2;
}

.feedback-history-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.feedback-history-date {
  font-size: 11px;
  color: #6b7280;
  font-weight: 400;
}

.feedback-history-text {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}

/* Action Buttons */
.feedback-actions {
  padding: 20px;
  display: flex;
  gap: 12px;
}

.feedback-clear-button {
  flex: 1;
  padding: 10px 16px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.feedback-clear-button:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: #fef2f2;
}

/* Scrollbar Styling */
.feedback-panel::-webkit-scrollbar {
  width: 6px;
}

.feedback-panel::-webkit-scrollbar-track {
  background: #f9fafb;
}

.feedback-panel::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.feedback-panel::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Responsive */
@media (max-width: 768px) {
  .feedback-panel {
    width: 90vw;
    max-width: 400px;
  }
}
```

---

### Step 5: Highlight Active Candidate

**ADD TO** `App.css`:

```css
/* Highlight candidate when feedback drawer is open */
.candidate-card.feedback-active {
  border-left: 4px solid #7c3aed;
  background: linear-gradient(90deg, rgba(124, 58, 237, 0.05) 0%, transparent 100%);
  transition: all 0.3s ease;
}
```

**UPDATE** candidate card JSX to add class:

```jsx
<div
  className={`candidate-card ${activeCandidate === candidate.url ? 'feedback-active' : ''}`}
  data-candidate-url={candidate.url}
>
```

---

### Step 6: Import ReactDOM

**ADD AT TOP** of App.js:

```javascript
import ReactDOM from 'react-dom';
```

---

### Step 7: Import Feedback Drawer CSS

**ADD TO** `App.css`:

```css
/* Import feedback drawer styles */
@import './styles/components/feedback-drawer.css';
```

---

## 🎯 How It Works After Fix

### User Scrolls → Drawer Auto-Switches
```
1. User scrolls down
2. Intersection Observer updates candidateVisibility
3. Candidate B becomes most visible (ratio 0.8)
4. User clicks feedback tab
5. toggleDrawer() calls getMostVisibleCandidate()
6. Returns Candidate B URL
7. Sets activeCandidate = Candidate B
8. Drawer shows Candidate B's feedback
9. Candidate B card gets .feedback-active class
```

### Drawer Behavior
```
State: activeCandidate = null, all drawerOpen[url] = false
  → Drawer not visible at all

User clicks feedback on Card A:
  → activeCandidate = Card A
  → drawerOpen[Card A] = true
  → Drawer appears at right edge, shows Card A feedback
  → Card A gets purple left border

User scrolls to Card B (Card B now most visible):
  → candidateVisibility[Card B] = 0.9 (highest)
  → activeCandidate still = Card A (no auto-switch until user clicks)

User clicks feedback tab again:
  → getMostVisibleCandidate() returns Card B
  → Save Card A feedback
  → activeCandidate = Card B
  → drawerOpen[Card B] = true
  → Drawer content switches to Card B
  → Card B gets purple border, Card A loses it
```

---

## ✅ Testing Checklist

- [ ] Import ReactDOM at top of App.js
- [ ] Remove old feedback drawer from accordion (line ~5240)
- [ ] Add new Portal-based drawer after all candidates
- [ ] Update toggleDrawer to handle active candidate switching
- [ ] Create feedback-drawer.css
- [ ] Import feedback-drawer.css in App.css
- [ ] Add .feedback-active styles to App.css
- [ ] Test: Drawer appears at right edge
- [ ] Test: Drawer follows scroll (position: fixed)
- [ ] Test: Click feedback on Card A → shows Card A
- [ ] Test: Scroll to Card B, click feedback → auto-switches to Card B
- [ ] Test: Active card gets purple border
- [ ] Test: Textarea, voice button, clear button all work
- [ ] Test: Feedback history loads correctly
- [ ] Test: Close drawer → activeCandidate = null

---

## 🎉 Final Result

```
Screen Layout:

┌────────────────────────────────────────────────────────┐
│ ┌────────────────────────────────┐                     │
│ │ Candidate A                    │                     │
│ │ (Purple border if active)      │                     │
│ └────────────────────────────────┘                     │
│                                                         │
│ ┌────────────────────────────────┐                     │
│ │ Candidate B (most visible)     │   ┌──────┐         │
│ │ (Purple border if active)      │   │📝    │ Tab     │
│ └────────────────────────────────┘   │      │         │
│                                       └──┬───┘         │
│ ┌────────────────────────────────┐      │             │
│ │ Candidate C                    │   ┌──┴──────────┐  │
│ └────────────────────────────────┘   │  Feedback   │  │
│                                       │  Panel      │  │
└───────────────────────────────────────│  (slides in)│──┘
                                        │             │
                                        │  [Content]  │
                                        └─────────────┘

Key Features:
✅ Single drawer instance (efficient)
✅ Fixed at viewport right (follows scroll)
✅ Auto-switches to most visible candidate
✅ Highlights active candidate with purple border
✅ Saves feedback before switching
✅ No tooltip CSS interference
```

---

## Summary

**What We're Keeping:**
- ✅ Intersection Observer tracking
- ✅ getMostVisibleCandidate() logic
- ✅ Smart auto-switching to most visible
- ✅ All state management (activeCandidate, drawerOpen, candidateVisibility)

**What We're Changing:**
- ❌ Remove drawer from inside accordion
- ✅ Move to single global drawer with Portal
- ✅ Use position: fixed for viewport anchoring
- ✅ Dedicated CSS (no tooltip inheritance)
- ✅ Highlight active candidate

**Result:**
Same smart behavior, better positioning!
