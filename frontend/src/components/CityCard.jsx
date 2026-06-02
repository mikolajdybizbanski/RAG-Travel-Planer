import React from "react";

export default function CityCard({ name, data, onClick }) {
  return (
    <button className="city-card" onClick={onClick}>
      <img src={data.img} alt={name} className="city-card-img" />
      <div className="city-card-overlay" />
      <div className="city-card-content">
        <div className="city-card-name">{data.emoji} {name}</div>
        <div className="city-card-desc">{data.desc}</div>
      </div>
    </button>
  );
}