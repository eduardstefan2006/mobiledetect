import React, { useMemo } from 'react';
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

function Dashboard({ locationSummaries, devices, recentActivity, loading, formatRelativeTime, locations }) {
  const barData = useMemo(
    () =>
      locationSummaries.map((item) => ({
        name: item.name,
        online: item.online,
        offline: Math.max(item.total - item.online, 0),
      })),
    [locationSummaries],
  );

  const pieData = useMemo(() => {
    const phones = devices.filter((device) => device.is_phone).length;
    const others = Math.max(devices.length - phones, 0);
    return [
      { name: 'Telefoane', value: phones, color: '#10b981' },
      { name: 'Alte dispozitive', value: others, color: '#6366f1' },
    ];
  }, [devices]);

  if (loading) {
    return (
      <section className="grid gap-16">
        <div className="location-card-grid">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="card skeleton-card" />
          ))}
        </div>
        <div className="chart-grid">
          <div className="card skeleton-card chart-skeleton" />
          <div className="card skeleton-card chart-skeleton" />
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
                {pieData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </article>
      </div>

      <article className="card">
        <h3>Activitate recentă</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>MAC Address</th>
                <th>Hostname</th>
                <th>IP</th>
                <th>Locație</th>
                <th>Ultima activitate</th>
              </tr>
            </thead>
            <tbody>
              {recentActivity.map((device) => (
                <tr key={device.mac_address}>
                  <td>{device.mac_address}</td>
                  <td>{device.hostname || device.vendor || '-'}</td>
                  <td>{device.latest_network?.ip_address || '-'}</td>
                  <td>{locations[device.latest_network?.router_ip]?.name || '-'}</td>
                  <td>{formatRelativeTime(device.last_seen)}</td>
                </tr>
              ))}
              {recentActivity.length === 0 && (
                <tr>
                  <td colSpan="5" className="empty-state">Nu există activitate recentă.</td>
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
