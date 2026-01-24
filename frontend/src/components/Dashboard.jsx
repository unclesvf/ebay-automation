import React, { useEffect, useState, useRef, useCallback } from 'react';
import { api } from '../api';
import { Activity, Play, Terminal, Database, Youtube, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = () => {
  const [status, setStatus] = useState({ orchestrator_running: false, model: 'Loading...', ollama_status: 'Unknown' });
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const logsEndRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.getStatus();
      setStatus(res.data || { orchestrator_running: false, model: 'Unknown' });
      setIsRunning(res.data?.orchestrator_running || false);
      setConnectionError(null);
    } catch (e) {
      console.error("Status fetch failed", e);
      setConnectionError("Cannot connect to server");
      setStatus({ orchestrator_running: false, model: 'Offline', ollama_status: 'Unknown' });
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await api.getLogs();
      if (res.data?.logs && Array.isArray(res.data.logs)) {
        setLogs(res.data.logs);
      }
    } catch (e) {
      // Don't show error for logs - less critical
      console.error("Logs fetch failed", e);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchLogs();
    // Reduced polling from 2s to 5s to reduce network traffic
    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchLogs]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleRun = async () => {
    if (isRunning) return;
    try {
      await api.runOrchestrator();
      fetchStatus();
    } catch (e) {
      alert("Failed to start orchestrator: " + e.message);
    }
  };

  return (
    <div className="dashboard-container">
      <header className="page-header">
        <div>
          <h2 className="page-title">Mission Control</h2>
          <p className="page-subtitle">Overview & Orchestration</p>
        </div>
        <button 
          className={`action-btn ${isRunning ? 'disabled' : ''}`}
          onClick={handleRun}
          disabled={isRunning}
        >
          {isRunning ? <Activity className="spin" /> : <Play />}
          {isRunning ? 'ORCHESTRATING...' : 'INITIATE SEQUENCE'}
        </button>
      </header>
      
      <div className="stats-grid">
        <StatCard 
          icon={Youtube} 
          label="YouTube Analysis" 
          value="Enabled" 
          sub="qwen2.5:32b" 
          color="var(--primary-cyan)" 
        />
        <StatCard 
          icon={Database} 
          label="Knowledge Base" 
          value="Online" 
          sub="ChromaDB" 
          color="var(--secondary-purple)" 
        />
        <StatCard 
          icon={FileText} 
          label="Latest Action" 
          value={isRunning ? "Running..." : "Idle"} 
          sub="Check logs" 
          color={isRunning ? "var(--accent-green)" : "var(--text-muted)"} 
        />
      </div>

      <div className="stats-grid">
        <StatCard 
          icon={Youtube} 
          label="YouTube Analysis" 
          value="Enabled" 
          sub="qwen2.5:32b" 
          color="var(--primary-cyan)" 
        />
        <StatCard 
          icon={Database} 
          label="Knowledge Base" 
          value="Online" 
          sub="ChromaDB" 
          color="var(--secondary-purple)" 
        />
        <StatCard 
          icon={FileText} 
          label="Latest Action" 
          value={isRunning ? "Running..." : "Idle"} 
          sub="Check logs" 
          color={isRunning ? "var(--accent-green)" : "var(--text-muted)"} 
        />
      </div>

      <style>{`
        .dashboard-container {
          display: flex;
          flex-direction: column;
          gap: 2rem;
          height: 100%;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .page-title {
          font-size: 2rem;
          font-weight: 700;
          color: var(--text-main);
        }

        .page-subtitle {
          color: var(--text-muted);
        }

        .action-btn {
          background: rgba(255, 138, 138, 0.1);
          border: 1px solid var(--primary-cyan);
          color: var(--primary-cyan);
          padding: 1rem 2rem;
          border-radius: 8px;
          font-weight: 600;
          letter-spacing: 1px;
          display: flex;
          align-items: center;
          gap: 0.8rem;
          transition: all 0.3s ease;
          box-shadow: 0 0 15px rgba(255, 138, 138, 0.15);
        }

        .action-btn:hover:not(.disabled) {
          background: var(--primary-cyan);
          color: #000;
          box-shadow: 0 0 30px rgba(255, 138, 138, 0.4);
          transform: translateY(-2px);
        }

        .action-btn.disabled {
          opacity: 0.6;
          cursor: not-allowed;
          filter: grayscale(0.5);
        }

        .spin {
          animation: spin 2s linear infinite;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
        }

        .stat-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--border-glass);
          padding: 1.5rem;
          border-radius: 16px;
          display: flex;
          align-items: center;
          gap: 1.5rem;
          transition: transform 0.3s ease;
        }

        .stat-card:hover {
          background: rgba(255, 255, 255, 0.05);
          transform: translateY(-5px);
        }

        .stat-icon {
          padding: 1rem;
          background: rgba(255,255,255,0.05);
          border-radius: 12px;
        }

        .stat-content h3 {
          font-size: 0.9rem;
          color: var(--text-muted);
          font-weight: 500;
        }

        .stat-content .value {
          font-size: 1.5rem;
          font-weight: 700;
          margin: 0.3rem 0;
        }

        .stat-content .sub {
          font-size: 0.8rem;
          color: rgba(255,255,255,0.4);
        }

        .terminal-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          background: #050508;
          border-radius: 12px;
          border: 1px solid var(--border-glass);
          overflow: hidden;
          min-height: 300px;
        }

        .terminal-header {
          padding: 0.8rem 1.5rem;
          background: rgba(255,255,255,0.02);
          border-bottom: 1px solid var(--border-glass);
          display: flex;
          align-items: center;
          gap: 0.8rem;
          font-size: 0.9rem;
          color: var(--text-muted);
        }

        .terminal-window {
          flex: 1;
          padding: 1.5rem;
          overflow-y: auto;
          font-family: 'Fira Code', monospace;
          font-size: 0.9rem;
          color: #a0a0a0;
        }

        .log-line {
          margin-bottom: 0.2rem;
          word-break: break-all;
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, sub, color }) => (
  <div className="stat-card">
    <div className="stat-icon" style={{ color: color, boxShadow: `0 0 15px ${color}20` }}>
      <Icon size={24} />
    </div>
    <div className="stat-content">
      <h3>{label}</h3>
      <div className="value" style={{ textShadow: `0 0 10px ${color}40` }}>{value}</div>
      <div className="sub">{sub}</div>
    </div>
  </div>
);

export default Dashboard;
