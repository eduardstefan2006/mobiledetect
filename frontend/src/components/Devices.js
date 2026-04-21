import React, { useMemo, useState } from 'react';

const quickFilters = [
  { key: 'all', label: 'Toate' },
  { key: 'online', label: 'Online' },
  { key: 'offline', label: 'Offline' },
  { key: 'phones', label: 'Telefoane' },
  { key: 'trusted', label: 'De încredere' },
];

function Devices({ devices, loading, formatRelativeTime, locations, onSelectDevice }) {
  const [search, setSearch] = useState('');
  const [quickFilter, setQuickFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');
  const [sortKey, setSortKey] = useState('last_seen');
  const [sortDirection, setSortDirection] = useState('desc');

  const filteredDevices = useMemo(() => {
    const normalizedSearch = search.toLowerCase();

    return devices
      .filter((device) => {
        const searchFields = [
          device.mac_address,
          device.hostname,
          device.latest_network?.ip_address,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();

        if (normalizedSearch && !searchFields.includes(normalizedSearch)) {
          return false;
        }

        if (quickFilter === 'online' && device.is_offline) return false;
        if (quickFilter === 'offline' && !device.is_offline) return false;
        if (quickFilter === 'phones' && !device.is_phone) return false;
        if (quickFilter === 'trusted' && !device.is_trusted) return false;

        if (locationFilter !== 'all' && device.latest_network?.router_ip !== locationFilter) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        const aValue =
          sortKey === 'status'
            ? (a.is_offline ? 1 : 0)
            : sortKey === 'hostname'
              ? (a.hostname || a.vendor || '').toLowerCase()
              : sortKey === 'location'
                ? (locations[a.latest_network?.router_ip]?.name || '').toLowerCase()
                : sortKey === 'last_seen'
                  ? new Date(a.last_seen || 0).getTime()
                  : sortKey === 'seen_count'
                    ? a.seen_count || 0
                    : sortKey === 'mac_address'
                      ? (a.mac_address || '').toLowerCase()
                      : sortKey === 'ip_address'
                        ? (a.latest_network?.ip_address || '').toLowerCase()
                        : '';

        const bValue =
          sortKey === 'status'
            ? (b.is_offline ? 1 : 0)
            : sortKey === 'hostname'
              ? (b.hostname || b.vendor || '').toLowerCase()
              : sortKey === 'location'
                ? (locations[b.latest_network?.router_ip]?.name || '').toLowerCase()
                : sortKey === 'last_seen'
                  ? new Date(b.last_seen || 0).getTime()
                  : sortKey === 'seen_count'
                    ? b.seen_count || 0
                    : sortKey === 'mac_address'
                      ? (b.mac_address || '').toLowerCase()
                      : sortKey === 'ip_address'
                        ? (b.latest_network?.ip_address || '').toLowerCase()
                        : '';

        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
  }, [devices, locationFilter, locations, quickFilter, search, sortDirection, sortKey]);

  const onSort = (key) => {
    if (sortKey === key) {
      setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setSortKey(key);
    setSortDirection('asc');
  };

  if (loading) {
    return (
      <div className="card">
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
      </div>
    );
  }

  return (
    <section className="grid gap-16">
      <article className="card filter-card">
        <input
          className="search-input"
          placeholder="Caută după MAC, hostname sau IP"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <div className="filter-row">
          {quickFilters.map((filter) => (
            <button
              key={filter.key}
              className={quickFilter === filter.key ? 'chip active' : 'chip'}
              onClick={() => setQuickFilter(filter.key)}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="filter-row">
          <button className={locationFilter === 'all' ? 'chip active' : 'chip'} onClick={() => setLocationFilter('all')}>
            Toate locațiile
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
      </article>

      <article className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th onClick={() => onSort('status')} className="sortable">Status</th>
                <th onClick={() => onSort('mac_address')} className="sortable">MAC Address</th>
                <th onClick={() => onSort('hostname')} className="sortable">Hostname / Vendor</th>
                <th onClick={() => onSort('ip_address')} className="sortable">IP curent</th>
                <th onClick={() => onSort('location')} className="sortable">Locație</th>
                <th>VLAN</th>
                <th>Tip</th>
                <th>De încredere</th>
                <th onClick={() => onSort('seen_count')} className="sortable">Văzut de N ori</th>
                <th onClick={() => onSort('last_seen')} className="sortable">Ultima dată</th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.map((device) => {
                const location = locations[device.latest_network?.router_ip];
                return (
                  <tr key={device.mac_address} onClick={() => onSelectDevice(device.mac_address)} className="clickable-row">
                    <td>
                      <span className={device.is_offline ? 'badge danger' : 'badge success'}>
                        {device.is_offline ? '🔴 Offline' : '🟢 Online'}
                      </span>
                    </td>
                    <td>{device.mac_address}</td>
                    <td>{device.hostname || device.vendor || '-'}</td>
                    <td>{device.latest_network?.ip_address || '-'}</td>
                    <td>
                      {location ? (
                        <span className="location-badge" style={{ backgroundColor: `${location.color}22`, borderColor: location.color }}>
                          {location.name}
                        </span>
                      ) : '-'}
                    </td>
                    <td>{device.latest_network?.vlan || '-'}</td>
                    <td>{device.is_phone ? '📱' : '💻'}</td>
                    <td>{device.is_trusted ? '✅' : '❌'}</td>
                    <td>{device.seen_count || 0}</td>
                    <td>{formatRelativeTime(device.last_seen)}</td>
                  </tr>
                );
              })}
              {filteredDevices.length === 0 && (
                <tr>
                  <td colSpan="10" className="empty-state">Nu există dispozitive pentru filtrele selectate.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

export default Devices;
