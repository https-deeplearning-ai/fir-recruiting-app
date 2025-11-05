import React from 'react';
import { TbRefresh } from "react-icons/tb";
import './CompanyTooltip.css';
import CrunchbaseEditModal from './CrunchbaseEditModal';

/**
 * CompanyTooltip Component
 *
 * Displays enriched company intelligence on hover
 * Shows: Company description, funding stage, amount raised, company type, HQ location, growth signals
 */
const CompanyTooltip = ({ enrichedData, companyName, visible, companyId, onRegenerateUrl, onCrunchbaseClick, onEditUrl }) => {
  const [showFullDescription, setShowFullDescription] = React.useState(false);
  const [isRegenerating, setIsRegenerating] = React.useState(false);
  const [clickedUrl, setClickedUrl] = React.useState(null);
  const [showEditModal, setShowEditModal] = React.useState(false);

  // DEBUG: Log Crunchbase URL presence
  if (enrichedData && visible) {
    console.log(`[CompanyTooltip] ${companyName}:`, {
      hasCrunchbaseUrl: !!enrichedData.crunchbase_company_url,
      crunchbaseUrl: enrichedData.crunchbase_company_url,
      allKeys: Object.keys(enrichedData)
    });
  }

  if (!enrichedData || !visible) return null;

  // Handler for regenerating Crunchbase URL
  const handleRegenerateUrl = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!onRegenerateUrl || isRegenerating) return;

    setIsRegenerating(true);
    try {
      await onRegenerateUrl(companyName, companyId, enrichedData.crunchbase_company_url);
    } catch (error) {
      console.error('Error regenerating URL:', error);
    } finally {
      setIsRegenerating(false);
    }
  };

  // Handler for clicking Crunchbase link
  const handleCrunchbaseClick = (e) => {
    // Don't prevent default - let the link open in new tab
    e.stopPropagation();

    const crunchbaseUrl = enrichedData.crunchbase_company_url || enrichedData.crunchbase_url;

    // Track the click for validation modal
    setClickedUrl(crunchbaseUrl);

    // Notify parent component after a delay (user will see the page first)
    if (onCrunchbaseClick) {
      setTimeout(() => {
        onCrunchbaseClick({
          companyId,
          companyName,
          crunchbaseUrl,
          source: enrichedData.crunchbase_source
        });
      }, 1000); // 1 second delay so modal doesn't block the new tab
    }
  };

  // Handler for editing Crunchbase URL
  const handleEditUrl = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowEditModal(true);
  };

  // Handler for saving edited URL
  const handleSaveEditedUrl = async (data) => {
    if (onEditUrl) {
      await onEditUrl(data);
    }
    setShowEditModal(false);
  };

  const formatFundingAmount = (amount) => {
    if (!amount) return null;
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    return `$${amount.toLocaleString()}`;
  };

  const getFundingStageIcon = (stage) => {
    if (!stage) return '🏢';
    const stageStr = stage.toLowerCase();
    if (stageStr.includes('seed')) return '🌱';
    if (stageStr.includes('series_a') || stageStr.includes('series a')) return '🚀';
    if (stageStr.includes('series_b') || stageStr.includes('series b')) return '📈';
    if (stageStr.includes('growth') || stageStr.includes('series_c') || stageStr.includes('series_d')) return '📊';
    if (stageStr.includes('public') || stageStr.includes('ipo')) return '🏛️';
    if (stageStr.includes('mature')) return '🏢';
    return '💼';
  };

  const getStageColor = (stage) => {
    if (!stage) return '#6c757d';
    const stageStr = stage.toLowerCase();
    if (stageStr.includes('seed')) return '#4CAF50';
    if (stageStr.includes('series_a') || stageStr.includes('series a')) return '#2196F3';
    if (stageStr.includes('series_b') || stageStr.includes('series b')) return '#FF9800';
    if (stageStr.includes('growth')) return '#9C27B0';
    if (stageStr.includes('public')) return '#607D8B';
    if (stageStr.includes('mature')) return '#795548';
    return '#6c757d';
  };

  const renderGrowthSignals = (signals) => {
    if (!signals || signals.length === 0) return null;

    const signalIcons = {
      'hypergrowth_potential': '🚀',
      'recently_funded': '💰',
      'b2b_model': '🏢',
      'modern_tech_stack': '⚙️',
      'strong_brand': '⭐'
    };

    const signalLabels = {
      'hypergrowth_potential': 'Hypergrowth',
      'recently_funded': 'Recently Funded',
      'b2b_model': 'B2B',
      'modern_tech_stack': 'Modern Tech',
      'strong_brand': 'Strong Brand'
    };

    return (
      <div className="growth-signals">
        {signals.map((signal, idx) => (
          <span key={idx} className="signal-badge">
            {signalIcons[signal] || '•'} {signalLabels[signal] || signal}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div className="company-tooltip">
      <div className="tooltip-header">
        <span className="tooltip-company-name">🏢 {companyName || enrichedData.name}</span>
      </div>

      <div className="tooltip-content">
        {/* Company Description - "What this company does" */}
        {enrichedData.description && (
          <div className="company-description-section">
            <div className="description-header">
              <span className="description-title">📝 What this company does</span>
            </div>
            <div className={`description-text ${showFullDescription ? 'expanded' : 'collapsed'}`}>
              {enrichedData.description}
            </div>
            {enrichedData.description.length > 200 && (
              <button
                className="show-more-btn"
                onClick={() => setShowFullDescription(!showFullDescription)}
              >
                {showFullDescription ? '▲ Show less' : '▼ Show more'}
              </button>
            )}
          </div>
        )}

        {/* Funding Information */}
        {enrichedData.last_funding_type && (
          <div className="tooltip-row funding-row">
            <span className="tooltip-icon">{getFundingStageIcon(enrichedData.inferred_stage)}</span>
            <span className="tooltip-label">Funding Stage:</span>
            <span
              className="tooltip-value funding-stage"
              style={{ color: getStageColor(enrichedData.inferred_stage) }}
            >
              {enrichedData.last_funding_type}
            </span>
          </div>
        )}

        {(enrichedData.last_funding_amount_formatted || enrichedData.last_funding_amount) && (
          <div className="tooltip-row">
            <span className="tooltip-icon">💰</span>
            <span className="tooltip-label">Amount Raised:</span>
            <span className="tooltip-value">
              {enrichedData.last_funding_amount_formatted || formatFundingAmount(enrichedData.last_funding_amount)}
            </span>
          </div>
        )}

        {enrichedData.total_funding_rounds && (
          <div className="tooltip-row">
            <span className="tooltip-icon">📊</span>
            <span className="tooltip-label">Total Rounds:</span>
            <span className="tooltip-value">{enrichedData.total_funding_rounds}</span>
          </div>
        )}

        {/* Company Type & Age */}
        {enrichedData.type && (
          <div className="tooltip-row">
            <span className="tooltip-icon">🏭</span>
            <span className="tooltip-label">Type:</span>
            <span className="tooltip-value">{enrichedData.type}</span>
          </div>
        )}

        {enrichedData.company_age_years && (
          <div className="tooltip-row">
            <span className="tooltip-icon">📅</span>
            <span className="tooltip-label">Founded:</span>
            <span className="tooltip-value">{enrichedData.company_age_years} years ago</span>
          </div>
        )}

        {/* Headquarters */}
        {(enrichedData.hq_city || enrichedData.hq_state) && (
          <div className="tooltip-row">
            <span className="tooltip-icon">📍</span>
            <span className="tooltip-label">HQ:</span>
            <span className="tooltip-value">
              {enrichedData.hq_city}
              {enrichedData.hq_city && enrichedData.hq_state && ', '}
              {enrichedData.hq_state}
            </span>
          </div>
        )}

        {/* Employee Count */}
        {enrichedData.employees_count && (
          <div className="tooltip-row">
            <span className="tooltip-icon">👥</span>
            <span className="tooltip-label">Employees:</span>
            <span className="tooltip-value">{enrichedData.employees_count.toLocaleString()}</span>
          </div>
        )}

        {/* Business Model */}
        {enrichedData.is_b2b !== undefined && (
          <div className="tooltip-row">
            <span className="tooltip-icon">💼</span>
            <span className="tooltip-label">Model:</span>
            <span className="tooltip-value">{enrichedData.is_b2b ? 'B2B' : 'B2C'}</span>
          </div>
        )}

        {/* Inferred Stage (if different from funding type) */}
        {enrichedData.inferred_stage && !enrichedData.last_funding_type && (
          <div className="tooltip-row">
            <span className="tooltip-icon">{getFundingStageIcon(enrichedData.inferred_stage)}</span>
            <span className="tooltip-label">Inferred Stage:</span>
            <span
              className="tooltip-value funding-stage"
              style={{ color: getStageColor(enrichedData.inferred_stage) }}
            >
              {enrichedData.inferred_stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>
        )}

        {/* Growth Signals */}
        {enrichedData.growth_signals && enrichedData.growth_signals.length > 0 && (
          <div className="tooltip-row signals-row">
            <span className="tooltip-label">Signals:</span>
            {renderGrowthSignals(enrichedData.growth_signals)}
          </div>
        )}

        {/* Company Links - ALL available links as colored pill buttons */}
        {(enrichedData.crunchbase_company_url ||
          enrichedData.crunchbase_funding_round_url ||
          enrichedData.crunchbase_url ||
          enrichedData.linkedin_company_url ||
          enrichedData.company_website) && (
          <div className="tooltip-row links-row">
            <span className="tooltip-icon">🔗</span>
            <span className="tooltip-label">Quick Links:</span>
            <div className="company-links-pills">
              {/* Crunchbase Company Page */}
              {enrichedData.crunchbase_source === 'not_found' ? (
                <div className="crunchbase-link-container">
                  <span className="link-pill crunchbase-pill crunchbase-not-found">
                    <span className="pill-icon">📊</span>
                    <span className="pill-text">Crunchbase: Not found</span>
                    <span className="inline-error" title="No Crunchbase profile found">✗</span>
                  </span>
                  <button
                    className="edit-btn-inline"
                    onClick={handleEditUrl}
                    title="Add Crunchbase URL manually"
                  >
                    ✎
                  </button>
                </div>
              ) : (enrichedData.crunchbase_company_url || enrichedData.crunchbase_url) && (
                <div className="crunchbase-link-container">
                  <a
                    href={enrichedData.crunchbase_company_url || enrichedData.crunchbase_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`link-pill crunchbase-pill ${
                      enrichedData.crunchbase_source === 'tavily_fallback' ||
                      enrichedData.crunchbase_source === 'tavily_single' ||
                      enrichedData.crunchbase_source === 'heuristic' ||
                      enrichedData.crunchbase_source === 'legacy'
                        ? 'crunchbase-uncertain'
                        : ''
                    }`}
                    onClick={handleCrunchbaseClick}
                    title="View company on Crunchbase"
                  >
                    <span className="pill-icon">📊</span>
                    <span className="pill-text">Crunchbase</span>
                    {/* Small inline indicator for CoreSignal verified */}
                    {enrichedData.crunchbase_source === 'coresignal' && (
                      <span className="inline-check" title="Verified by CoreSignal">✓</span>
                    )}
                    {/* Small inline indicator for AI-validated */}
                    {enrichedData.crunchbase_source === 'websearch_validated' && (
                      <span className="inline-check ai" title="Validated by AI WebSearch">✓</span>
                    )}
                    {/* Small inline indicator for user-verified */}
                    {enrichedData.crunchbase_source === 'user_verified' && (
                      <span className="inline-check user" title="Verified by User">✓</span>
                    )}
                    {/* Warning indicator for uncertain URLs */}
                    {(enrichedData.crunchbase_source === 'tavily_fallback' ||
                      enrichedData.crunchbase_source === 'tavily_single' ||
                      enrichedData.crunchbase_source === 'timeout_fallback') && (
                      <span className="inline-warning" title={`AI-Generated (${(enrichedData.crunchbase_confidence * 100).toFixed(0)}% confidence)`}>
                        ⚠️
                      </span>
                    )}
                    {(enrichedData.crunchbase_source === 'heuristic' ||
                      enrichedData.crunchbase_source === 'legacy') && (
                      <span className="inline-warning" title="Estimated URL">⚠️</span>
                    )}
                  </a>

                  {/* Deep Search button - only for uncertain URLs */}
                  {(enrichedData.crunchbase_source === 'tavily_fallback' ||
                    enrichedData.crunchbase_source === 'tavily_single' ||
                    enrichedData.crunchbase_source === 'timeout_fallback' ||
                    enrichedData.crunchbase_source === 'heuristic' ||
                    enrichedData.crunchbase_source === 'legacy') && onRegenerateUrl && (
                    <button
                      className={`regenerate-btn-inline ${isRegenerating ? 'loading' : ''}`}
                      onClick={handleRegenerateUrl}
                      disabled={isRegenerating}
                      title="Use Claude WebSearch to verify/correct this URL"
                    >
                      <TbRefresh size={14} />
                    </button>
                  )}

                  {/* Edit button - always show pencil icon for all URL states */}
                  <button
                    className="edit-btn-inline"
                    onClick={handleEditUrl}
                    title="Edit Crunchbase URL"
                  >
                    ✎
                  </button>
                </div>
              )}

              {/* Funding Round Details */}
              {enrichedData.crunchbase_funding_round_url &&
               enrichedData.crunchbase_funding_round_url !== enrichedData.crunchbase_company_url && (
                <a
                  href={enrichedData.crunchbase_funding_round_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-pill funding-pill"
                  onClick={(e) => e.stopPropagation()}
                  title={`View ${enrichedData.last_funding_type || 'funding round'} details`}
                >
                  <span className="pill-icon">💰</span>
                  <span className="pill-text">{enrichedData.last_funding_type || 'Funding'}</span>
                </a>
              )}

              {/* LinkedIn Company Page */}
              {enrichedData.linkedin_company_url && (
                <a
                  href={enrichedData.linkedin_company_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-pill linkedin-pill"
                  onClick={(e) => e.stopPropagation()}
                  title="View company on LinkedIn"
                >
                  <span className="pill-icon">💼</span>
                  <span className="pill-text">LinkedIn</span>
                </a>
              )}

              {/* Company Website */}
              {enrichedData.company_website && (
                <a
                  href={enrichedData.company_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-pill website-pill"
                  onClick={(e) => e.stopPropagation()}
                  title="Visit company website"
                >
                  <span className="pill-icon">🌐</span>
                  <span className="pill-text">Website</span>
                </a>
              )}
            </div>
          </div>
        )}

        {/* Company Data Freshness */}
        {(enrichedData.coresignal_last_updated || enrichedData.from_storage) && (
          <div className="tooltip-row company-freshness-row">
            <span className="tooltip-icon">📅</span>
            <div className="company-freshness-details">
              {enrichedData.coresignal_last_updated && (
                <div className="freshness-item-compact">
                  <span className="freshness-label-compact">Data fetched from CoreSignal:</span>
                  <span className="freshness-date-compact">
                    {new Date(enrichedData.coresignal_last_updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
              )}
              {enrichedData.from_storage && (
                <div className="freshness-item-compact">
                  <span className="freshness-label-compact">Stored in database:</span>
                  <span className="freshness-date-compact">
                    {enrichedData.storage_age_days}d ago
                  </span>
                </div>
              )}
              {!enrichedData.from_storage && (
                <div className="freshness-item-compact">
                  <span className="freshness-fresh-compact">✨ Fresh from API</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* No data message */}
      {!enrichedData.last_funding_type &&
       !enrichedData.type &&
       !enrichedData.hq_city &&
       !enrichedData.employees_count && (
        <div className="tooltip-no-data">
          <p>Limited company data available</p>
        </div>
      )}

      {/* Edit Modal */}
      <CrunchbaseEditModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        companyName={companyName}
        companyId={companyId}
        currentUrl={enrichedData.crunchbase_company_url}
        onSave={handleSaveEditedUrl}
      />
    </div>
  );
};

export default CompanyTooltip;
