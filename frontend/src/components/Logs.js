import React, { useEffect, useMemo, useState } from 'react';

const ROUTER_LOCATIONS = {
  '192.168.1.1': 'Școala 1',
  '192.168.2.1': 'Școala 2',
  '192.168.3.1': 'Școala 3',
  '192.168.4.1': 'Școala 4',
  '192.168.5.1': 'Grădinița 3',
};

const FILTERS = [
  { key: 'all', label: 'Toate' },
  { key: 'connected', label: 'Conectări' },
  { key: 'disconnected', label: 'Deconectări' },
  { key: 'network_change', label: 'Schimbări rețea' },
];

const EVENT_META = {
  connected: { label: 'connected', className: 'success' },
  disconnected: { label: 'disconnected', className: 'danger' },
  network_change: { label: 'network_change', className: 'info' },
};

const formatRelativeTime = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  const diffSec = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (diffSec < 5) return 'acum';
  if (diffSec < 60) return `acum ${diffSec}s`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `acum ${diffMin} min`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `acum ${diffHours}h`;
  return `acum ${Math.floor(diffHours / 24)}z`;
};

function Logs({ API_URL }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    let mounted = true;
    const fetchLogs = async () => {
      try {
        const response = await fetch(`${API_URL}/logs`);
        const data = response.ok ? await response.json() : [];
        if (mounted) {
          setLogs(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        console.error('Failed to fetch logs', error);
        if (mounted) {
          setLogs([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [API_URL]);

  const filteredLogs = useMemo(() => {
    const needle = searchTerm.trim().toLowerCase();
    return logs.filter((log) => {
      if (activeFilter !== 'all' && log.event_type !== activeFilter) {
        return false;
      }
      if (!needle) {
        return true;
      }
      const mac = (log.mac_address || '').toLowerCase();
      const hostname = (log.hostname || '').toLowerCase();
      return mac.includes(needle) || hostname.includes(needle);
    });
  }, [logs, activeFilter, searchTerm]);

  return (
    <div className="grid gap-16">
      <section className="card filter-card">
        <div className="filter-row">
          {FILTERS.map((filter) => (
            <button
              key={filter.key}
              className={filter.key === activeFilter ? 'chip active' : 'chip'}
              onClick={() => setActiveFilter(filter.key)}
            >
              {filter.label}
            </button>
          ))}
        </div>
        <input
          className="search-input"
          placeholder="Caută după MAC sau hostname..."
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />
      </section>

      <section className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Eveniment</th>
                <th>MAC / Hostname</th>
                <th>Locație</th>
                <th>IP</th>
                <th>VLAN</th>
                <th>Timp</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="empty-state">
                    Se încarcă logurile...
                  </td>
                </tr>
              ) : filteredLogs.length ? (
                filteredLogs.map((log) => {
                  const meta = EVENT_META[log.event_type] || { label: log.event_type, className: 'warning' };
                  const location = ROUTER_LOCATIONS[log.router_ip] || log.router_ip || '-';
                  const ipValue = log.event_type === 'network_change' && log.old_ip
                    ? `${log.old_ip} → ${log.ip_address || '-'}`
                    : (log.ip_address || '-');
                  return (
                    <tr key={log.id}>
                      <td>
                        <span className={`badge ${meta.className}`}>{meta.label}</span>
                      </td>
                      <td>
                        <div>{log.mac_address || '-'}</div>
                        <small className="muted">{log.hostname || '-'}</small>
                      </td>
                      <td>{location}</td>
                      <td>{ipValue}</td>
                      <td>{log.vlan || '-'}</td>
                      <td>{formatRelativeTime(log.timestamp)}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="empty-state">
                    Nu există loguri pentru filtrul selectat.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default Logs;
