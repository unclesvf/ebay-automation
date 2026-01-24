import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import { TrendingUp, Users, Calendar, ExternalLink, Copy, Star, Github, Youtube, Bookmark } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const UniversalInsights = () => {
  const [insights, setInsights] = useState({ items: [], timeline: {}, top_authors: [], total_count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('impact');
  const [limit, setLimit] = useState(50);
  const [filterAuthor, setFilterAuthor] = useState(null);
  const requestIdRef = useRef(0);  // Track request ordering

  useEffect(() => {
    let isMounted = true;
    const currentRequestId = ++requestIdRef.current;

    const fetchInsights = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getInsights(limit, sortBy);
        // Only update if this is the most recent request and component is mounted
        if (isMounted && currentRequestId === requestIdRef.current) {
          if (res.data && Array.isArray(res.data.items)) {
            setInsights(res.data);
          } else if (res.data?.error) {
            setError(res.data.error);
          } else {
            setInsights({ items: [], timeline: {}, top_authors: [], total_count: 0 });
          }
        }
      } catch (e) {
        if (isMounted && currentRequestId === requestIdRef.current) {
          console.error("Failed to fetch insights", e);
          setError(e.message || "Failed to load insights");
        }
      } finally {
        if (isMounted && currentRequestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    };

    fetchInsights();

    return () => {
      isMounted = false;
    };
  }, [sortBy, limit]);

  const getTypeIcon = (type) => {
    switch(type) {
      case 'GitHub': return <Github size={14} />;
      case 'Tutorial': return <Youtube size={14} />;
      case 'HuggingFace': return '🤗';
      case 'Style': return '🎨';
      default: return '📦';
    }
  };

  const getTypeColor = (type) => {
    switch(type) {
      case 'GitHub': return '#238636';
      case 'Tutorial': return '#ff0000';
      case 'HuggingFace': return '#ff9d00';
      case 'Style': return '#5865f2';
      default: return '#666';
    }
  };

  const formatUrl = (url) => {
    if (!url) return '#';
    if (url.startsWith('http')) return url;
    return `https://${url}`;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const formatMetric = (value) => {
    if (!value) return null;
    if (value >= 1000000) return `${(value/1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value/1000).toFixed(1)}K`;
    return value;
  };

  return (
    <div className="insights-container">
      <style>{`
        .insights-container {
          padding: 0;
          color: var(--text-primary);
        }

        .insights-header {
          margin-bottom: 2rem;
        }

        .page-title {
          font-size: 1.8rem;
          font-weight: 700;
          margin-bottom: 0.25rem;
          background: linear-gradient(90deg, var(--primary-coral), var(--primary-yellow));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .page-subtitle {
          color: var(--text-muted);
          font-size: 0.95rem;
        }

        .controls-bar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          align-items: center;
          flex-wrap: wrap;
        }

        .control-group {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .control-group label {
          color: var(--text-muted);
          font-size: 0.85rem;
        }

        .control-group select {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: var(--text-primary);
          padding: 0.4rem 0.8rem;
          border-radius: 6px;
          cursor: pointer;
          -webkit-appearance: menulist;
          appearance: menulist;
        }

        .control-group select option {
          background: #1a1a2e;
          color: #ffffff;
          padding: 0.5rem;
        }

        .stats-row {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
        }

        .stat-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          padding: 1rem 1.5rem;
          min-width: 120px;
        }

        .stat-value {
          font-size: 1.8rem;
          font-weight: 700;
          color: var(--primary-coral);
        }

        .stat-label {
          color: var(--text-muted);
          font-size: 0.8rem;
        }

        .main-grid {
          display: grid;
          grid-template-columns: 1fr 300px;
          gap: 1.5rem;
        }

        @media (max-width: 900px) {
          .main-grid {
            grid-template-columns: 1fr;
          }
        }

        .trending-section h3, .sidebar h3 {
          font-size: 1rem;
          margin-bottom: 1rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--text-primary);
        }

        .items-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
        }

        .insight-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          padding: 1rem;
          transition: all 0.2s ease;
        }

        .insight-card:hover {
          transform: translateY(-2px);
          border-color: var(--primary-coral);
          box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 0.5rem;
        }

        .type-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.2rem 0.6rem;
          border-radius: 12px;
          font-size: 0.7rem;
          font-weight: 600;
          color: white;
        }

        .impact-badge {
          background: linear-gradient(135deg, var(--primary-coral), #ff6b6b);
          padding: 0.2rem 0.5rem;
          border-radius: 6px;
          font-size: 0.7rem;
          font-weight: 700;
          color: white;
        }

        .confidence-indicator {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          font-size: 0.7rem;
          color: var(--text-muted);
          margin-top: 0.25rem;
        }

        .confidence-bar {
          width: 50px;
          height: 4px;
          background: rgba(255,255,255,0.1);
          border-radius: 2px;
          overflow: hidden;
        }

        .confidence-fill {
          height: 100%;
          border-radius: 2px;
          transition: width 0.3s ease;
        }

        .confidence-high { background: #4ade80; }
        .confidence-medium { background: #fbbf24; }
        .confidence-low { background: #f87171; }

        .relevance-tags {
          display: flex;
          gap: 0.3rem;
          flex-wrap: wrap;
          margin-top: 0.5rem;
        }

        .relevance-tag {
          background: rgba(77, 168, 218, 0.2);
          color: var(--link);
          padding: 0.15rem 0.4rem;
          border-radius: 4px;
          font-size: 0.65rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .card-title {
          font-size: 0.95rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          line-height: 1.3;
        }

        .card-title a {
          color: var(--text-primary);
          text-decoration: none;
        }

        .card-title a:hover {
          color: var(--primary-coral);
        }

        .card-meta {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
          margin-bottom: 0.5rem;
        }

        .meta-item {
          color: var(--text-muted);
          font-size: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .metrics-row {
          display: flex;
          gap: 0.75rem;
          margin-top: 0.5rem;
        }

        .metric {
          color: var(--text-muted);
          font-size: 0.75rem;
        }

        .card-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.75rem;
          padding-top: 0.75rem;
          border-top: 1px solid rgba(255,255,255,0.05);
        }

        .action-btn {
          background: rgba(255,255,255,0.05);
          border: none;
          color: var(--text-muted);
          padding: 0.3rem 0.6rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.7rem;
          display: flex;
          align-items: center;
          gap: 0.3rem;
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--primary-coral);
          color: white;
        }

        .sidebar {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .sidebar-section {
          background: rgba(255,255,255,0.02);
          border: 1px solid rgba(255,255,255,0.05);
          border-radius: 12px;
          padding: 1rem;
        }

        .author-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem;
          border-bottom: 1px solid rgba(255,255,255,0.05);
          cursor: pointer;
          border-radius: 6px;
          margin: 0.25rem 0;
          transition: all 0.2s ease;
        }

        .author-item:hover {
          background: rgba(255,255,255,0.05);
        }

        .author-item.active {
          background: rgba(var(--primary-coral-rgb, 255, 107, 107), 0.2);
          border-color: var(--primary-coral);
        }

        .author-item:last-child {
          border-bottom: none;
        }

        .author-name {
          font-size: 0.85rem;
          color: var(--text-primary);
        }

        .clear-filter-btn {
          background: rgba(255,255,255,0.1);
          border: none;
          color: var(--text-muted);
          padding: 0.3rem 0.6rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.75rem;
          margin-bottom: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.3rem;
          transition: all 0.2s;
        }

        .clear-filter-btn:hover {
          background: var(--primary-coral);
          color: white;
        }

        .filter-active-text {
          color: var(--primary-coral);
          font-size: 0.8rem;
          margin-bottom: 0.5rem;
        }

        .author-stats {
          display: flex;
          gap: 0.5rem;
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .timeline-item {
          padding: 0.5rem 0;
          border-left: 2px solid var(--primary-coral);
          padding-left: 0.75rem;
          margin-bottom: 0.5rem;
        }

        .timeline-date {
          font-size: 0.75rem;
          color: var(--primary-coral);
          font-weight: 600;
        }

        .timeline-count {
          font-size: 0.8rem;
          color: var(--text-muted);
        }

        .loading-state {
          text-align: center;
          padding: 3rem;
          color: var(--text-muted);
        }

        .empty-state {
          text-align: center;
          padding: 3rem;
          color: var(--text-muted);
        }
      `}</style>

      <header className="insights-header">
        <h2 className="page-title">Universal Insights</h2>
        <p className="page-subtitle">Unified view of all intelligence, ranked by impact</p>
      </header>

      <div className="controls-bar">
        <div className="control-group">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="impact">Impact Score</option>
            <option value="date">Date</option>
          </select>
        </div>
        <div className="control-group">
          <label>Show:</label>
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            <option value={25}>25 items</option>
            <option value={50}>50 items</option>
            <option value={100}>100 items</option>
          </select>
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{insights.total_count}</div>
          <div className="stat-label">Total Items</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{insights.top_authors?.length || 0}</div>
          <div className="stat-label">Contributors</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{Object.keys(insights.timeline || {}).length}</div>
          <div className="stat-label">Active Days</div>
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Loading insights...</div>
      ) : (
        <div className="main-grid">
          <div className="trending-section">
            <h3><TrendingUp size={18} /> Trending Now {filterAuthor && `(${filterAuthor})`}</h3>
            <div className="items-grid">
              <AnimatePresence>
                {insights.items
                  ?.filter(item => !filterAuthor || item.author === filterAuthor)
                  .map((item, index) => (
                  <motion.div
                    key={item.id || index}
                    className="insight-card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.03 }}
                  >
                    <div className="card-header">
                      <span 
                        className="type-badge" 
                        style={{ backgroundColor: getTypeColor(item.type) }}
                      >
                        {getTypeIcon(item.type)} {item.type}
                      </span>
                      {item.impact > 0 && (
                        <span className="impact-badge">⚡ {item.impact}</span>
                      )}
                    </div>
                    
                    <div className="card-title">
                      <a href={formatUrl(item.url)} target="_blank" rel="noopener noreferrer">
                        {item.title}
                      </a>
                    </div>
                    
                    <div className="card-meta">
                      {item.author && item.author !== 'Unknown' && (
                        <span className="meta-item">👤 {item.author}</span>
                      )}
                      {item.owner && (
                        <span className="meta-item">📁 {item.owner}</span>
                      )}
                      {item.date && (
                        <span className="meta-item">📅 {item.date}</span>
                      )}
                    </div>

                    {item.metrics && Object.keys(item.metrics).some(k => item.metrics[k] > 0) && (
                      <div className="metrics-row">
                        {item.metrics.views > 0 && <span className="metric">👁️ {formatMetric(item.metrics.views)}</span>}
                        {item.metrics.likes > 0 && <span className="metric">❤️ {formatMetric(item.metrics.likes)}</span>}
                        {item.metrics.reposts > 0 && <span className="metric">🔁 {formatMetric(item.metrics.reposts)}</span>}
                      </div>
                    )}

                    {/* Relevance Tags */}
                    {item.relevance_tags && item.relevance_tags.length > 0 && (
                      <div className="relevance-tags">
                        {item.relevance_tags.map((tag, i) => (
                          <span key={i} className="relevance-tag">{tag}</span>
                        ))}
                      </div>
                    )}

                    {/* Confidence Indicator */}
                    {item.confidence > 0 && (
                      <div className="confidence-indicator">
                        <span>Confidence:</span>
                        <div className="confidence-bar">
                          <div
                            className={`confidence-fill ${
                              item.confidence >= 0.7 ? 'confidence-high' :
                              item.confidence >= 0.4 ? 'confidence-medium' : 'confidence-low'
                            }`}
                            style={{ width: `${item.confidence * 100}%` }}
                          />
                        </div>
                        <span>{Math.round(item.confidence * 100)}%</span>
                      </div>
                    )}

                    <div className="card-actions">
                      <button 
                        className="action-btn"
                        onClick={() => window.open(formatUrl(item.url), '_blank')}
                      >
                        <ExternalLink size={12} /> Open
                      </button>
                      <button 
                        className="action-btn"
                        onClick={() => copyToClipboard(formatUrl(item.url))}
                      >
                        <Copy size={12} /> Copy
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          <div className="sidebar">
            <div className="sidebar-section">
              <h3><Users size={16} /> Top Contributors</h3>
              {filterAuthor && (
                <>
                  <div className="filter-active-text">Filtering by: {filterAuthor}</div>
                  <button
                    className="clear-filter-btn"
                    onClick={() => setFilterAuthor(null)}
                  >
                    ✕ Clear Filter
                  </button>
                </>
              )}
              {insights.top_authors?.map((author, i) => (
                <div
                  key={i}
                  className={`author-item ${filterAuthor === author.author ? 'active' : ''}`}
                  onClick={() => setFilterAuthor(filterAuthor === author.author ? null : author.author)}
                  title={`Click to filter by ${author.author}`}
                >
                  <span className="author-name">{author.author}</span>
                  <span className="author-stats">
                    <span>📊 {author.count}</span>
                    <span>⚡ {author.impact}</span>
                  </span>
                </div>
              ))}
            </div>

            <div className="sidebar-section">
              <h3><Calendar size={16} /> Activity Timeline</h3>
              {Object.entries(insights.timeline || {}).slice(0, 7).map(([date, data]) => (
                <div key={date} className="timeline-item">
                  <div className="timeline-date">{date}</div>
                  <div className="timeline-count">{data.count} items added</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UniversalInsights;
