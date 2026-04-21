import React, { useMemo } from 'react';
import { formatTimestamp } from '../utils';

function Alerts({ alerts, loading }) {
  const sortedAlerts = useMemo(
    () => [...alerts].sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()),
    [alerts],
  );

  if (loading) {
    return (
      <div className="card">
        <div className="skeleton-line" />
        <div className="skeleton-line" />
      </div>
    );
  }

  if (!sortedAlerts.length) {
    return (
      <article className="card empty-alerts">
        <h3>Totul este în regulă ✅</h3>
        <p>Nu există alerte în acest moment.</p>
      </article>
    );
  }

  return (
    <section className="grid gap-16">
      {sortedAlerts.map((alert) => (
        <article key={alert.id} className="card alert-item">
          <div className="alert-item-top">
            <span className={alert.alert_type === 'new_device' ? 'badge warning' : 'badge'}>{alert.alert_type}</span>
            <span className="muted">{formatTimestamp(alert.created_at)}</span>
          </div>
          <h4>{alert.mac_address}</h4>
          <p>{alert.message}</p>
        </article>
      ))}
    </section>
  );
}

export default Alerts;
