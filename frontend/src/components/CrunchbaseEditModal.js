import React, { useState } from 'react';
import './CrunchbaseEditModal.css';

function CrunchbaseEditModal({
  isOpen,
  onClose,
  companyName,
  companyId,
  currentUrl,
  onSave
}) {
  const [urlInput, setUrlInput] = useState(currentUrl || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const extractSlug = (input) => {
    if (!input || input.trim() === '') return '';

    // If input is just a slug (no slashes)
    if (!input.includes('/')) {
      return input.trim();
    }

    // Extract slug from full URL
    const match = input.match(/crunchbase\.com\/organization\/([a-z0-9-]+)/i);
    if (match) {
      return match[1];
    }

    return '';
  };

  const handleSave = async () => {
    setError('');
    const slug = extractSlug(urlInput);

    if (!slug && urlInput.trim() !== '') {
      setError('Invalid Crunchbase URL. Please enter a valid organization URL or slug.');
      return;
    }

    setIsSubmitting(true);
    try {
      const fullUrl = slug ? `https://www.crunchbase.com/organization/${slug}` : null;

      await onSave({
        companyId,
        crunchbaseUrl: fullUrl,
        isCorrect: true,
        verificationStatus: 'verified',
        correctedUrl: fullUrl
      });

      onClose();
    } catch (err) {
      setError('Failed to save URL. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleMarkAsNotFound = async () => {
    setIsSubmitting(true);
    try {
      await onSave({
        companyId,
        crunchbaseUrl: null,
        isCorrect: false,
        verificationStatus: 'not_found',
        correctedUrl: null
      });

      onClose();
    } catch (err) {
      setError('Failed to mark as not found. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSearchCrunchbase = () => {
    const searchQuery = encodeURIComponent(companyName);
    window.open(`https://www.crunchbase.com/search/organizations/field/organizations/name/${searchQuery}`, '_blank');
  };

  return (
    <div className="crunchbase-edit-modal-overlay" onClick={onClose}>
      <div className="crunchbase-edit-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="crunchbase-edit-modal-header">
          <h3>✎ Edit Crunchbase URL</h3>
          <button className="crunchbase-edit-modal-close" onClick={onClose}>×</button>
        </div>

        <div className="crunchbase-edit-modal-body">
          <div className="company-name">
            Company: <strong>{companyName}</strong>
          </div>

          <div className="form-group">
            <label>Enter Crunchbase slug or full URL:</label>
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="rex-technologies"
              className={error ? 'error' : ''}
              disabled={isSubmitting}
            />
            {error && <div className="error-message">{error}</div>}
          </div>

          <div className="help-text">
            💡 <strong>Tip:</strong> Search on Crunchbase.com first to find the
            correct profile, then copy the slug here.
            <br />
            <strong>Example:</strong> From <code>crunchbase.com/organization/rex-technologies</code>,
            enter <code>rex-technologies</code>
          </div>

          <div className="crunchbase-edit-modal-actions">
            <button
              className="btn-secondary"
              onClick={handleSearchCrunchbase}
              disabled={isSubmitting}
            >
              🔍 Search Crunchbase.com
            </button>

            <button
              className="btn-danger"
              onClick={handleMarkAsNotFound}
              disabled={isSubmitting}
            >
              ✗ No URL exists
            </button>
          </div>

          <div className="crunchbase-edit-modal-footer">
            <button
              className="btn-cancel"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CrunchbaseEditModal;
