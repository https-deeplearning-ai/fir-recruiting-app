import React, { useState } from 'react';
import { TbRefresh } from "react-icons/tb";
import './CrunchbaseValidationModal.css';

function CrunchbaseValidationModal({
  isOpen,
  onClose,
  companyName,
  crunchbaseUrl,
  companyId,
  onValidate,
  onRegenerate
}) {
  const [isIncorrect, setIsIncorrect] = useState(false);
  const [correctedUrl, setCorrectedUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCandidates, setShowCandidates] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isLoadingCandidates, setIsLoadingCandidates] = useState(false);

  if (!isOpen) return null;

  // Helper function to render confidence score as stars
  const renderStars = (score) => {
    const stars = Math.round(score * 5);
    return '⭐'.repeat(stars);
  };

  const handleCorrect = async () => {
    setIsSubmitting(true);
    try {
      await onValidate({
        companyId,
        isCorrect: true,
        verificationStatus: 'verified',
        correctedUrl: null,
        crunchbaseUrl  // CRITICAL: Pass the URL being verified so backend can save it
      });
      onClose();
    } catch (error) {
      console.error('Error validating URL:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleIncorrect = () => {
    setIsIncorrect(true);
  };

  const handleSubmitCorrection = async () => {
    setIsSubmitting(true);
    try {
      await onValidate({
        companyId,
        isCorrect: false,
        verificationStatus: 'needs_review',
        correctedUrl: correctedUrl.trim() || null
      });
      onClose();
      setIsIncorrect(false);
      setCorrectedUrl('');
    } catch (error) {
      console.error('Error submitting correction:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = async () => {
    setIsSubmitting(true);
    try {
      await onValidate({
        companyId,
        isCorrect: null,
        verificationStatus: 'skipped',
        correctedUrl: null
      });
      onClose();
    } catch (error) {
      console.error('Error skipping validation:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegenerate = async () => {
    if (!onRegenerate) return;
    setIsLoadingCandidates(true);
    try {
      // Call backend with return_candidates=true
      const response = await fetch('/regenerate-crunchbase-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: companyName,
          company_id: companyId,
          current_url: crunchbaseUrl,
          return_candidates: true
        })
      });

      const data = await response.json();

      if (data.success && data.candidates) {
        setCandidates(data.candidates);
        setShowCandidates(true);
        // Pre-select Claude's validated pick if available
        const claudePick = data.candidates.find(c => c.validated);
        if (claudePick) {
          setSelectedCandidate(claudePick.url);
        }
      } else {
        console.error('No candidates returned:', data);
        alert('Could not find alternative Crunchbase URLs');
      }
    } catch (error) {
      console.error('Error fetching candidates:', error);
      alert('Failed to fetch alternative URLs');
    } finally {
      setIsLoadingCandidates(false);
    }
  };

  const handleConfirmCandidate = async () => {
    if (!selectedCandidate) return;

    setIsSubmitting(true);
    try {
      // If user selected one of the candidates, validate it
      if (selectedCandidate !== 'NONE' && selectedCandidate !== 'NO_URL') {
        await onValidate({
          companyId,
          isCorrect: true,
          verificationStatus: 'verified',
          correctedUrl: null,
          crunchbaseUrl: selectedCandidate
        });
      } else if (selectedCandidate === 'NO_URL') {
        // User indicated no Crunchbase URL exists - remove it
        await onValidate({
          companyId,
          isCorrect: false,
          verificationStatus: 'no_url_exists',
          correctedUrl: null
        });
      } else {
        // User selected "None of these are correct" - skip
        await onValidate({
          companyId,
          isCorrect: null,
          verificationStatus: 'skipped',
          correctedUrl: null
        });
      }
      onClose();
    } catch (error) {
      console.error('Error confirming candidate:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelCandidates = () => {
    setShowCandidates(false);
    setCandidates([]);
    setSelectedCandidate(null);
  };

  const handleCancel = () => {
    setIsIncorrect(false);
    setCorrectedUrl('');
    onClose();
  };

  return (
    <div className="validation-modal-overlay" onClick={handleCancel}>
      <div className="validation-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={handleCancel}>×</button>

        {showCandidates ? (
          /* Candidate Selection View */
          <>
            <h3 className="modal-title">Select Correct Crunchbase Profile</h3>
            <p className="modal-description">
              Choose the correct Crunchbase profile for <strong>{companyName}</strong>:
            </p>

            {isLoadingCandidates ? (
              <div className="modal-loading">
                <TbRefresh size={32} className="spinner" />
                <p>Searching for alternatives...</p>
              </div>
            ) : (
              <>
                <div className="candidate-list">
                  {candidates.map((candidate, index) => (
                    <label
                      key={index}
                      className={`candidate-option ${selectedCandidate === candidate.url ? 'selected' : ''} ${candidate.validated ? 'validated' : ''}`}
                    >
                      <input
                        type="radio"
                        name="candidate"
                        value={candidate.url}
                        checked={selectedCandidate === candidate.url}
                        onChange={() => setSelectedCandidate(candidate.url)}
                      />
                      <div className="candidate-info">
                        <div className="candidate-title">{candidate.title}</div>
                        <div className="candidate-url">{candidate.url}</div>
                        <div className="candidate-score">
                          {renderStars(candidate.score)} {(candidate.score * 100).toFixed(0)}%
                          {candidate.validated && <span className="validated-badge">Claude Pick</span>}
                        </div>
                      </div>
                    </label>
                  ))}

                  <label className={`candidate-option skip-option ${selectedCandidate === 'NONE' ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="candidate"
                      value="NONE"
                      checked={selectedCandidate === 'NONE'}
                      onChange={() => setSelectedCandidate('NONE')}
                    />
                    <div className="candidate-info">
                      <div className="candidate-title">None of these are correct</div>
                      <div className="candidate-subtitle">Skip for now</div>
                    </div>
                  </label>

                  <label className={`candidate-option skip-option ${selectedCandidate === 'NO_URL' ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="candidate"
                      value="NO_URL"
                      checked={selectedCandidate === 'NO_URL'}
                      onChange={() => setSelectedCandidate('NO_URL')}
                    />
                    <div className="candidate-info">
                      <div className="candidate-title">No Crunchbase URL exists for this company</div>
                      <div className="candidate-subtitle">Remove URL from profile</div>
                    </div>
                  </label>
                </div>

                <div className="modal-actions">
                  <button
                    className="modal-btn modal-btn-submit"
                    onClick={handleConfirmCandidate}
                    disabled={!selectedCandidate || isSubmitting}
                  >
                    {isSubmitting ? 'Saving...' : 'Confirm Selection'}
                  </button>
                  <button
                    className="modal-btn modal-btn-cancel"
                    onClick={handleCancelCandidates}
                    disabled={isSubmitting}
                  >
                    Back
                  </button>
                </div>
              </>
            )}
          </>
        ) : !isIncorrect ? (
          <>
            <h3 className="modal-title">Verify Crunchbase Profile</h3>
            <p className="modal-description">
              Did this link take you to the correct Crunchbase profile for <strong>{companyName}</strong>?
            </p>
            <div className="modal-url-display">
              {crunchbaseUrl}
            </div>

            <div className="modal-actions">
              <button
                className="modal-btn modal-btn-correct"
                onClick={handleCorrect}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Saving...' : 'Yes, Correct'}
              </button>
              <button
                className="modal-btn modal-btn-incorrect"
                onClick={handleIncorrect}
                disabled={isSubmitting}
              >
                No, Incorrect
              </button>
              <button
                className="modal-btn modal-btn-skip"
                onClick={handleSkip}
                disabled={isSubmitting}
              >
                Skip
              </button>
              {onRegenerate && (
                <button
                  className="modal-btn modal-btn-regenerate"
                  onClick={handleRegenerate}
                  disabled={isSubmitting || isLoadingCandidates}
                  title="Use Claude WebSearch to find correct URL"
                >
                  <TbRefresh size={16} style={{marginRight: '6px'}} />
                  {isLoadingCandidates ? 'Searching...' : 'Regenerate'}
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            <h3 className="modal-title">Provide Correct URL</h3>
            <p className="modal-description">
              We'll use your correction to improve future results. Enter the correct Crunchbase URL for <strong>{companyName}</strong>:
            </p>

            <div className="modal-input-group">
              <label htmlFor="corrected-url">Correct Crunchbase URL (optional)</label>
              <input
                id="corrected-url"
                type="url"
                className="modal-url-input"
                placeholder="https://www.crunchbase.com/organization/..."
                value={correctedUrl}
                onChange={(e) => setCorrectedUrl(e.target.value)}
                autoFocus
              />
              <small className="input-hint">
                Leave blank if you don't have the correct URL right now
              </small>
            </div>

            <div className="modal-actions">
              <button
                className="modal-btn modal-btn-submit"
                onClick={handleSubmitCorrection}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Correction'}
              </button>
              <button
                className="modal-btn modal-btn-cancel"
                onClick={handleCancel}
                disabled={isSubmitting}
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default CrunchbaseValidationModal;
