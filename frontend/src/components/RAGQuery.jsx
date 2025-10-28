import { useState } from 'react';
import { ragAPI } from '../services/api';

const RAGQuery = () => {
  const [query, setQuery] = useState('');
  const [k, setK] = useState(3);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRAGQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    
    try {
      const result = await ragAPI.ragQuery(query, k);
      setResponse(result.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'RAG query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>RAG Query</h2>
      <form onSubmit={handleRAGQuery}>
        <div className="form-group">
          <label htmlFor="rag-query">Your Question</label>
          <textarea
            id="rag-query"
            className="form-control"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question based on the scraped content..."
            rows="3"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="rag-k">Context Chunks</label>
          <input
            id="rag-k"
            type="number"
            className="form-control"
            value={k}
            onChange={(e) => setK(parseInt(e.target.value))}
            min="1"
            max="10"
          />
        </div>
        
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Processing...' : 'Ask Question'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {response && (
        <div className="results">
          <div className="rag-answer">
            <strong>Answer:</strong>
            <div style={{ marginTop: '10px' }}>{response.answer}</div>
          </div>
          <div className="stats">
            Processed in {response.processing_time.toFixed(2)}s using {response.ctx_count} context chunks
          </div>
        </div>
      )}
    </div>
  );
};

export default RAGQuery;