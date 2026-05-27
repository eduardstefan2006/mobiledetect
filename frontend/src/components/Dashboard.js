import React, { useMemo, useState } from 'react';
import { formatTimestamp } from '../utils';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const ipToNumber = (ip) => {
  if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(ip || '')) return -1;
  const parts = ip.split('.').map((part) => Number.parseInt(part, 10));
  if (parts.some((part) => part < 0 || part > 255)) return -1;
  return parts.reduce((total, part) => (total << 8) + part, 0);
};
const dedupeKey = (device) => {
  if (device.hostname) {
    const routerIp = device.latest_network?.router_ip || 'unknown';
    return `h:${device.hostname.toLowerCase()}@${routerIp}`;
  }
  return `m:${device.mac_address}`;
};

function Dashboard({ locationSummaries, devices, loading, locations, onSelectDevice }) {
  const [locationFilter, setLocationFilter] = useState('all');
  const [sortKey, setSortKey] = useState('last_seen');
  const [sortDir, setSortDir] = useState('desc');

  const barData = useMemo(() => locationSummaries.map((item) => ({
    name: item.name,
    online: item.online,
    offline: Math.max(item.total - item.online, 0),
  })), [locationSummaries]);

  const pieData = useMemo(() => {
    const phones = devices.filter((device) => device.is_phone).length;
    return [
      { name: 'Telefoane', value: phones, color: '#10b981' },
      { name: 'Alte dispozitive', value: Math.max(devices.length - phones, 0), color: '#6366f1' },
    ];
  }, [devices]);

  const onSort = (key) => {
    if (sortKey === key) setSortDir((direction) => (direction === 'asc' ? 'desc' : 'asc'));
    else {
      setSortKey(key);
      setSortDir('asc');
    }
  };
  const sortIndicator = (key) => (sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : '');

  const tableData = useMemo(() => {
    const sortedByActivity = [...devices].sort((a, b) => new Date(b.last_seen || 0) - new Date(a.last_seen || 0));
    const seen = new Set();
    const deduped = [];
    for (const device of sortedByActivity) {
      const key = dedupeKey(device);
      if (!seen.has(key)) {
        seen.add(key);
        deduped.push(device);
      }
    }

    let result = locationFilter === 'all'
      ? deduped
      : deduped.filter((device) => device.latest_network?.router_ip === locationFilter);

    result.sort((a, b) => {
      let aVal;
      let bVal;
      if (sortKey === 'hostname') {
        aVal = (a.hostname || a.vendor || '').toLowerCase();
        bVal = (b.hostname || b.vendor || '').toLowerCase();
      } else if (sortKey === 'ip') {
        aVal = ipToNumber(a.latest_network?.ip_address);
        bVal = ipToNumber(b.latest_network?.ip_address);
      } else if (sortKey === 'vlan') {
        aVal = a.latest_network?.vlan || '';
        bVal = b.latest_network?.vlan || '';
      } else if (sortKey === 'location') {
        aVal = (locations[a.latest_network?.router_ip]?.name || '').toLowerCase();
        bVal = (locations[b.latest_network?.router_ip]?.name || '').toLowerCase();
      } else {
        aVal = new Date(a.last_seen || 0).getTime();
        bVal = new Date(b.last_seen || 0).getTime();
      }
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return result.slice(0, 30);
  }, [devices, locationFilter, sortKey, sortDir, locations]);

  if (loading) {
    return (
      <section className="grid gap-16">
        <div className="location-card-grid">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="card skeleton-card" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="grid gap-16">
      <div className="location-card-grid">
        {locationSummaries.map((location) => (
          <article key={location.routerIp} className="card stat-card">
            <div className="card-title-row">
              <h3>{location.name}</h3>
              <span className="location-dot" style={{ backgroundColor: location.color }} />
            </div>
            <p className="stat-text">Online: {location.online}</p>
            <p className="muted">Telefoane: {location.phones}</p>
          </article>
        ))}
      </div>

      <div className="chart-grid">
        <article className="card chart-card">
          <h3>Dispozitive per locație</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
              <XAxis dataKey="name" stroke="#8892b0" />
              <YAxis stroke="#8892b0" />
              <Tooltip />
              <Legend />
              <Bar dataKey="online" fill="#10b981" radius={[6, 6, 0, 0]} />
              <Bar dataKey="offline" fill="#ef4444" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </article>
        <article className="card chart-card">
          <h3>Telefoane vs Alte dispozitive</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={92} innerRadius={50} label>
                {pieData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </article>
      </div>

      <article className="card">
        <h3>Activitate recentă</h3>
        <div className="filter-row" style={{ marginBottom: 12 }}>
          <button className={locationFilter === 'all' ? 'chip active' : 'chip'} onClick={() => setLocationFilter('all')}>
            Toate
          </button>
          {Object.entries(locations).map(([routerIp, location]) => (
            <button
              key={routerIp}
              className={locationFilter === routerIp ? 'chip active' : 'chip'}
              style={{ borderColor: location.color }}
              onClick={() => setLocationFilter(routerIp)}
            >
              <span className="location-dot" style={{ backgroundColor: location.color }} />
              {location.name}
            </button>
          ))}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>MAC Address</th>
                <th onClick={() => onSort('hostname')} className="sortable">Hostname{sortIndicator('hostname')}</th>
                <th onClick={() => onSort('ip')} className="sortable">IP{sortIndicator('ip')}</th>
                <th onClick={() => onSort('vlan')} className="sortable">VLAN{sortIndicator('vlan')}</th>
                <th onClick={() => onSort('location')} className="sortable">Locație{sortIndicator('location')}</th>
                <th onClick={() => onSort('last_seen')} className="sortable">Ultima activitate{sortIndicator('last_seen')}</th>
              </tr>
            </thead>
            <tbody>
              {tableData.map((device) => (
                <tr
                  key={device.mac_address}
                  onClick={() => onSelectDevice && onSelectDevice(device.mac_address)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault();
                      onSelectDevice && onSelectDevice(device.mac_address);
                    }
                  }}
                  className="clickable-row"
                  tabIndex={0}
                  role="button"
                >
                  <td>
                    {device.is_offline
                      ? <span style={{ color: '#ef4444' }}>🔴 {device.disconnected_at ? new Date(device.disconnected_at).toLocaleString('ro-RO') : 'Offline'}</span>
                      : <span style={{ color: '#10b981' }}>🟢 {device.connected_at ? new Date(device.connected_at).toLocaleString('ro-RO') : 'Online'}</span>
                    }
                  </td>
                  <td>{device.mac_address}</td>
                  <td>{device.hostname || (device.vendor ? `📱 ${device.vendor}` : (device.is_phone ? '📱' : '-'))}</td>
                  <td>{device.latest_network?.ip_address || '-'}</td>
                  <td>{device.latest_network?.vlan || '-'}</td>
                  <td>{locations[device.latest_network?.router_ip]?.name || '-'}</td>
                  <td>{formatTimestamp(device.last_seen)}</td>
                </tr>
              ))}
              {tableData.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty-state">Nu există activitate recentă.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

export default Dashboard;
