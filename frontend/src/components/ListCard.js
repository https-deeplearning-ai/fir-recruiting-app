// ListCard.js - Individual list card component
import React from 'react';

function ListCard({ list, onClick, onDelete }) {
  const {
    list_name,
    description,
    profile_count = 0,
    assessed_count = 0,
    created_at
  } = list;

  const assessedPercentage = profile_count > 0
    ? Math.round((assessed_count / profile_count) * 100)
    : 0;

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getStatusColor = () => {
    if (profile_count === 0) return '#94a3b8'; // Gray - empty
    if (assessed_count === 0) return '#f59e0b'; // Orange - not started
    if (assessed_count === profile_count) return '#10b981'; // Green - complete
    return '#3b82f6'; // Blue - in progress
  };

  const handleDelete = (e) => {
    e.stopPropagation(); // Prevent card click
    onDelete();
  };

  return (
    <div className="list-card" onClick={onClick}>
      <div className="list-card-header">
        <h3 className="list-card-title">{list_name}</h3>
        <button
          className="list-card-delete"
          onClick={handleDelete}
          title="Delete list"
        >
          ×
        </button>
      </div>

      {description && (
        <p className="list-card-description">{description}</p>
      )}

      <div className="list-card-stats">
        <div className="stat">
          <span className="stat-value">{profile_count}</span>
          <span className="stat-label">Profile{profile_count !== 1 ? 's' : ''}</span>
        </div>

        <div className="stat">
          <span className="stat-value">{assessed_count}</span>
          <span className="stat-label">Assessed</span>
        </div>

        <div className="stat">
          <span className="stat-value">{assessedPercentage}%</span>
          <span className="stat-label">Complete</span>
        </div>
      </div>

      <div className="list-card-progress">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{
              width: `${assessedPercentage}%`,
              backgroundColor: getStatusColor()
            }}
          />
        </div>
      </div>

      <div className="list-card-footer">
        <span className="list-card-date">Created {formatDate(created_at)}</span>
        <span className="list-card-action">
          {profile_count === 0 ? 'Empty list' : 'Open →'}
        </span>
      </div>
    </div>
  );
}

export default ListCard;
