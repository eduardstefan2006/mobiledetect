import React from 'react';

const items = [
  { key: 'dashboard', label: '📊 Dashboard' },
  { key: 'devices', label: '📱 Dispozitive' },
  { key: 'alerts', label: '🔔 Alerte' },
  { key: 'locations', label: '🗺️ Locații' },
  { key: 'logs', label: '📋 Loguri' },
];

function Sidebar({ activePage, onNavigate, unresolvedAlerts }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">NM</div>
        <div>
          <h2>Network Monitor</h2>
          <p>control panel</p>
        </div>
      </div>
      <nav className="sidebar-nav">
        {items.map((item) => (
          <button
            key={item.key}
            className={item.key === activePage ? 'nav-item active' : 'nav-item'}
            onClick={() => onNavigate(item.key)}
          >
            <span>{item.label}</span>
            {item.key === 'alerts' && unresolvedAlerts > 0 ? (
              <span className="alert-badge">{unresolvedAlerts}</span>
            ) : null}
          </button>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
