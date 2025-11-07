import { useEffect, useRef, useCallback } from 'react';
import { buildApiUrl } from '../utils/api';

/**
 * Custom hook for Server-Sent Events (SSE) streaming
 *
 * @param {Object} options - Configuration options
 * @param {string} options.url - SSE endpoint URL (relative path)
 * @param {boolean} options.enabled - Whether streaming is active
 * @param {Function} options.onMessage - Callback for messages (data) => void
 * @param {Function} options.onError - Callback for errors (error) => void
 * @param {Function} options.onOpen - Callback when connection opens () => void
 * @param {Function} options.onClose - Callback when connection closes () => void
 * @param {Array} options.stopConditions - Array of status values that should stop streaming
 *
 * @returns {Object} - { close: function to manually close stream }
 *
 * @example
 * const { close } = useSSEStream({
 *   url: `/research-companies/${sessionId}/stream`,
 *   enabled: isStreaming,
 *   onMessage: (data) => {
 *     if (data.session) {
 *       setProgress(data.session.progress_percentage);
 *     }
 *   },
 *   onError: (error) => console.error('Stream error:', error),
 *   stopConditions: ['completed', 'failed']  // Valid: completed, failed
 * });
 */
export const useSSEStream = ({
  url,
  enabled = false,
  onMessage,
  onError,
  onOpen,
  onClose,
  stopConditions = []
}) => {
  const eventSourceRef = useRef(null);
  const lastStatusRef = useRef(null);

  // Close stream function
  const close = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('[SSE] Closing connection:', url);
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      if (onClose) onClose();
    }
  }, [url, onClose]);

  useEffect(() => {
    // Don't start if not enabled or URL is missing
    if (!enabled || !url) {
      return;
    }

    // Build full URL for SSE connection
    const streamUrl = buildApiUrl(url);
    console.log('[SSE] Opening connection:', streamUrl);

    // Create EventSource connection
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    // Connection opened
    eventSource.onopen = (event) => {
      console.log('[SSE] ✅ Connection opened');
      if (onOpen) onOpen(event);
    };

    // Handle messages
    eventSource.onmessage = (event) => {
      console.log('[SSE] 📨 Message received:', event.data);

      try {
        const data = JSON.parse(event.data);

        // Check stop conditions
        if (data.session?.status) {
          const status = data.session.status;

          // Stop streaming if status matches stop condition
          if (stopConditions.includes(status)) {
            console.log('[SSE] Stop condition met:', status);
            close();
          }

          lastStatusRef.current = status;
        }

        // Call message handler
        if (onMessage) {
          onMessage(data);
        }
      } catch (err) {
        console.error('[SSE] Failed to parse message:', err);
        if (onError) onError(err);
      }
    };

    // Handle errors
    eventSource.onerror = (event) => {
      console.error('[SSE] ❌ Error:', event);
      console.error('[SSE] ReadyState:', eventSource.readyState);

      // ReadyState 2 = CLOSED
      if (eventSource.readyState === 2) {
        console.error('[SSE] Connection closed by server');
        close();
      }

      if (onError) {
        onError(event);
      }
    };

    // Cleanup on unmount or when dependencies change
    return () => {
      console.log('[SSE] Cleaning up connection');
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [url, enabled, onMessage, onError, onOpen, close, stopConditions]);

  return { close };
};
