import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { Activity, Brain, Settings, Cpu, LineChart } from 'lucide-react';
import { motion } from 'framer-motion';

const Layout = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Activity, label: 'Mission Control' },
    { path: '/cortex', icon: Brain, label: 'Cortex' },
    { path: '/insights', icon: LineChart, label: 'Insights' },
    { path: '/synapse', icon: Settings, label: 'Synapse' },
  ];

  return (
    <div className="layout-container">
      {/* Sidebar */}
      <nav className="sidebar">
        <div className="logo-section">
          <Cpu className="logo-icon" size={32} color="var(--primary-cyan)" />
          <h1 className="logo-text">AMBROSE</h1>
        </div>

        <div className="nav-links">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
              {location.pathname === item.path && (
                <motion.div
                  layoutId="active-nav"
                  className="active-indicator"
                  initial={false}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
            </NavLink>
          ))}
        </div>

        <div className="system-status">
          <div className="status-dot pulsing"></div>
          <span>SYSTEM ONLINE</span>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>

      {/* Styles are defined inline or in CSS modules usually, but for simplicity using global CSS from index.css 
          referenced by classNames 
      */}
      <style>{`
        .layout-container {
          display: flex;
          height: 100vh;
          width: 100vw;
          overflow: hidden;
        }

        .sidebar {
          width: 260px;
          background: rgba(10, 10, 15, 0.6);
          backdrop-filter: blur(20px);
          border-right: 1px solid var(--border-glass);
          display: flex;
          flex-direction: column;
          padding: 2rem;
          z-index: 10;
        }

        .logo-section {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 3rem;
        }

        .logo-text {
          font-weight: 700;
          letter-spacing: 2px;
          color: var(--text-main);
          font-size: 1.2rem;
        }

        .nav-links {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          flex: 1;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.8rem 1rem;
          border-radius: 12px;
          color: var(--text-muted);
          text-decoration: none;
          position: relative;
          transition: all 0.3s ease;
        }

        .nav-item:hover {
          color: var(--text-main);
          background: rgba(255, 255, 255, 0.03);
        }

        .nav-item.active {
          color: var(--primary-cyan);
          background: rgba(255, 138, 138, 0.08);
        }

        .active-indicator {
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 3px;
          background: var(--primary-cyan);
          border-radius: 0 4px 4px 0;
        }

        .system-status {
          display: flex;
          align-items: center;
          gap: 0.8rem;
          padding: 1rem;
          background: rgba(0, 255, 96, 0.05);
          border: 1px solid rgba(0, 255, 96, 0.1);
          border-radius: 8px;
          color: var(--accent-green);
          font-size: 0.8rem;
          font-weight: 600;
          letter-spacing: 1px;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          background: var(--accent-green);
          border-radius: 50%;
          box-shadow: 0 0 10px var(--accent-green);
        }

        .pulsing {
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { opacity: 1; box-shadow: 0 0 0 0 rgba(10, 255, 96, 0.4); }
          70% { opacity: 0.6; box-shadow: 0 0 0 6px rgba(10, 255, 96, 0); }
          100% { opacity: 1; box-shadow: 0 0 0 0 rgba(10, 255, 96, 0); }
        }

        .main-content {
          flex: 1;
          overflow-y: auto;
          background: radial-gradient(circle at 50% -20%, #1a1a2e 0%, #0a0a0f 60%);
          padding: 2rem;
        }
      `}</style>
    </div>
  );
};

export default Layout;
