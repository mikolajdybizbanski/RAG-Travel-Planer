import React from "react";
import { DAY_COLORS } from "../constants";

export default function ItineraryCards({ days }) {
  return (
    <div className="itinerary-list">
      {days.map((d, di) => {
        const col = DAY_COLORS[di % DAY_COLORS.length];
        
        return (
          <div key={di} className="itinerary-card">
            {/* Header uses dynamic background */}
            <div className="itinerary-header" style={{ background: col }}>
              <div className="itinerary-day-badge">{d.day}</div>
              <span className="itinerary-day-title">Day {d.day}</span>
              <span className="itinerary-day-stops">{d.entries.length} stops</span>
            </div>
            
            <div className="itinerary-body">
              {d.entries.map((e, ei) => (
                <div key={ei} className="itinerary-stop">
                  {/* Timeline bar dynamically colored */}
                  <div className="itinerary-stop-line" style={{ background: `${col}30` }} />
                  
                  <div className="itinerary-stop-content">
                    <div className="itinerary-time-wrap">
                      <div className="itinerary-time-start" style={{ color: col }}>{e.start}</div>
                      <div className="itinerary-time-end">→ {e.end}</div>
                    </div>
                    <div className="itinerary-stop-details">
                      <div className="itinerary-stop-name">{e.name}</div>
                      {e.note && <div className="itinerary-stop-note">{e.note}</div>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}