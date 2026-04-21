import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';

const ROUTER_NAMES = {
  '192.168.1.1': 'Școala 1',
  '192.168.2.1': 'Școala 2',
  '192.168.3.1': 'Școala 3',
  '192.168.4.1': 'Școala 4',
  '192.168.5.1': 'Grădinița 3',
};

function App() {
  const [tab, setTab] = useState('devices');
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [devicesRes, alertsRes] = await Promise.all([
        fetch(`${API_URL}/devices`),
        fetch(`${API_URL}/alerts`),
      ]);
      const [devicesData, alertsData] = await Promise.all([
        devicesRes.json(),
        alertsRes.json(),
      ]);
      setDevices(Array.isArray(devicesData) ? devicesData : []);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
    } catch (err) {
      console.error('Error fetching data:', err);
    }
    setLoading(false);
  }, [API_URL]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const locationStats = useMemo(() => {
    const counts = Object.keys(ROUTER_NAMES).reduce((acc, ip) => ({ ...acc, [ip]: 0 }), {});
    devices.forEach((device) => {
      const routerIp = device.latest_network?.router_ip;
      if (routerIp && !device.is_offline) {
        counts[routerIp] = (counts[routerIp] || 0) + 1;
      }
    });
    return counts;
  }, [devices]);

  const unresolvedAlerts = useMemo(
    () => alerts.filter((alert) => !alert.is_resolved),
    [alerts],
  );

  const formatDate = (value) => (value ? new Date(value).toLocaleString('ro-RO') : '-');
  const locationName = (routerIp) => ROUTER_NAMES[routerIp] || routerIp || '-';

  return (
    <div className="app">
      <header className="app-header">
        <h1>Network Monitor</h1>
        <p>{loading ? 'Actualizare...' : `Dispozitive: ${devices.length} | Alerte: ${alerts.length}`}</p>
      </header>

      <main className="app-main">
        <div className="tabs">
          <button className={tab === 'devices' ? 'tab active' : 'tab'} onClick={() => setTab('devices')}>Dispozitive</button>
          <button className={tab === 'alerts' ? 'tab active' : 'tab'} onClick={() => setTab('alerts')}>Alerte</button>
          <button className={tab === 'stats' ? 'tab active' : 'tab'} onClick={() => setTab('stats')}>Statistici</button>
        </div>

        {tab === 'devices' && (
          <section className="panel">
            <table>
              <thead>
                <tr>
                  <th>MAC Address</th>
                  <th>Hostname</th>
                  <th>IP curent</th>
                  <th>Locație</th>
                  <th>VLAN (dhcp_server)</th>
                  <th>Tip</th>
                  <th>Status</th>
                  <th>De încredere</th>
                  <th>Văzut de ori</th>
                  <th>Ultima dată văzut</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.mac_address}>
                    <td>{device.mac_address}</td>
                    <td>{device.hostname || '-'}</td>
                    <td>{device.latest_network?.ip_address || '-'}</td>
                    <td>{locationName(device.latest_network?.router_ip)}</td>
                    <td>{device.latest_network?.vlan || '-'}</td>
                    <td>{device.is_phone ? '📱 Telefon' : '💻 Alt dispozitiv'}</td>
                    <td>
                      <span className={device.is_offline ? 'badge badge-offline' : 'badge badge-online'}>
                        {device.is_offline ? '🔴 Offline' : '🟢 Online'}
                      </span>
                    </td>
                    <td>{device.is_trusted ? '✅' : '❌'}</td>
                    <td>{device.seen_count || 0}</td>
                    <td>{formatDate(device.last_seen)}</td>
                  </tr>
                ))}
                {!devices.length && (
                  <tr>
                    <td colSpan="10" className="empty">Nu există dispozitive.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        )}

        {tab === 'alerts' && (
          <section className="panel">
            <table>
              <thead>
                <tr>
                  <th>MAC Address</th>
                  <th>Tip alertă</th>
                  <th>Mesaj</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {unresolvedAlerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>{alert.mac_address}</td>
                      <td>{alert.alert_type}</td>
                      <td>{alert.message}</td>
                      <td>{formatDate(alert.created_at)}</td>
                    </tr>
                  ))}
                {!unresolvedAlerts.length && (
                  <tr>
                    <td colSpan="4" className="empty">Nu există alerte active.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        )}

        {tab === 'stats' && (
          <section className="panel stats-grid">
            {Object.entries(ROUTER_NAMES).map(([routerIp, name]) => (
              <article key={routerIp} className="stat-card">
                <h3>{name}</h3>
                <p>{locationStats[routerIp] || 0} dispozitive</p>
              </article>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
