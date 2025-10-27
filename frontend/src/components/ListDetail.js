// ListDetail.js - Detailed view of profiles in a list
import React, { useState, useEffect } from 'react';

function ListDetail({ list, recruiterName, onBack, showNotification }) {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [assessing, setAssessing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProfiles();
  }, [list.id]);

  const fetchProfiles = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/extension/profiles/${list.id}`);

      if (!response.ok) {
        throw new Error('Failed to fetch profiles');
      }

      const data = await response.json();
      setProfiles(data.profiles || data);
    } catch (err) {
      setError(err.message || 'Failed to fetch profiles');
      console.error('Error fetching profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAssessAll = async () => {
    const unassessedCount = profiles.filter(p => !p.assessed).length;

    if (unassessedCount === 0) {
      showNotification('All profiles are already assessed!', 'info');
      return;
    }

    if (!window.confirm(`This will assess ${unassessedCount} profile${unassessedCount !== 1 ? 's' : ''}. This may take a few minutes and use API credits. Continue?`)) {
      return;
    }

    setAssessing(true);
    showNotification(`Assessing ${unassessedCount} profiles... This may take a few minutes.`, 'info');

    try {
      const response = await fetch(`/lists/${list.id}/assess`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          requirements: [
            {
              name: 'Relevant Experience',
              description: 'Experience relevant to the role',
              weight: 40
            },
            {
              name: 'Career Trajectory',
              description: 'Career growth and progression',
              weight: 30
            }
          ]
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to assess profiles');
      }

      const result = await response.json();

      showNotification(
        `Successfully assessed ${result.assessed || 0} profile${result.assessed !== 1 ? 's' : ''}! Average score: ${result.avg_score?.toFixed(1) || 'N/A'}`,
        'success'
      );

      // Refresh profiles to show new scores
      await fetchProfiles();
    } catch (err) {
      showNotification(err.message || 'Failed to assess profiles', 'error');
      console.error('Error assessing profiles:', err);
    } finally {
      setAssessing(false);
    }
  };

  const handleExportCSV = async () => {
    const assessedCount = profiles.filter(p => p.assessed).length;

    if (assessedCount === 0) {
      showNotification('No assessed profiles to export. Assess profiles first!', 'error');
      return;
    }

    try {
      const response = await fetch(`/lists/${list.id}/export-csv?recruiter_name=${encodeURIComponent(recruiterName)}`);

      if (!response.ok) {
        throw new Error('Failed to export CSV');
      }

      // Trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${list.list_name.replace(/\s+/g, '-').toLowerCase()}-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showNotification('CSV exported successfully!', 'success');
    } catch (err) {
      showNotification(err.message || 'Failed to export CSV', 'error');
      console.error('Error exporting CSV:', err);
    }
  };

  const handleRemoveProfile = async (profileId) => {
    if (!window.confirm('Remove this profile from the list?')) {
      return;
    }

    try {
      const response = await fetch(`/extension/profiles/${profileId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to remove profile');
      }

      showNotification('Profile removed from list', 'success');
      await fetchProfiles(); // Refresh list
    } catch (err) {
      showNotification(err.message || 'Failed to remove profile', 'error');
      console.error('Error removing profile:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const assessedProfiles = profiles.filter(p => p.assessed);
  const unassessedProfiles = profiles.filter(p => !p.assessed);

  return (
    <div className="list-detail">
      <div className="list-detail-header">
        <button className="back-btn" onClick={onBack}>
          ← Back to Lists
        </button>

        <div className="list-detail-title">
          <h2>{list.list_name}</h2>
          {list.description && <p className="list-description">{list.description}</p>}
        </div>

        <div className="list-detail-actions">
          {unassessedProfiles.length > 0 && (
            <button
              className="assess-all-btn"
              onClick={handleAssessAll}
              disabled={assessing}
            >
              {assessing ? 'Assessing...' : `Assess ${unassessedProfiles.length} Unassessed`}
            </button>
          )}

          {assessedProfiles.length > 0 && (
            <button
              className="export-csv-btn"
              onClick={handleExportCSV}
            >
              Export CSV ({assessedProfiles.length})
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="list-detail-error">
          <p>{error}</p>
        </div>
      )}

      {loading && (
        <div className="list-detail-loading">
          <div className="list-loading-spinner"></div>
          <p>Loading profiles...</p>
        </div>
      )}

      {!loading && !error && profiles.length === 0 && (
        <div className="list-detail-empty">
          <div className="empty-icon">📝</div>
          <h3>No Profiles Yet</h3>
          <p>Use the Chrome extension to add LinkedIn profiles to this list</p>
        </div>
      )}

      {!loading && !error && profiles.length > 0 && (
        <div className="list-detail-profiles">
          {/* Assessed Profiles */}
          {assessedProfiles.length > 0 && (
            <div className="profiles-section">
              <h3 className="section-title">
                ✅ Assessed ({assessedProfiles.length})
              </h3>
              <div className="profiles-list">
                {assessedProfiles.map(profile => (
                  <div key={profile.id} className="profile-card">
                    <div className="profile-card-header">
                      <div className="profile-info">
                        <h4 className="profile-name">{profile.name}</h4>
                        <p className="profile-headline">{profile.headline || 'No headline'}</p>
                        {profile.location && (
                          <p className="profile-location">📍 {profile.location}</p>
                        )}
                      </div>
                      <div className="profile-score">
                        <span className="score-value">{Math.round(profile.assessment_score)}</span>
                        <span className="score-label">/100</span>
                      </div>
                    </div>

                    <div className="profile-card-footer">
                      <span className="profile-added">Added {formatDate(profile.added_at)}</span>
                      <div className="profile-actions">
                        <a
                          href={profile.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="profile-link"
                        >
                          View LinkedIn
                        </a>
                        <button
                          className="profile-remove"
                          onClick={() => handleRemoveProfile(profile.id)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unassessed Profiles */}
          {unassessedProfiles.length > 0 && (
            <div className="profiles-section">
              <h3 className="section-title">
                ⏳ Not Assessed ({unassessedProfiles.length})
              </h3>
              <div className="profiles-list">
                {unassessedProfiles.map(profile => (
                  <div key={profile.id} className="profile-card unassessed">
                    <div className="profile-card-header">
                      <div className="profile-info">
                        <h4 className="profile-name">{profile.name}</h4>
                        <p className="profile-headline">{profile.headline || 'No headline'}</p>
                        {profile.location && (
                          <p className="profile-location">📍 {profile.location}</p>
                        )}
                      </div>
                      <div className="profile-status">
                        <span className="status-badge">Pending</span>
                      </div>
                    </div>

                    <div className="profile-card-footer">
                      <span className="profile-added">Added {formatDate(profile.added_at)}</span>
                      <div className="profile-actions">
                        <a
                          href={profile.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="profile-link"
                        >
                          View LinkedIn
                        </a>
                        <button
                          className="profile-remove"
                          onClick={() => handleRemoveProfile(profile.id)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ListDetail;
