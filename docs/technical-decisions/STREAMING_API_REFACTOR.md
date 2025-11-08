# Streaming API Modular Approach

## Overview
Created reusable utilities for SSE (Server-Sent Events) streaming and API endpoint management.

## Files Created

### 1. `src/utils/api.js`
**Purpose:** Centralized API URL management

**Key Functions:**
- `getBackendUrl()` - Smart environment-aware URL builder
  - Production: Returns empty string (same-origin, no CORS)
  - Development: Returns `http://localhost:5001`
  - Override: Respects `REACT_APP_BACKEND_URL` env var

- `buildApiUrl(path)` - Builds full API URLs
  ```javascript
  buildApiUrl('/research-companies/123/stream')
  // Dev: http://localhost:5001/research-companies/123/stream
  // Prod: /research-companies/123/stream
  ```

### 2. `src/hooks/useSSEStream.js`
**Purpose:** Reusable React hook for SSE connections

**Features:**
- ✅ Automatic connection management
- ✅ Error handling
- ✅ Auto-reconnect on conditions
- ✅ Stop conditions (completed, failed, etc.)
- ✅ Proper cleanup on unmount

**Usage Example:**
```javascript
import { useSSEStream } from './hooks/useSSEStream';

function CompanyResearch() {
  const [progress, setProgress] = useState(0);
  const [isStreaming, setIsStreaming] = useState(true);

  useSSEStream({
    url: `/research-companies/${sessionId}/stream`,
    enabled: isStreaming,
    onMessage: (data) => {
      if (data.session) {
        setProgress(data.session.progress_percentage);
      }
    },
    onError: (error) => {
      console.error('Stream error:', error);
      showNotification('Stream disconnected', 'error');
    },
    stopConditions: ['completed', 'failed', 'discovered']
  });
}
```

## Current Status

### ✅ Completed
1. Created modular utilities (`api.js`, `useSSEStream.js`)
2. Updated all company research endpoints to use `getBackendUrl()`
3. Fixed `/results` endpoint paths
4. Verified compilation

### 📋 TODO: Refactor Existing Streaming Code

**Current implementation** (lines ~3590-3690 in App.js):
```javascript
// Manual EventSource management
const streamUrl = `${getBackendUrl()}/research-companies/${id}/stream`;
const eventSource = new EventSource(streamUrl);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setCompanyResearchStatus(data.session);
  // ... lots of manual state management
};

eventSource.onerror = (event) => {
  // ... manual error handling
};
```

**Target implementation** (using useSSEStream):
```javascript
// Clean, declarative streaming
const { close } = useSSEStream({
  url: `/research-companies/${companySessionId}/stream`,
  enabled: companyResearching,
  onMessage: (data) => {
    if (data.session) {
      setCompanyResearchStatus(data.session);

      // Extract discovered companies during streaming
      if (data.session.search_config?.discovered_companies_list) {
        setDiscoveredCompanies(data.session.search_config.discovered_companies_list);
      }
    }
  },
  onError: (error) => {
    showNotification('Stream connection error', 'error');
    setCompanyResearching(false);
  },
  stopConditions: ['completed', 'failed', 'discovered']
});

// When streaming completes, fetch full results
useEffect(() => {
  if (companyResearchStatus.status === 'discovered') {
    fetchCompanyResults(companySessionId);
  }
}, [companyResearchStatus.status]);
```

## Benefits

1. **Reusability:** Same hook works for any SSE endpoint
2. **Maintainability:** All streaming logic in one place
3. **Consistency:** Same error handling, logging across app
4. **Testability:** Easier to mock and test
5. **Production-ready:** Automatic environment detection

## Future SSE Endpoints

If you add more streaming features (e.g., batch profile assessment streaming), just reuse the hook:

```javascript
useSSEStream({
  url: `/batch-assess/${batchId}/stream`,
  enabled: batchProcessing,
  onMessage: handleBatchUpdate,
  stopConditions: ['completed', 'failed']
});
```

## Environment Variables

**Development:** No configuration needed (defaults to localhost:5001)

**Production:** Set `REACT_APP_BACKEND_URL` if backend is on different origin
```bash
# .env.production
REACT_APP_BACKEND_URL=https://api.yourapp.com
```

**Same-origin deployment:** No env var needed (backend serves frontend)
