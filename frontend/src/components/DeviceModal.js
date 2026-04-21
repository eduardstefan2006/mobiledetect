import React, { useEffect, useMemo, useState } from 'react';

function DeviceModal({ macAddress, isOpen, onClose, apiUrl, formatRelativeTime, locations }) {
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

  const history = useMemo(() => (Array.isArray(device?.history) ? device.history : []), [device?.history]);

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
              <p><strong>Prima apariție:</strong> {formatRelativeTime(device.first_seen)}</p>
              <p><strong>Ultima apariție:</strong> {formatRelativeTime(device.last_seen)}</p>
              <p><strong>Seen count:</strong> {device.seen_count || 0}</p>
            </div>

            <h4>Istoric IP</h4>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>IP Address</th>
                    <th>VLAN</th>
                    <th>Router</th>
                    <th>Timp</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((entry, index) => (
                    <tr key={`${entry.timestamp}-${entry.ip_address}-${index}`}>
                      <td>{entry.ip_address || '-'}</td>
                      <td>{entry.vlan || '-'}</td>
                      <td>{locations[entry.router_ip]?.name || entry.router_ip || '-'}</td>
                      <td>{formatRelativeTime(entry.timestamp)}</td>
                    </tr>
                  ))}
                  {!history.length && (
                    <tr>
                      <td colSpan="4" className="empty-state">Nu există istoric disponibil.</td>
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
