// ListsView.js - Dashboard view showing all candidate lists
import React, { useState, useEffect } from 'react';
import ListCard from './ListCard';
import ListDetail from './ListDetail';
import './ListsView.css';

function ListsView({ recruiterName, showNotification }) {
  const [lists, setLists] = useState([]);
  const [selectedList, setSelectedList] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState('dashboard'); // 'dashboard' or 'detail'

  // Fetch lists on mount and when recruiterName changes
  useEffect(() => {
    if (recruiterName) {
      fetchLists();
    }
  }, [recruiterName]);

  const fetchLists = async () => {
    if (!recruiterName) {
      setError('Please enter your recruiter name at the top');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/extension/lists?recruiter_name=${encodeURIComponent(recruiterName)}`);

      if (!response.ok) {
        throw new Error('Failed to fetch lists');
      }

      const data = await response.json();
      setLists(data.lists || data); // Handle both {lists: [...]} and [...] responses
    } catch (err) {
      setError(err.message || 'Failed to fetch lists');
      console.error('Error fetching lists:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectList = (list) => {
    setSelectedList(list);
    setView('detail');
  };

  const handleBackToLists = () => {
    setView('dashboard');
    setSelectedList(null);
    fetchLists(); // Refresh lists when returning to dashboard
  };

  const handleDeleteList = async (listId) => {
    if (!window.confirm('Are you sure you want to delete this list? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/extension/lists/${listId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete list');
      }

      showNotification('List deleted successfully', 'success');
      fetchLists(); // Refresh lists
    } catch (err) {
      showNotification(err.message || 'Failed to delete list', 'error');
      console.error('Error deleting list:', err);
    }
  };

  // Show list detail view
  if (view === 'detail' && selectedList) {
    return (
      <ListDetail
        list={selectedList}
        recruiterName={recruiterName}
        onBack={handleBackToLists}
        showNotification={showNotification}
      />
    );
  }

  // Show lists dashboard
  return (
    <div className="lists-view">
      <div className="lists-header">
        <h2>Your Candidate Lists</h2>
        <button
          className="refresh-btn"
          onClick={fetchLists}
          disabled={loading}
        >
          {loading ? '↻ Loading...' : '↻ Refresh'}
        </button>
      </div>

      {error && (
        <div className="lists-error">
          <p>{error}</p>
          {error.includes('recruiter name') && (
            <p className="hint">Enter your name in the "Recruiter" field at the top of the page</p>
          )}
        </div>
      )}

      {!recruiterName && !loading && (
        <div className="lists-placeholder">
          <div className="placeholder-icon">📋</div>
          <h3>Enter Your Name to Get Started</h3>
          <p>Enter your recruiter name at the top of the page to view your lists</p>
        </div>
      )}

      {recruiterName && !loading && !error && lists.length === 0 && (
        <div className="lists-placeholder">
          <div className="placeholder-icon">🔖</div>
          <h3>No Lists Yet</h3>
          <p>Start using the Chrome extension to bookmark LinkedIn profiles!</p>
          <div className="placeholder-steps">
            <div className="step">
              <span className="step-number">1</span>
              <p>Install the Chrome extension</p>
            </div>
            <div className="step">
              <span className="step-number">2</span>
              <p>Browse LinkedIn profiles</p>
            </div>
            <div className="step">
              <span className="step-number">3</span>
              <p>Click the extension icon and add to a list</p>
            </div>
            <div className="step">
              <span className="step-number">4</span>
              <p>Come back here to view and assess candidates</p>
            </div>
          </div>
        </div>
      )}

      {recruiterName && !loading && lists.length > 0 && (
        <div className="lists-grid">
          {lists.map(list => (
            <ListCard
              key={list.id}
              list={list}
              onClick={() => handleSelectList(list)}
              onDelete={() => handleDeleteList(list.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ListsView;
