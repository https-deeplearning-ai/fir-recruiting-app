# Feedback Drawer Positioning Fix Plan

**Date:** 2025-11-06
**Issue:** Feedback drawer needs to be fixed to viewport right edge and follow scroll, separate from tooltip CSS

## Current System (How It Works Now)

### ✅ Smart Viewport Tracking (KEEP THIS!)
- **Intersection Observer**: Tracks visibility of each `.candidate-card[data-candidate-url]`
- **Visibility Ratio**: Measures 0-1 how much of each card is visible (11 thresholds)
- **Most Visible Logic**: `getMostVisibleCandidate()` finds card with highest ratio
- **Auto-Switch**: When you scroll, feedback switches to whichever candidate is most visible
- **State Management**:
  - `candidateVisibility`: Maps URL → visibility ratio
  - `drawerOpen`: Maps URL → isOpen boolean
  - `activeCandidate`: Currently active candidate URL

### ✅ Current Behavior (Lines 474-510 in App.js)
```javascript
const toggleDrawer = async (linkedinUrl, candidateName) => {
  // If no URL or opening from closed state, use most visible candidate
  if (!linkedinUrl || !drawerOpen[linkedinUrl]) {
    const mostVisible = getMostVisibleCandidate();
    if (mostVisible) {
      targetUrl = mostVisible; // Switch to most visible!
    }
  }

  // Save previous feedback if switching candidates
  if (activeCandidate && activeCandidate !== targetUrl) {
    await handleDrawerCollapse(activeCandidate);
  }

  // Open drawer for target candidate
  setDrawerOpen({ [targetUrl]: true });
  setActiveCandidate(targetUrl);

  // Load feedback history for this candidate
  await loadFeedbackHistory(targetUrl);
}
```

## Current Problem

The feedback drawer positioning is currently affected by:
1. **Inside accordion** - Lives inside `<details>` content (line 5240)
2. **Relative positioning** - Constrained by parent candidate card
3. **Needs viewport-fixed** - Should be at right edge, follow scroll
4. **Tooltip CSS conflicts** - May inherit unwanted styles

## Requirements

✅ **Position:** Fixed at right edge of viewport (not relative to card)
✅ **Scroll Behavior:** Stays fixed in viewport, follows scroll naturally
✅ **Independence:** Should NOT inherit tooltip CSS
✅ **Location:** Appears to the left of the viewport right edge
✅ **Z-index:** Above all content but below modals

## Implementation Plan

### Step 1: Identify Current Feedback Drawer Code
- [ ] Find feedback drawer JSX in App.js
- [ ] Check current CSS classes used
- [ ] Verify if it's inside candidate cards or at app level

### Step 2: Move to React Portal (if needed)
- [ ] Similar to modal fix, use `ReactDOM.createPortal()`
- [ ] Render at `document.body` level
- [ ] Remove from inside candidate card component

### Step 3: Create Dedicated Feedback Drawer CSS
- [ ] Create new CSS file: `styles/components/feedback-drawer.css`
- [ ] Use `position: fixed` for viewport anchoring
- [ ] Set `right: 0` or `right: 20px` for positioning
- [ ] Set `top: 100px` or similar for vertical position
- [ ] Add `z-index: 2000` (above content, below modals at 9999)
- [ ] NO inheritance from tooltip CSS

### Step 4: CSS Structure

```css
/* feedback-drawer.css */

.feedback-drawer-container {
  position: fixed;
  right: 0;
  top: 120px;
  height: calc(100vh - 140px);
  z-index: 2000;
  pointer-events: none; /* Allow clicks through when closed */
}

.feedback-drawer-tab {
  position: absolute;
  right: 0;
  top: 0;
  width: 40px;
  height: 80px;
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  pointer-events: auto;
  transition: transform 0.3s ease;
}

.feedback-drawer-tab:hover {
  transform: translateX(-4px);
}

.feedback-drawer-panel {
  position: absolute;
  right: 0;
  top: 0;
  width: 400px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  pointer-events: auto;
  overflow-y: auto;
}

.feedback-drawer-panel.open {
  transform: translateX(0);
}

.feedback-drawer-content {
  padding: 24px;
  /* NO gap, NO tooltip inheritance */
}
```

### Step 5: Update App.js Structure

**Current (likely inside cards):**
```jsx
<div className="candidate-card">
  {/* candidate content */}
  <div className="feedback-drawer">
    {/* feedback UI */}
  </div>
</div>
```

