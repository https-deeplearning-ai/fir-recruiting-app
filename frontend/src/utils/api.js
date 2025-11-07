// API utility functions

/**
 * Auto-detect backend URL using smart heuristics
 *
 * Detection Strategy:
 * 1. Check for explicit override (REACT_APP_BACKEND_URL)
 * 2. Auto-detect from window.location for common patterns
 * 3. Check if we're in development (port 3000)
 * 4. Default to same-origin for production
 *
 * Examples:
 * - localhost:3000 -> http://localhost:5001 (dev)
 * - myapp.com -> '' (same origin, production)
 * - staging.myapp.com -> '' (same origin, staging)
 * - custom deployment -> REACT_APP_BACKEND_URL override
 */
export const getBackendUrl = () => {
  // Priority 1: Explicit override via environment variable
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }

  // Priority 2: Auto-detect from window.location
  const { protocol, hostname, port } = window.location;

  // Development: Detect React dev server (port 3000) -> point to backend port 5001
  if (hostname === 'localhost' && port === '3000') {
    return 'http://localhost:5001';
  }

  // Development: Detect 127.0.0.1 dev server
  if (hostname === '127.0.0.1' && port === '3000') {
    return 'http://127.0.0.1:5001';
  }

  // Production/Staging: Same origin (backend serves frontend static files)
  // Empty string means relative URLs like '/api/endpoint'
  return '';
};

/**
 * Build full API URL
 * @param {string} path - API path (e.g., '/research-companies')
 * @returns {string} Full URL
 */
export const buildApiUrl = (path) => {
  const base = getBackendUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
};
