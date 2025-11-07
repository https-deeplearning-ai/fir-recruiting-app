import React from 'react';
import WorkExperienceCard from './WorkExperienceCard';
import './WorkExperienceSection.css';

/**
 * WorkExperienceSection Component
 *
 * Displays all work experiences in a LinkedIn-style layout
 * Integrates with enriched company data for tooltips
 */
const WorkExperienceSection = ({ profileData, profileSummary, onRegenerateUrl, onCrunchbaseClick, onEditUrl }) => {
  // Extract experiences from either profileSummary or profileData
  let experiences = [];

  if (profileSummary && profileSummary.experiences) {
    experiences = profileSummary.experiences;
  } else if (profileData && profileData.experience) {
    experiences = profileData.experience;
  }

  if (!experiences || experiences.length === 0) {
    return null;
  }

  const totalYears = profileSummary?.total_experience_years || 0;

  return (
    <div className="work-experience-section">
      <div className="section-header">
        <h3 className="section-title">
          💼 Work Experience
          {totalYears > 0 && (
            <span className="total-years"> ({totalYears} years total)</span>
          )}
        </h3>
        <div className="section-subtitle">
          {experiences.length} {experiences.length === 1 ? 'position' : 'positions'}
        </div>
      </div>

      <div className="experiences-list">
        {experiences.map((exp, index) => (
          <WorkExperienceCard
            key={index}
            experience={exp}
            index={index}
            onRegenerateUrl={onRegenerateUrl}
            onCrunchbaseClick={onCrunchbaseClick}
            onEditUrl={onEditUrl}
          />
        ))}
      </div>

      {/* Enrichment Stats (if available) */}
      {profileSummary && (
        <div className="experience-stats">
          {profileSummary.total_experiences && (
            <div className="stat-item">
              <span className="stat-label">Total Positions:</span>
              <span className="stat-value">{profileSummary.total_experiences}</span>
            </div>
          )}
          {profileSummary.total_experience_years && (
            <div className="stat-item">
              <span className="stat-label">Total Years:</span>
              <span className="stat-value">{profileSummary.total_experience_years} yrs</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkExperienceSection;
