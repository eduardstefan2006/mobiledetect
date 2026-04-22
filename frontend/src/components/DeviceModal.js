import React, { useEffect, useMemo, useState } from 'react';
import { formatTimestamp } from '../utils';

const EVENT_LABELS = {
  connected: { label: 'Conectat', color: '#10b981' },
  disconnected: { label: 'Deconectat', color: '#ef4444' },
  network_change: { label: 'Schimbare rețea', color: '#f59e0b' },
};

function DeviceModal({ macAddress, isOpen, onClose, apiUrl, locations }) {
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !macAddress) return;

    const controller = new AbortController();

    const fetchDevice = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${apiUrl}/devices/${encodeURIComponent(macAddress)}`, {
          signal: controller.signal,
        });
        const payload = response.ok ? await response.json() : null;
        setDevice(payload);
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Failed to load device details', error);
          setDevice(null);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDevice();
    return () => controller.abort();
  }, [apiUrl, isOpen, macAddress]);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  const connectionLogs = useMemo(
    () => (Array.isArray(device?.connection_logs) ? device.connection_logs : []),
    [device?.connection_logs],
  );
  const lastDisconnectedAt = useMemo(
    () => connectionLogs.find((log) => log.event_type === 'disconnected')?.timestamp || null,
    [connectionLogs],
  );

  if (!isOpen) return null;

  const location = locations[device?.latest_network?.router_ip];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h3>Detalii dispozitiv</h3>
          <button className="icon-button" onClick={onClose}>✕</button>
        </div>

        {loading && <div className="skeleton-line" />}

        {!loading && !device && <p className="muted">Nu s-au putut încărca detaliile dispozitivului.</p>}

        {!loading && device && (
          <>
            <div className="details-grid">
              <p><strong>MAC:</strong> {device.mac_address}</p>
              <p><strong>Hostname:</strong> {device.hostname || '-'}</p>
              <p><strong>Vendor:</strong> {device.vendor || '-'}</p>
              <p><strong>IP curent:</strong> {device.latest_network?.ip_address || '-'}</p>
              <p><strong>Locație:</strong> {location?.name || '-'}</p>
              <p><strong>VLAN:</strong> {device.latest_network?.vlan || '-'}</p>
              <p><strong>Status:</strong> {device.is_offline ? 'Offline' : 'Online'}</p>
              <p><strong>Tip:</strong> {device.is_phone ? 'Telefon' : 'Alt dispozitiv'}</p>
              <p><strong>De încredere:</strong> {device.is_trusted ? 'Da' : 'Nu'}</p>
              <p><strong>Prima apariție:</strong> {formatTimestamp(device.first_seen)}</p>
              <p><strong>Ultima apariție:</strong> {formatTimestamp(device.last_seen)}</p>
              <p><strong>Ultima deconectare:</strong> {formatTimestamp(lastDisconnectedAt)}</p>
              <p><strong>Seen count:</strong> {device.seen_count || 0}</p>
            </div>

            <h4>Istoric conexiuni</h4>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Eveniment</th>
                    <th>IP</th>
                    <th>VLAN</th>
                    <th>Router</th>
                    <th>Timp</th>
                  </tr>
                </thead>
                <tbody>
                  {connectionLogs.map((log, index) => {
                    const meta = EVENT_LABELS[log.event_type] || { label: log.event_type, color: '#8892b0' };
                    return (
                      <tr key={`${log.timestamp}-${index}`}>
                        <td>
                          <span style={{ color: meta.color, fontWeight: 600 }}>
                            {meta.label}
                          </span>
                        </td>
                        <td>{log.ip_address || '-'}</td>
                        <td>{log.vlan || '-'}</td>
                        <td>{locations[log.router_ip]?.name || log.router_ip || '-'}</td>
                        <td>{formatTimestamp(log.timestamp)}</td>
                      </tr>
                    );
                  })}
                  {!connectionLogs.length && (
                    <tr>
                      <td colSpan="5" className="empty-state">Nu există istoric disponibil.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default DeviceModal;
