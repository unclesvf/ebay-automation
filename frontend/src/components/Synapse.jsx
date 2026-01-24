import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { ToggleLeft, ToggleRight, Save, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

const Synapse = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.getConfig();
      setConfig(res.data);
      if (res.data.global) {
        setDryRun(res.data.global.dry_run);
      }
      setLoading(false);
    } catch (e) {
      console.error("Config load failed", e);
      setLoading(false);
    }
  };

  const handleToggleDryRun = async () => {
    setSaving(true);
    try {
      const newValue = !dryRun;
      await api.setDryRun(newValue);
      setDryRun(newValue);
      // Update local config object too (with null safety)
      setConfig(prev => ({
        ...prev,
        global: { ...(prev?.global || {}), dry_run: newValue }
      }));
    } catch (e) {
      console.error("Failed to update settings", e);
      alert("Failed to update settings: " + (e.response?.data?.detail || e.message));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading">Initializing Synapse...</div>;

  return (
    <div className="synapse-container">
       <header className="page-header">
        <div>
          <h2 className="page-title">Synapse</h2>
          <p className="page-subtitle">System Configuration & Logic</p>
        </div>
      </header>

      <div className="settings-panel">
        <div className="setting-item">
          <div className="setting-info">
             <h3>Dry Run Mode</h3>
             <p>When enabled, actions are simulated but not executed. No emails are moved.</p>
          </div>
          <button 
            className={`toggle-btn ${dryRun ? 'active' : ''}`}
            onClick={handleToggleDryRun}
            disabled={saving}
          >
            {dryRun ? <ToggleRight size={32} color="var(--accent-green)" /> : <ToggleLeft size={32} color="var(--text-muted)" />}
            <span className="toggle-label">{dryRun ? 'ENABLED' : 'DISABLED'}</span>
          </button>
        </div>

        {!dryRun && (
          <div className="alert-box">
             <ShieldAlert size={20} />
             <span><strong>CAUTION:</strong> Live mode is active. Actions will be permanent.</span>
          </div>
        )}
      </div>

      <div className="config-viewer">
        <h3>Raw Configuration (Read-Only)</h3>
        <pre>{JSON.stringify(config, null, 2)}</pre>
      </div>

      <style>{`
        .synapse-container {
           display: flex;
           flex-direction: column;
           gap: 2rem;
        }

        .settings-panel {
          background: rgba(255,255,255,0.03);
          border: 1px solid var(--border-glass);
          border-radius: 12px;
          padding: 2rem;
        }

        .setting-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
        }

        .setting-info h3 {
          font-size: 1.2rem;
          margin-bottom: 0.5rem;
        }
        
        .setting-info p {
          color: var(--text-muted);
          max-width: 500px;
        }

        .toggle-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }

        .toggle-label {
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 1px;
          color: var(--text-muted);
        }
        
        .toggle-btn.active .toggle-label {
           color: var(--accent-green);
        }

        .alert-box {
          background: rgba(255, 42, 42, 0.1);
          border: 1px solid rgba(255, 42, 42, 0.3);
          color: #ff8888;
          padding: 1rem;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .config-viewer {
          flex: 1;
          background: #000;
          border-radius: 12px;
          border: 1px solid var(--border-glass);
          padding: 1.5rem;
          overflow: auto;
        }

        .config-viewer h3 {
           margin-bottom: 1rem;
           color: var(--text-muted);
           font-size: 0.9rem;
        }

        pre {
          color: #a0a0a0;
          font-family: 'Fira Code', monospace;
          font-size: 0.85rem;
        }
      `}</style>
    </div>
  );
};

export default Synapse;
