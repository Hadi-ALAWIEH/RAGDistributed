import { useState } from 'react';
import { ragAPI } from '../services/api';

const Search = () => {
  const [query, setQuery] = useState('');
  const [k, setK] = useState(5);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await ragAPI.search(query, k);
      setResults(response.data.results);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Semantic Search</h2>
      <form onSubmit={handleSearch}>
        <div className="form-group">
          <label htmlFor="search-query">Search Query</label>
          <input
            id="search-query"
            type="text"
            className="form-control"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="search-k">Number of Results</label>
          <input
            id="search-k"
            type="number"
            className="form-control"
            value={k}
            onChange={(e) => setK(parseInt(e.target.value))}
            min="1"
            max="20"
          />
        </div>
        
        <button type="submit" className="btn" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      <div className="results">
        {results.map((result, index) => (
          <div key={index} className="result-item">
            {result.url && (
              <div className="url">
                <strong>URL:</strong> {result.url}
              </div>
            )}
            {result.score && (
              <div className="score">Similarity Score: {result.score.toFixed(4)}</div>
            )}
            <div className="text">{result.text}</div>
          </div>
        ))}
        
        {results.length === 0 && !loading && query && (
          <div className="loading">No results found</div>
        )}
      </div>
    </div>
  );
};

export default Search;