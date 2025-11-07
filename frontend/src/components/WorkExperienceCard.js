import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import CompanyTooltip from './CompanyTooltip';
import './WorkExperienceCard.css';

/**
 * WorkExperienceCard Component
 *
 * Displays a single work experience in LinkedIn-style format
 * with hoverable company name that shows enriched company data
 */
const WorkExperienceCard = ({ experience, index, onRegenerateUrl, onCrunchbaseClick, onEditUrl }) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const [modalVisible, setModalVisible] = useState(false);
  const hoverTimeoutRef = React.useRef(null);
  const targetElementRef = React.useRef(null); // Store the hovered element
  const [debugInfo, setDebugInfo] = useState(null); // Store debug information
  const DEBUG_MODE = false; // Set to true to enable debugging with persistent tooltips

  // Function to calculate tooltip position from target element
  const calculateTooltipPosition = () => {
    if (!targetElementRef.current) {
      console.log('❌ No target element reference');
      return;
    }

    // Use offsetTop/offsetLeft for position relative to parent card
    const targetElement = targetElementRef.current;
    const offsetTop = targetElement.offsetTop;
    const offsetLeft = targetElement.offsetLeft;

    // Constants for tooltip dimensions (matches CompanyTooltip.css)
    const HORIZONTAL_OFFSET = 250; // Fixed offset from left edge of company name

    // Simple positioning: always to the right with fixed offset from left edge
    let left = offsetLeft + HORIZONTAL_OFFSET;
    let top = offsetTop;

    console.log(`📍 ${experience.company_name}: offsetTop=${offsetTop}, offsetLeft=${offsetLeft}, top=${top}, left=${left}`);

    // Store debug info
    const debug = {
      offset: {
        top: offsetTop,
        left: offsetLeft
      },
      calculated: {
        top,
        left
      }
    };

    if (DEBUG_MODE) {
      console.log('🎯 TOOLTIP POSITIONING DEBUG:', {
        company: experience.company_name,
        ...debug
      });
      setDebugInfo(debug);
    }

    setTooltipPosition({ top, left });
  };

  // No scroll listener needed - tooltip stays at initial position

  const handleMouseEnter = (e) => {
    console.log('🖱️ HOVER: Mouse entered company name', experience.company_name);

    // Clear any pending hide timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    // Store the target element for position recalculation on scroll
    targetElementRef.current = e.target;

    // Calculate initial tooltip position
    calculateTooltipPosition();

    console.log('✅ HOVER: Setting tooltip visible to TRUE');
    setTooltipVisible(true);
  };

  const handleMouseLeave = () => {
    if (DEBUG_MODE) {
      console.log('🚪 Mouse left company name - tooltip will stay open in DEBUG_MODE');
      // In debug mode, don't auto-hide - let user manually close
      return;
    }
    // Add small delay before hiding to allow moving to tooltip
    hoverTimeoutRef.current = setTimeout(() => {
      setTooltipVisible(false);
      targetElementRef.current = null; // Clear reference when hiding
    }, 200);
  };

  const handleTooltipMouseEnter = () => {
    console.log('🖱️ Mouse entered tooltip');
    // Cancel hide if mouse enters tooltip
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
  };

  const handleTooltipMouseLeave = () => {
    if (DEBUG_MODE) {
      console.log('🚪 Mouse left tooltip - will stay open in DEBUG_MODE');
      // In debug mode, don't auto-hide
      return;
    }
    setTooltipVisible(false);
    targetElementRef.current = null; // Clear reference when hiding
  };

  const handleCloseTooltip = () => {
    console.log('❌ Manually closing tooltip');
    setTooltipVisible(false);
    targetElementRef.current = null;
    setDebugInfo(null);
  };

  const handleClick = (e) => {
    e.stopPropagation();
    setModalVisible(true);
    setTooltipVisible(false); // Hide tooltip when modal opens
    targetElementRef.current = null; // Clear reference
  };

  const handleCloseModal = (e) => {
    if (e) e.stopPropagation();
    setModalVisible(false);
  };

  const getStageIcon = (enrichedData) => {
    if (!enrichedData || !enrichedData.inferred_stage) return '🏢';

    const stage = enrichedData.inferred_stage.toLowerCase();
    if (stage.includes('seed')) return '🌱';
    if (stage.includes('series_a') || stage.includes('series a')) return '🚀';
    if (stage.includes('series_b') || stage.includes('series b')) return '📈';
    if (stage.includes('growth')) return '📊';
    if (stage.includes('public')) return '🏛️';
    if (stage.includes('mature')) return '🏢';
    return '💼';
  };

  const formatDuration = (duration) => {
    if (!duration) return '';
    return duration;
  };

  const formatDateRange = (exp) => {
    const startYear = exp.date_from_year || '';
    const startMonth = exp.date_from_month || '';
    const endYear = exp.date_to_year || '';
    const endMonth = exp.date_to_month || '';

    const start = startYear && startMonth ? `${getMonthName(startMonth)} ${startYear}` :
                  startYear ? startYear : '';
    const end = exp.is_current ? 'Present' :
                endYear && endMonth ? `${getMonthName(endMonth)} ${endYear}` :
                endYear ? endYear : 'Present';

    return `${start} - ${end}`;
  };

  const getMonthName = (month) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[parseInt(month) - 1] || '';
  };

  const hasEnrichedData = experience.company_enriched &&
    (experience.company_enriched.last_funding_type ||
     experience.company_enriched.type ||
     experience.company_enriched.hq_city ||
     experience.company_enriched.employees_count);

  // Debug logging
  React.useEffect(() => {
    console.log(`📊 Company: ${experience.company_name}`, {
      hasEnrichedData,
      enrichedData: experience.company_enriched,
      startYear: experience.date_from_year
    });
  }, []);

  return (
    <div className="work-experience-card">
      <div className="experience-icon">
        {hasEnrichedData && experience.company_enriched.logo_url ? (
          <img
            src={experience.company_enriched.logo_url}
            alt={`${experience.company_name} logo`}
            className="company-logo"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : null}
        <div className="fallback-icon" style={{ display: hasEnrichedData && experience.company_enriched.logo_url ? 'none' : 'flex' }}>
          {hasEnrichedData ? getStageIcon(experience.company_enriched) : '🏢'}
        </div>
      </div>

      <div className="experience-content">
        <div className="experience-header">
          <h4 className="experience-title">{experience.title || 'Unknown Role'}</h4>
          {experience.is_current && <span className="current-badge">Current</span>}
        </div>

        <div
          className={`company-name ${hasEnrichedData ? 'has-tooltip clickable' : ''}`}
          onMouseEnter={hasEnrichedData ? handleMouseEnter : null}
          onMouseLeave={hasEnrichedData ? handleMouseLeave : null}
          onClick={hasEnrichedData ? handleClick : null}
          style={hasEnrichedData ? { cursor: 'pointer' } : {}}
        >
          {experience.company_name || 'Unknown Company'}
          {hasEnrichedData && <span className="tooltip-indicator">ℹ️ Click for details</span>}
        </div>

        <div className="experience-dates">
          <span className="date-range">{formatDateRange(experience)}</span>
          {experience.duration && (
            <>
              <span className="date-separator">•</span>
              <span className="duration">{formatDuration(experience.duration)}</span>
            </>
          )}
        </div>

        {experience.location && (
          <div className="experience-location">
            📍 {experience.location}
          </div>
        )}

        {/* Quick Company Stats (if enriched) */}
        {hasEnrichedData && (
          <div className="company-quick-stats">
            {experience.company_enriched.last_funding_type && (
              <span className="quick-stat funding-stat">
                💰 {experience.company_enriched.last_funding_type}
              </span>
            )}
            {experience.company_enriched.employees_count && (
              <span className="quick-stat">
                👥 {experience.company_enriched.employees_count.toLocaleString()}
              </span>
            )}
            {experience.company_enriched.inferred_stage && !experience.company_enriched.last_funding_type && (
              <span className="quick-stat stage-stat">
                {getStageIcon(experience.company_enriched)}{' '}
                {experience.company_enriched.inferred_stage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            )}
          </div>
        )}

        {/* Company Data Freshness (if enriched) */}
        {hasEnrichedData && (experience.company_enriched.coresignal_last_updated || experience.company_enriched.from_storage !== undefined) && (
          <div className="company-freshness-box">
            {experience.company_enriched.coresignal_last_updated && (
              <div className="company-freshness-item">
                <span className="company-freshness-label">Data fetched from CoreSignal:</span>
                <span className="company-freshness-date">
                  {new Date(experience.company_enriched.coresignal_last_updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
              </div>
            )}
            {experience.company_enriched.from_storage ? (
              <div className="company-freshness-item">
                <span className="company-freshness-label">Stored in database:</span>
                <span className="company-freshness-date">
                  {experience.company_enriched.storage_age_days}d ago
                </span>
              </div>
            ) : (
              <div className="company-freshness-item">
                <span className="company-freshness-fresh">✨ Fresh from API</span>
              </div>
            )}
          </div>
        )}

        {experience.description && (
          <div className="experience-description">
            {experience.description}
          </div>
        )}
      </div>

      {/* Tooltip (on hover) */}
      {hasEnrichedData && tooltipVisible && !modalVisible && (
        <div
          className="tooltip-wrapper"
          style={{
            position: 'absolute',
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            zIndex: 'var(--z-tooltip, 9999)'
          }}
          onMouseEnter={handleTooltipMouseEnter}
          onMouseLeave={handleTooltipMouseLeave}
        >
          {/* Debug Mode: Close Button */}
          {DEBUG_MODE && (
            <button
              onClick={handleCloseTooltip}
              style={{
                position: 'absolute',
                top: '-10px',
                right: '-10px',
                width: '30px',
                height: '30px',
                borderRadius: '50%',
                background: '#ef4444',
                color: 'white',
                border: '2px solid white',
                fontSize: '18px',
                fontWeight: 'bold',
                cursor: 'pointer',
                zIndex: 10000,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
              }}
            >
              ✕
            </button>
          )}

          {/* Debug Mode: Positioning Debug Overlay */}
          {DEBUG_MODE && debugInfo && (
            <div
              style={{
                position: 'absolute',
                top: '-80px',
                left: '0',
                background: 'rgba(0, 0, 0, 0.9)',
                color: '#00ff00',
                padding: '8px 12px',
                borderRadius: '4px',
                fontSize: '11px',
                fontFamily: 'monospace',
                whiteSpace: 'pre',
                zIndex: 10001,
                maxWidth: '400px',
                border: '1px solid #00ff00',
                boxShadow: '0 2px 8px rgba(0,0,0,0.5)'
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '4px', color: '#ffff00' }}>
                🎯 {experience.company_name}
              </div>
              <div>Offset: top={Math.round(debugInfo.offset.top)} left={Math.round(debugInfo.offset.left)}</div>
              <div>Tooltip: top={Math.round(debugInfo.calculated.top)} left={Math.round(debugInfo.calculated.left)}</div>
            </div>
          )}

          <CompanyTooltip
            enrichedData={experience.company_enriched}
            companyName={experience.company_name}
            visible={tooltipVisible}
            companyId={experience.company_id}
            onRegenerateUrl={onRegenerateUrl}
            onCrunchbaseClick={onCrunchbaseClick}
            onEditUrl={onEditUrl}
          />
        </div>
      )}

      {/* Modal (on click) - Rendered via Portal at document root */}
      {hasEnrichedData && modalVisible && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content company-details-modal" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={handleCloseModal}>✕</button>
            <CompanyTooltip
              enrichedData={experience.company_enriched}
              companyName={experience.company_name}
              visible={true}
              companyId={experience.company_id}
              onRegenerateUrl={onRegenerateUrl}
              onCrunchbaseClick={onCrunchbaseClick}
              onEditUrl={onEditUrl}
            />
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default WorkExperienceCard;
