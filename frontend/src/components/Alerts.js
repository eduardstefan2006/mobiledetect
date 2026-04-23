import React, { useMemo, useState } from 'react';
import { formatTimestamp } from '../utils';

function Alerts({ alerts, loading, apiUrl, onRefresh }) {
  const [isResolvingAll, setIsResolvingAll] = useState(false);
  const [resolvingId, setResolvingId] = useState(null);
  const sortedAlerts = useMemo(
    () => [...alerts].sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()),
    [alerts],
  );

  const resolveOne = async (alertId) => {
    if (!apiUrl || isResolvingAll || resolvingId !== null) {
      return;
    }

    setResolvingId(alertId);
    try {
      const response = await fetch(`${apiUrl}/alerts/${alertId}/resolve`, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`Resolve alert failed with status ${response.status}`);
      }
      await onRefresh?.();
    } catch (error) {
      console.error('Failed to resolve alert', error);
    } finally {
      setResolvingId(null);
    }
  };

  const resolveAll = async () => {
    if (!apiUrl || isResolvingAll || resolvingId !== null) {
      return;
    }

    setIsResolvingAll(true);
    try {
      const response = await fetch(`${apiUrl}/alerts/resolve-all`, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`Resolve all alerts failed with status ${response.status}`);
      }
      await onRefresh?.();
    } catch (error) {
      console.error('Failed to resolve all alerts', error);
    } finally {
      setIsResolvingAll(false);
    }
  };

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
      <div className="alert-actions-row">
        <button
          className="chip"
          onClick={resolveAll}
          disabled={isResolvingAll || resolvingId !== null}
        >
          {isResolvingAll ? 'Rezolv...' : `Rezolvă toate (${sortedAlerts.length})`}
        </button>
      </div>

      {sortedAlerts.map((alert) => (
        <article key={alert.id} className="card alert-item">
          <div className="alert-item-top">
            <span className={alert.alert_type === 'new_device' ? 'badge warning' : 'badge'}>{alert.alert_type}</span>
            <span className="muted">{formatTimestamp(alert.created_at)}</span>
          </div>
          <h4>{alert.mac_address}</h4>
          <p>{alert.message}</p>
          <div className="alert-item-bottom">
            <button
              className="chip"
              onClick={() => resolveOne(alert.id)}
              disabled={isResolvingAll || resolvingId !== null}
            >
              {resolvingId === alert.id ? 'Rezolv...' : 'Rezolvă'}
            </button>
          </div>
        </article>
      ))}
    </section>
  );
}

export default Alerts;
