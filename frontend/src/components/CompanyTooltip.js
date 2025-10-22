import React from 'react';
import './CompanyTooltip.css';

/**
 * CompanyTooltip Component
 *
 * Displays enriched company intelligence on hover
 * Shows: Company description, funding stage, amount raised, company type, HQ location, growth signals
 */
const CompanyTooltip = ({ enrichedData, companyName, visible }) => {
  const [showFullDescription, setShowFullDescription] = React.useState(false);

  if (!enrichedData || !visible) return null;

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
              {(enrichedData.crunchbase_company_url || enrichedData.crunchbase_url) && (
                <a
                  href={enrichedData.crunchbase_company_url || enrichedData.crunchbase_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-pill crunchbase-pill"
                  onClick={(e) => e.stopPropagation()}
                  title="View company on Crunchbase"
                >
                  <span className="pill-icon">📊</span>
                  <span className="pill-text">Crunchbase</span>
                </a>
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
    </div>
  );
};

export default CompanyTooltip;
