import React from 'react';
import HealthStatus from './components/HealthStatus';
import Search from './components/Search';
import RAGQuery from './components/RAGQuery';
import Documents from './components/Documents';
import './App.css';

function App() {
  return (
    <div className="container">
      <div className="header">
        <h1>RAG Scraper Dashboard</h1>
        <p>Search and query your scraped documents with semantic search and RAG</p>
      </div>

      <HealthStatus />

      <div className="grid">
        <Search />
        <RAGQuery />
      </div>

      <Documents />
    </div>
  );
}

export default App;