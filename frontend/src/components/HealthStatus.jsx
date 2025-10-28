
import { useState, useEffect } from 'react';
import { ragAPI } from '../services/api';

const HealthStatus = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const response = await ragAPI.getHealth();
      setHealth(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch health status');
      console.error('Health check error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return <div className="loading">Loading health status...</div>;
  }

  if (error && !health) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="card">
      <h2>System Health</h2>
      {error && <div className="error">{error}</div>}
      <div className="health-status">
        <div className="health-item">
          <div className="label">Status</div>
          <div className="value">
            <span className={`status ${health?.status === 'healthy' ? 'status-healthy' : 'status-unhealthy'}`}>
              {health?.status || 'unknown'}
            </span>
          </div>
        </div>
        <div className="health-item">
          <div className="label">Vector Index</div>
          <div className="value">{health?.vector_index_loaded ? 'Loaded' : 'Not Loaded'}</div>
        </div>
        <div className="health-item">
          <div className="label">Vectors</div>
          <div className="value">{health?.vector_count || 0}</div>
        </div>
        <div className="health-item">
          <div className="label">Raw Docs</div>
          <div className="value">{health?.raw_documents || 0}</div>
        </div>
        <div className="health-item">
          <div className="label">Clean Docs</div>
          <div className="value">{health?.clean_documents || 0}</div>
        </div>
      </div>
      <button onClick={fetchHealth} className="btn" style={{ marginTop: '15px' }}>
        Refresh Health
      </button>
    </div>
  );
};

export default HealthStatus;