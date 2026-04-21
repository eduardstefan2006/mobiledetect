import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/devices`);
      const data = await res.json();
      setDevices(data);
    } catch (err) {
      console.error('Error fetching devices:', err);
    }
    setLoading(false);
  };

  const handleScan = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/devices/scan`, { method: 'POST' });
      const data = await res.json();
      console.log('Scan result:', data);
      fetchDevices();
    } catch (err) {
      console.error('Error scanning:', err);
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Network Monitor</h1>
        <button onClick={handleScan} disabled={loading}>
          {loading ? 'Scanning...' : 'Scan Network'}
        </button>
      </header>

      <main>
        <section className="devices-list">
          <h2>Devices ({devices.length})</h2>
          {devices.length === 0 ? (
            <p>No devices found. Run a scan.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>MAC Address</th>
                  <th>IP Address</th>
                  <th>Name</th>
                  <th>Mobile</th>
                  <th>Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((dev) => (
                  <tr key={dev.mac}>
                    <td>{dev.mac}</td>
                    <td>{dev.ip}</td>
                    <td>{dev.name || '-'}</td>
                    <td>{dev.is_mobile ? 'Yes' : 'No'}</td>
                    <td>{new Date(dev.last_seen).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
