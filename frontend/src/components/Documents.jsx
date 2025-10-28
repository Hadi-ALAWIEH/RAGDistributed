import { useState, useEffect } from 'react';
import { ragAPI } from '../services/api';

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [type, setType] = useState('clean');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = type === 'clean' 
        ? await ragAPI.getCleanDocuments(10)
        : await ragAPI.getRawDocuments(10);
      setDocuments(response.data.items);
    } catch (err) {
      setError('Failed to fetch documents');
      console.error('Documents error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [type]);

  return (
    <div className="card">
      <h2>Documents</h2>
      
      <div className="form-group">
        <label>Document Type</label>
        <div>
          <label style={{ marginRight: '15px' }}>
            <input
              type="radio"
              value="clean"
              checked={type === 'clean'}
              onChange={(e) => setType(e.target.value)}
              style={{ marginRight: '5px' }}
            />
            Clean Text
          </label>
          <label>
            <input
              type="radio"
              value="raw"
              checked={type === 'raw'}
              onChange={(e) => setType(e.target.value)}
              style={{ marginRight: '5px' }}
            />
            Raw HTML
          </label>
        </div>
      </div>

      <button onClick={fetchDocuments} className="btn" disabled={loading}>
        {loading ? 'Refreshing...' : 'Refresh Documents'}
      </button>

      {error && <div className="error">{error}</div>}

      <div className="results" style={{ marginTop: '20px' }}>
        {documents.map((doc, index) => (
          <div key={index} className="result-item">
            {doc.url && (
              <div className="url">
                <strong>URL:</strong> {doc.url}
              </div>
            )}
            {doc.text && (
              <div className="text">{doc.text.substring(0, 200)}...</div>
            )}
            {doc.html && (
              <div className="text">
                <strong>HTML:</strong> {doc.html.substring(0, 150)}...
              </div>
            )}
          </div>
        ))}
        
        {documents.length === 0 && !loading && (
          <div className="loading">No documents found</div>
        )}
      </div>
    </div>
  );
};

export default Documents;