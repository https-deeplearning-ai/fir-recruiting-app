# Tooltip Positioning Solution

**Date:** 2025-11-06
**Component:** WorkExperienceCard.js
**Issue:** Company name hover tooltips were positioning incorrectly

## Problem Summary

Tooltips for company names in work experience cards were not appearing in the correct position. Multiple issues were discovered and fixed during debugging.

## Root Causes Identified

### 1. CSS Position Conflicts
**Issue:** Multiple `position: relative` declarations conflicted with tooltip positioning
- `CompanyTooltip.css` had `position: relative` on `.company-tooltip`
- `WorkExperienceCard.css` had more specific selector `.tooltip-wrapper .company-tooltip { position: relative; }`

**Fix:** Removed all position declarations from tooltip component, allowing it to default to `position: static`

### 2. Modal CSS Class Name Mismatch
**Issue:** `modals.css` used BEM naming (`.modal__header`) but React used different names (`.modal-header`)

**Fix:** Updated `modals.css` to match React component class names

### 3. Coordinate System Mismatch (CRITICAL)
**Issue:** Mixed viewport coordinates with document-relative positioning
- Used `getBoundingClientRect()` which returns **viewport coordinates**
- But tooltip used `position: absolute` which positions relative to **parent element**
- This caused tooltips to appear at wrong positions, especially when scrolling

**Fix:** Changed to `offsetTop` and `offsetLeft` which give position relative to parent card

### 4. Overly Aggressive Viewport Constraints
**Issue:** Bottom viewport constraint forced all tooltips to same vertical position
```javascript
// WRONG - forced all tooltips to same position
if (top + TOOLTIP_MAX_HEIGHT > viewportHeight) {
  top = viewportHeight - TOOLTIP_MAX_HEIGHT - MARGIN;
}
```

**Fix:** Removed bottom constraint, allowing tooltips to extend beyond viewport (users can scroll)

### 5. Scroll Listener Causing Movement
**Issue:** Tooltip recalculated position on every scroll event, making it follow the viewport

**Fix:** Removed scroll event listener - tooltips now stay at their initial position

## Final Solution

### Positioning Logic
```javascript
// Use offsetTop/offsetLeft for position relative to parent card
const offsetTop = targetElement.offsetTop;
const offsetLeft = targetElement.offsetLeft;

// Simple positioning: 250px to the right of company name
let left = offsetLeft + 250;
let top = offsetTop;

// Only constrain if too close to top
if (top < 12) {
  top = 12;
}
```

### CSS Setup
```css
/* Parent card has position: relative */
.work-experience-card {
  position: relative;
}

/* Tooltip wrapper uses absolute positioning */
.tooltip-wrapper {
  position: absolute;  /* NOT fixed */
  /* top and left set via inline styles */
}

/* Tooltip component has NO position property */
.company-tooltip {
  /* Defaults to static - works correctly in absolute wrapper */
}
```

## Key Learnings

### Browser Coordinate Systems
1. **Viewport Coordinates** (`getBoundingClientRect()`) - relative to browser window
2. **Document Coordinates** (`pageX/pageY`) - relative to entire page
3. **Element Offset** (`offsetTop/offsetLeft`) - relative to positioned parent
4. **Position: fixed** - positioned relative to viewport
5. **Position: absolute** - positioned relative to nearest positioned ancestor

**Critical Rule:** Match the coordinate system of your measurements with your positioning method!

### Debug Mode
Added `DEBUG_MODE` flag for troubleshooting:
- Set to `true`: Tooltips persist until manually closed (red X button)
- Shows debug overlay with positioning data
- Disables auto-hide on mouse leave
- Set to `false`: Normal behavior (auto-hide)

## Files Modified

1. **WorkExperienceCard.js** - Fixed positioning logic
   - Line 18: `DEBUG_MODE = false`
   - Lines 20-62: New positioning function using `offsetTop/offsetLeft`
   - Line 90: Removed scroll listener
   - Line 326: Changed from `position: fixed` to `position: absolute`

2. **CompanyTooltip.css** - Removed position conflict
   - Line 4: Removed `position: relative`

3. **WorkExperienceCard.css** - Removed specific position override
   - Line 187: Removed `position: relative` from `.tooltip-wrapper .company-tooltip`

4. **modals.css** - Fixed class name mismatch
   - Updated all BEM names to match React components

5. **App.css** - Removed duplicate modal CSS
   - Removed 112 lines of duplicate modal styles

## Testing Notes

Test tooltips by:
1. Hover over company names with enriched data
2. Tooltip appears to the right of company name
3. Scroll up/down - tooltip stays at initial position
4. Move mouse away - tooltip disappears after 200ms delay
5. Test on different scroll positions

## Debugging

To enable debug mode:
1. Set `DEBUG_MODE = true` in WorkExperienceCard.js line 18
2. Hover over company name
3. Check console for 📍 emoji logs
4. View green debug overlay above tooltip
5. Use red X button to close tooltip manually
