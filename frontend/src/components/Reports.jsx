import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { FileText, ExternalLink, RefreshCw, X, Maximize2, Minimize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await api.getReports();
      if (res.data && res.data.reports) {
        setReports(res.data.reports);
      }
    } catch (e) {
      console.error("Failed to fetch reports", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const openReport = (report) => {
    setSelectedReport(report);
  };

  const closeViewer = () => {
    setSelectedReport(null);
    setIsFullscreen(false);
  };

  const openInNewTab = (report) => {
    window.open(report.url, '_blank');
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="reports-container">
      <style>{`
        .reports-container {
          padding: 0;
          color: var(--text-primary);
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .reports-header {
          margin-bottom: 2rem;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
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

        .header-actions {
          display: flex;
          gap: 0.75rem;
        }

        .action-btn {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          color: var(--text-muted);
          padding: 0.5rem 1rem;
          border-radius: 8px;
          cursor: pointer;
          font-size: 0.85rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--primary-coral);
          color: white;
          border-color: var(--primary-coral);
        }

        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .reports-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
        }

        .report-card {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          padding: 1.25rem;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .report-card:hover {
          transform: translateY(-2px);
          border-color: var(--primary-coral);
          box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }

        .report-icon {
          font-size: 2rem;
          margin-bottom: 0.75rem;
        }

        .report-name {
          font-size: 1.1rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          color: var(--text-primary);
        }

        .report-description {
          color: var(--text-muted);
          font-size: 0.85rem;
          margin-bottom: 0.75rem;
          line-height: 1.4;
        }

        .report-meta {
          display: flex;
          justify-content: space-between;
          font-size: 0.75rem;
          color: var(--text-muted);
          padding-top: 0.75rem;
          border-top: 1px solid rgba(255,255,255,0.05);
        }

        .report-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.75rem;
        }

        .report-action-btn {
          background: rgba(255,255,255,0.05);
          border: none;
          color: var(--text-muted);
          padding: 0.4rem 0.8rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.3rem;
          transition: all 0.2s;
        }

        .report-action-btn:hover {
          background: var(--primary-coral);
          color: white;
        }

        /* Viewer Modal */
        .viewer-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.8);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }

        .viewer-overlay.fullscreen {
          padding: 0;
        }

        .viewer-container {
          background: var(--bg-primary);
          border-radius: 12px;
          width: 100%;
          max-width: 1200px;
          height: 85vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          border: 1px solid rgba(255,255,255,0.1);
        }

        .viewer-overlay.fullscreen .viewer-container {
          max-width: 100%;
          height: 100vh;
          border-radius: 0;
        }

        .viewer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 1.5rem;
          background: rgba(255,255,255,0.03);
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }

        .viewer-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .viewer-title h3 {
          margin: 0;
          font-size: 1.1rem;
        }

        .viewer-controls {
          display: flex;
          gap: 0.5rem;
        }

        .viewer-control-btn {
          background: rgba(255,255,255,0.05);
          border: none;
          color: var(--text-muted);
          padding: 0.5rem;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .viewer-control-btn:hover {
          background: var(--primary-coral);
          color: white;
        }

        .viewer-iframe {
          flex: 1;
          border: none;
          background: white;
        }

        .loading-state {
          text-align: center;
          padding: 3rem;
          color: var(--text-muted);
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <header className="reports-header">
        <div>
          <h2 className="page-title">Knowledge Base Reports</h2>
          <p className="page-subtitle">Browse and view generated HTML reports</p>
        </div>
        <div className="header-actions">
          <button className="action-btn" onClick={fetchReports} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </header>

      {loading ? (
        <div className="loading-state">Loading reports...</div>
      ) : (
        <div className="reports-grid">
          <AnimatePresence>
            {reports.map((report, index) => (
              <motion.div
                key={report.filename}
                className="report-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                onClick={() => openReport(report)}
              >
                <div className="report-icon">{report.icon}</div>
                <div className="report-name">{report.name}</div>
                <div className="report-description">{report.description}</div>
                <div className="report-meta">
                  <span>{formatSize(report.size)}</span>
                  <span>{formatDate(report.modified)}</span>
                </div>
                <div className="report-actions">
                  <button
                    className="report-action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      openReport(report);
                    }}
                  >
                    <FileText size={12} /> View
                  </button>
                  <button
                    className="report-action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      openInNewTab(report);
                    }}
                  >
                    <ExternalLink size={12} /> New Tab
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Report Viewer Modal */}
      <AnimatePresence>
        {selectedReport && (
          <motion.div
            className={`viewer-overlay ${isFullscreen ? 'fullscreen' : ''}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeViewer}
          >
            <motion.div
              className="viewer-container"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="viewer-header">
                <div className="viewer-title">
                  <span style={{ fontSize: '1.5rem' }}>{selectedReport.icon}</span>
                  <h3>{selectedReport.name}</h3>
                </div>
                <div className="viewer-controls">
                  <button
                    className="viewer-control-btn"
                    onClick={() => openInNewTab(selectedReport)}
                    title="Open in new tab"
                  >
                    <ExternalLink size={18} />
                  </button>
                  <button
                    className="viewer-control-btn"
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                  >
                    {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                  </button>
                  <button
                    className="viewer-control-btn"
                    onClick={closeViewer}
                    title="Close"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>
              <iframe
                className="viewer-iframe"
                src={selectedReport.url}
                title={selectedReport.name}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Reports;