**New (using Portal):**
```jsx
// Inside App.js, outside candidate cards
{activeCandidate && ReactDOM.createPortal(
  <div className="feedback-drawer-container">
    <div className="feedback-drawer-tab">
      📝
    </div>
    <div className={`feedback-drawer-panel ${drawerOpen ? 'open' : ''}`}>
      <div className="feedback-drawer-content">
        {/* Feedback form, history, etc. */}
      </div>
    </div>
  </div>,
  document.body
)}
```

### Step 6: State Management

```javascript
// In App.js
const [feedbackDrawerOpen, setFeedbackDrawerOpen] = useState(false);
const [activeCandidateUrl, setActiveCandidateUrl] = useState(null);

// When user clicks feedback icon on candidate
const handleOpenFeedback = (candidateUrl) => {
  setActiveCandidateUrl(candidateUrl);
  setFeedbackDrawerOpen(true);
};

// Toggle drawer
const toggleFeedbackDrawer = () => {
  setFeedbackDrawerOpen(!feedbackDrawerOpen);
};
```

### Step 7: Visual Highlighting

```css
/* Highlight active candidate when drawer is open */
.candidate-card.feedback-active {
  border-left: 4px solid #7c3aed;
  background: linear-gradient(90deg, rgba(124, 58, 237, 0.05) 0%, transparent 100%);
}
```

## Key Differences from Tooltip/Modal

| Feature | Tooltip | Modal | Feedback Drawer |
|---------|---------|-------|-----------------|
| Position | `absolute` (card-relative) | `fixed` (viewport, centered) | `fixed` (viewport, right edge) |
| Scroll | Stays with content | Blocks scroll | Follows viewport |
| Trigger | Hover | Click | Click icon |
| Location | Next to company name | Center of screen | Right edge |
| Z-index | 9999 | 10000 | 2000 |
| Portal | No | Yes | Yes |
| CSS Inheritance | CompanyTooltip.css | modals.css | feedback-drawer.css (NEW) |

## Testing Checklist

After implementation:
- [ ] Drawer appears at right edge of viewport
- [ ] Drawer stays fixed when scrolling
- [ ] Tab is always visible
- [ ] Panel slides in/out smoothly
- [ ] NO tooltip CSS interference
- [ ] Works on different screen sizes
- [ ] Active candidate is highlighted
- [ ] Can close drawer and reopen
- [ ] Z-index correct (above content, below modals)

## Files to Modify

1. **frontend/src/App.js**
   - Import ReactDOM
   - Move feedback drawer outside candidate cards
   - Use Portal to render at document.body
   - Add state management

2. **frontend/src/styles/components/feedback-drawer.css** (NEW FILE)
   - Create dedicated CSS
   - position: fixed
   - No tooltip inheritance

3. **frontend/src/App.css**
   - Import feedback-drawer.css
   - Add .candidate-card.feedback-active styles

4. **Remove old feedback drawer CSS**
   - Remove any feedback-related styles from other files
   - Clean up old positioning code

## Expected Result

```
┌─────────────────────────────────────────────────┐
│ Assessment Results                              │
│                                                 │
│ ┌─────────────────────────┐                    │
│ │ Candidate Card          │                    │
│ │ (highlighted if active) │                    │
│ │                         │                    │
│ │ [Feedback icon]         │                    │
│ └─────────────────────────┘                    │
│                                                 │
│ ┌─────────────────────────┐                    │
│ │ Candidate Card          │                    │
│ └─────────────────────────┘                    │
└─────────────────────────────────────────────────┘
                                          ┌────────┐
                                          │ 📝     │ ← Tab
                                          │        │
                                          │        │
                                    ┌─────┴────────┤
                                    │ Feedback     │ ← Panel
                                    │ Drawer       │   (slides in)
                                    │              │
                                    │ [Form]       │
                                    │ [History]    │
                                    └──────────────┘
```

## Why This Approach Works

1. **React Portal:** Breaks out of DOM hierarchy, no parent constraints
2. **position: fixed:** Anchors to viewport, follows scroll automatically
3. **Dedicated CSS:** No inheritance from tooltip/modal styles
4. **document.body rendering:** Highest level, no z-index conflicts
5. **State-driven:** Single source of truth for which candidate is active

## Reference

- Modal fix: WorkExperienceCard.js line 378 (uses Portal)
- Tooltip positioning: TOOLTIP_POSITIONING_SOLUTION.md
- React Portals docs: https://react.dev/reference/react-dom/createPortal
