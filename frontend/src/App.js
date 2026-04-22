import React, { useCallback, useEffect, useMemo, useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Devices from './components/Devices';
import Alerts from './components/Alerts';
import Locations from './components/Locations';
import Logs from './components/Logs';
import DeviceModal from './components/DeviceModal';
import { formatTimestamp } from './utils';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const LOCATIONS = {
  '192.168.1.1': { name: 'Școala 1', color: '#3b82f6' },
  '192.168.2.1': { name: 'Școala 2', color: '#10b981' },
  '192.168.3.1': { name: 'Școala 3', color: '#f59e0b' },
  '192.168.4.1': { name: 'Școala 4', color: '#8b5cf6' },
  '192.168.5.1': { name: 'Grădinița 3', color: '#ec4899' },
};

const PAGE_TITLES = {
  dashboard: 'Dashboard',
  devices: 'Dispozitive',
  alerts: 'Alerte',
  locations: 'Locații',
  logs: 'Loguri',
};

const toArray = (value) => (Array.isArray(value) ? value : []);

export const formatRelativeTime = formatTimestamp;

function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshIn, setRefreshIn] = useState(30);
  const [selectedMac, setSelectedMac] = useState(null);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [devicesResponse, alertsResponse] = await Promise.all([
        fetch(`${API_URL}/devices?phones_only=true`),
        fetch(`${API_URL}/alerts`),
      ]);
      const [devicesData, alertsData] = await Promise.all([
        devicesResponse.ok ? devicesResponse.json() : [],
        alertsResponse.ok ? alertsResponse.json() : [],
      ]);
      setDevices(toArray(devicesData));
      setAlerts(toArray(alertsData));
    } catch (error) {
      console.error('Failed to fetch monitoring data', error);
      setDevices([]);
      setAlerts([]);
    } finally {
      setIsInitialLoading(false);
      setIsRefreshing(false);
      setRefreshIn(30);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const refreshInterval = setInterval(fetchData, 30000);
    return () => clearInterval(refreshInterval);
  }, [fetchData]);

  useEffect(() => {
    const countdownInterval = setInterval(() => {
      setRefreshIn((previous) => (previous <= 1 ? 30 : previous - 1));
    }, 1000);
    return () => clearInterval(countdownInterval);
  }, []);

  const unresolvedAlerts = useMemo(
    () => alerts.filter((alert) => !alert.is_resolved),
    [alerts],
  );

  const totals = useMemo(() => {
    const online = devices.filter((device) => !device.is_offline).length;
    const phones = devices.filter((device) => device.is_phone).length;
    return {
      total: devices.length,
      online,
      phones,
      alerts: unresolvedAlerts.length,
    };
  }, [devices, unresolvedAlerts.length]);

  const locationSummaries = useMemo(() => {
    return Object.entries(LOCATIONS).map(([routerIp, meta]) => {
      const locationDevices = devices.filter((device) => device.latest_network?.router_ip === routerIp);
      const online = locationDevices.filter((device) => !device.is_offline).length;
      const phones = locationDevices.filter((device) => device.is_phone).length;
      const latestSeen = locationDevices
        .map((device) => device.last_seen)
        .filter(Boolean)
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0] || null;

      return {
        routerIp,
        ...meta,
        total: locationDevices.length,
        online,
        phones,
        latestSeen,
      };
    });
  }, [devices]);

  const recentActivity = useMemo(() => {
    const sorted = [...devices].sort(
      (a, b) => new Date(b.last_seen || 0).getTime() - new Date(a.last_seen || 0).getTime(),
    );

    const seenHostnames = new Set();
    const deduplicated = [];
    for (const device of sorted) {
      const key = (device.hostname || device.vendor || device.mac_address || '').toLowerCase().trim();
      if (!seenHostnames.has(key)) {
        seenHostnames.add(key);
        deduplicated.push(device);
      }
    }

    return deduplicated.slice(0, 20);
  }, [devices]);

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        unresolvedAlerts={unresolvedAlerts.length}
      />
      <div className="app-content">
        <header className="top-header">
          <div>
            <h1>{PAGE_TITLES[activePage]}</h1>
            <div className="live-row">
              <span className="live-dot" />
              <span className="live-label">LIVE</span>
              <span className="refresh-counter">Refresh în {refreshIn}s</span>
            </div>
          </div>
          <div className="header-right">
            <div className="counter-grid">
              <span>Total: {totals.total}</span>
              <span>Online: {totals.online}</span>
              <span>Telefoane: {totals.phones}</span>
              <span>Alerte noi: {totals.alerts}</span>
            </div>
            <button className="refresh-button" onClick={fetchData} disabled={isRefreshing}>
              {isRefreshing ? 'Actualizare...' : 'Refresh'}
            </button>
          </div>
        </header>

        <main className="page-area">
          {activePage === 'dashboard' && (
            <Dashboard
              locationSummaries={locationSummaries}
              devices={devices}
              recentActivity={recentActivity}
              loading={isInitialLoading}
              locations={LOCATIONS}
              onSelectDevice={setSelectedMac}
            />
          )}
          {activePage === 'devices' && (
            <Devices
              devices={devices}
              loading={isInitialLoading}
              locations={LOCATIONS}
              onSelectDevice={setSelectedMac}
            />
          )}
          {activePage === 'alerts' && (
            <Alerts alerts={alerts} loading={isInitialLoading} />
          )}
          {activePage === 'locations' && (
            <Locations
              locationSummaries={locationSummaries}
              loading={isInitialLoading}
            />
          )}
          {activePage === 'logs' && (
            <Logs API_URL={API_URL} />
          )}
        </main>
      </div>
      <DeviceModal
        macAddress={selectedMac}
        isOpen={Boolean(selectedMac)}
        onClose={() => setSelectedMac(null)}
        apiUrl={API_URL}
        locations={LOCATIONS}
      />
    </div>
  );
}

export default App;
