import React, { useState } from 'react';
import CompanyTooltip from './CompanyTooltip';
import './WorkExperienceCard.css';

/**
 * WorkExperienceCard Component
 *
 * Displays a single work experience in LinkedIn-style format
 * with hoverable company name that shows enriched company data
 */
const WorkExperienceCard = ({ experience, index }) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const [modalVisible, setModalVisible] = useState(false);
  const hoverTimeoutRef = React.useRef(null);

  const handleMouseEnter = (e) => {
    console.log('🖱️ HOVER: Mouse entered company name', experience.company_name);

    // Clear any pending hide timeout
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    const rect = e.target.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    const spaceBelow = viewportHeight - rect.bottom;

    // Constants for tooltip dimensions
    const TOOLTIP_WIDTH = 420;

    // Always show below for simplicity (tooltips grow downward from top position)
    // This avoids complex "show above" calculations
    let top = rect.bottom + 8;
    console.log('📍 HOVER: Showing tooltip BELOW company name');

    // Calculate horizontal position (prevent going off-screen)
    let left = rect.left;
    if (left + TOOLTIP_WIDTH > viewportWidth) {
      left = viewportWidth - TOOLTIP_WIDTH - 20; // 20px margin from right edge
    }
    left = Math.max(8, left); // Prevent going off left edge

    console.log('📍 HOVER: Final position (viewport coordinates)', { top, left });
    console.log('✅ HOVER: Setting tooltip visible to TRUE');

    setTooltipPosition({
      top: top,
      left: left
    });
    setTooltipVisible(true);
  };

  const handleMouseLeave = () => {
    // Add small delay before hiding to allow moving to tooltip
    hoverTimeoutRef.current = setTimeout(() => {
      setTooltipVisible(false);
    }, 200);
  };

  const handleTooltipMouseEnter = () => {
    // Cancel hide if mouse enters tooltip
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
  };

  const handleTooltipMouseLeave = () => {
    setTooltipVisible(false);
  };

  const handleClick = (e) => {
    e.stopPropagation();
    setModalVisible(true);
    setTooltipVisible(false); // Hide tooltip when modal opens
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
        {hasEnrichedData ? getStageIcon(experience.company_enriched) : '🏢'}
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
            position: 'fixed',
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            zIndex: 9999
          }}
          onMouseEnter={handleTooltipMouseEnter}
          onMouseLeave={handleTooltipMouseLeave}
        >
          <CompanyTooltip
            enrichedData={experience.company_enriched}
            companyName={experience.company_name}
            visible={tooltipVisible}
          />
        </div>
      )}

      {/* Modal (on click) */}
      {hasEnrichedData && modalVisible && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={handleCloseModal}>✕</button>
            <CompanyTooltip
              enrichedData={experience.company_enriched}
              companyName={experience.company_name}
              visible={true}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkExperienceCard;
