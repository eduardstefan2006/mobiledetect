import React from 'react';
import { formatTimestamp } from '../utils';

function Locations({ locationSummaries, loading }) {
  if (loading) {
    return (
      <div className="location-card-grid">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="card skeleton-card" />
        ))}
      </div>
    );
  }

  return (
    <section className="location-card-grid">
      {locationSummaries.map((location) => (
        <article key={location.routerIp} className="card location-details-card">
          <div className="location-title">
            <span className="location-dot" style={{ backgroundColor: location.color }} />
            <h3>{location.name}</h3>
          </div>
          <ul>
            <li>Total dispozitive: <strong>{location.total}</strong></li>
            <li>Online acum: <strong>{location.online}</strong></li>
            <li>Telefoane detectate: <strong>{location.phones}</strong></li>
            <li>Ultimul scan: <strong>{location.latestSeen ? formatTimestamp(location.latestSeen) : '-'}</strong></li>
          </ul>
        </article>
      ))}
    </section>
  );
}

export default Locations;
