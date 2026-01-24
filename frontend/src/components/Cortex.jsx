import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Search, Database, ExternalLink, Hash } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Cortex = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [threshold, setThreshold] = useState(1.3);  // Distance threshold (lower = stricter)

  const performSearch = async (q) => {
    setLoading(true);
    try {
      const res = await api.searchKnowledge(q, threshold);
      if (res.data.items) {
        setResults(res.data.items);
      } else {
        setResults([]);
      }
    } catch (e) {
      console.error("Search failed", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load: peek
    performSearch('');
  }, []);

  // Re-search when threshold changes (with debounce)
  useEffect(() => {
    if (!query) return;  // Only re-search if there's an active query
    const timer = setTimeout(() => {
      performSearch(query);
    }, 300);  // 300ms debounce
    return () => clearTimeout(timer);
  }, [threshold]);

  const handleSearch = (e) => {
    e.preventDefault();
    performSearch(query);
  };

  // Helper to ensure URLs have proper protocol
  const formatUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return 'https://' + url;
  };

  // Extract a clean title from content
  const getTitle = (item) => {
    const content = item.content || '';
    // Try to get first line as title
    const firstLine = content.split('\n')[0];
    if (firstLine && firstLine.length < 100) {
      return firstLine;
    }
    return item.metadata?.category || 'Knowledge Item';
  };

  // Parse text and make URLs clickable
  const linkifyContent = (text) => {
    if (!text) return null;
    
    // Regex to match URLs - with or without protocol, including in angle brackets
    // Matches: https://..., http://..., youtu.be/..., github.com/..., etc.
    const urlRegex = /<?(?:https?:\/\/)?(?:(?:youtu\.be|youtube\.com|github\.com|huggingface\.co|x\.com|twitter\.com)[^\s<>]+)>?/gi;
    
    const parts = [];
    let lastIndex = 0;
    let match;
    
    while ((match = urlRegex.exec(text)) !== null) {
      // Add text before the URL
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      
      // Clean up the URL (remove angle brackets)
      let url = match[0].replace(/^<|>$/g, '');
      url = formatUrl(url);
      
      parts.push(
        <a key={match.index} href={url} target="_blank" rel="noopener noreferrer" className="inline-link">
          {url.length > 45 ? url.slice(0, 45) + '...' : url}
        </a>
      );
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    
    return parts.length > 0 ? parts : text;
  };

  return (
    <div className="cortex-container">
      <header className="page-header">
        <div>
          <h2 className="page-title">Cortex</h2>
          <p className="page-subtitle">Neural Knowledge Graph</p>
        </div>
      </header>
      
      <div className="search-section">
        <form onSubmit={handleSearch} className="search-bar">
          <Search className="search-icon" />
          <input 
            type="text" 
            placeholder="Query the knowledge base..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Scanning...' : 'Search'}
          </button>
        </form>
        
        <div className="threshold-slider">
          <label>
            Sensitivity: <span className="threshold-value">{threshold.toFixed(1)}</span>
            <span className="threshold-hint">(Lower = stricter match)</span>
          </label>
          <input 
            type="range" 
            min="0.5" 
            max="2.5" 
            step="0.1" 
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
          />
        </div>
      </div>

      <div className="results-grid">
        <AnimatePresence>
          {results.map((item, index) => (
            <motion.div 
              key={item.id || index}
              className="wisdom-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
            >
              <div className="card-header">
                <span className="card-tag">
                  <Hash size={12} />
                  {item.metadata?.category || 'General'}
                </span>
                {item.metadata?.source && (
                  <span className="source-tag" title={item.metadata.source}>
                    {item.metadata.source.length > 20 ? '...' + item.metadata.source.slice(-20) : item.metadata.source}
                  </span>
                )}
              </div>
              
              <div className="card-content">
                <div className="card-title">{getTitle(item)}</div>
                {item.content.split('\n').slice(1, 4).map((line, i) => (
                  <div key={i} className="card-line">{linkifyContent(line)}</div>
                ))}
              </div>

              <div className="card-footer">
                 <div className="meta-info">
                    {item.metadata?.timestamp && <span>{new Date(item.metadata.timestamp).toLocaleDateString()}</span>}
                 </div>
                 {item.metadata?.url && (
                   <a href={formatUrl(item.metadata.url)} target="_blank" rel="noopener noreferrer" className="link-btn">
                     <ExternalLink size={14} />
                   </a>
                 )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {!loading && results.length === 0 && (
          <div className="empty-state">
            <Database size={48} />
            <p>No knowledge patterns found.</p>
          </div>
        )}
      </div>

      <style>{`
        .cortex-container {
           display: flex;
           flex-direction: column;
           gap: 2rem;
           height: 100%;
        }
        
        .search-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
        }

        .search-bar {
          display: flex;
          align-items: center;
          background: rgba(255,255,255,0.05);
          border: 1px solid var(--border-glass);
          border-radius: 50px;
          padding: 0.5rem 1rem;
          width: 100%;
          max-width: 600px;
          transition: all 0.3s ease;
        }

        .search-bar:focus-within {
          background: rgba(255,255,255,0.08);
          border-color: var(--primary-cyan);
          box-shadow: 0 0 20px rgba(255, 138, 138, 0.15);
        }

        .search-icon {
          color: var(--text-muted);
          margin-right: 0.8rem;
        }

        .search-bar input {
          flex: 1;
          background: transparent;
          border: none;
          color: var(--text-main);
          font-size: 1rem;
          outline: none;
        }
        
        .search-bar button {
          background: var(--primary-cyan);
          color: #000;
          padding: 0.5rem 1.2rem;
          border-radius: 20px;
          font-weight: 600;
          font-size: 0.9rem;
        }

        .threshold-slider {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          margin-top: 1rem;
        }

        .threshold-slider label {
          color: var(--text-muted);
          font-size: 0.85rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .threshold-value {
          color: var(--primary-cyan);
          font-weight: 600;
        }

        .threshold-hint {
          color: var(--text-muted);
          font-size: 0.75rem;
        }

        .threshold-slider input[type="range"] {
          width: 200px;
          accent-color: var(--primary-cyan);
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 1.5rem;
          padding-bottom: 2rem;
        }

        .wisdom-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid var(--border-glass);
          border-radius: 12px;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
          transition: all 0.3s ease;
        }

        .wisdom-card:hover {
          transform: translateY(-5px);
          background: rgba(255,255,255,0.06);
          border-color: rgba(255,255,255,0.2);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .card-tag {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          background: rgba(188, 19, 254, 0.1);
          color: var(--secondary-purple);
          padding: 0.3rem 0.6rem;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 600;
        }
        
        .source-tag {
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .inline-link {
          color: var(--primary-cyan);
          text-decoration: underline;
        }

        .inline-link:hover {
          color: #ffb0b0;
        }

        .card-content {
          font-size: 0.9rem;
          line-height: 1.5;
          color: rgba(255,255,255,0.9);
          display: -webkit-box;
          -webkit-line-clamp: 6;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .card-footer {
          margin-top: auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 1rem;
          border-top: 1px solid rgba(255,255,255,0.05);
        }

        .meta-info {
           font-size: 0.8rem;
           color: var(--text-muted);
        }

        .link-btn {
          color: var(--text-muted);
          transition: color 0.2s;
        }
        
        .link-btn:hover {
          color: var(--primary-cyan);
        }

        .empty-state {
           grid-column: 1 / -1;
           display: flex;
           flex-direction: column;
           align-items: center;
           justify-content: center;
           padding: 4rem;
           color: var(--text-muted);
           opacity: 0.5;
        }
      `}</style>
    </div>
  );
};

export default Cortex;
