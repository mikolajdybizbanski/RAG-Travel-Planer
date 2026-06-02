import React, { useState, useRef, useEffect } from "react";
import "./index.css"; 
import { API_URL, BUDGET_CONFIG, CITIES, PROMPTS } from "./constants";
import AiMessage from "./components/AiMessage";
import UserMessage from "./components/UserMessage";
import CityCard from "./components/CityCard";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [city, setCity] = useState(null);
  const [budget, setBudget] = useState("Unknown");
  const [startPointId, setStartPointId] = useState(null);
  const [startPointName, setStartPointName] = useState(null);
  
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => { 
    bottomRef.current?.scrollIntoView({ behavior: "smooth" }); 
  }, [messages, loading]);

  const send = async (override) => {
    const text = (override ?? input).trim();
    if (!text || loading) return;
    setInput("");
    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setLoading(true);
    
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next, city, budget, start_point_id: startPointId }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Server error");
      
      const data = await res.json();
      setMessages([...next, { role: "assistant", content: data.reply }]);
      
      if (data.city) setCity(data.city);
      if (data.budget && data.budget !== "Unknown") setBudget(data.budget);
      if (data.start_point_id) setStartPointId(data.start_point_id);
      if (data.start_point_name) setStartPointName(data.start_point_name);
    } catch(e) {
      setMessages([...next, { role: "assistant", content: `⚠️ ${e.message}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 30);
    }
  };

  const reset = () => {
    setMessages([]); setCity(null); setBudget("Unknown");
    setStartPointId(null); setStartPointName(null); setInput("");
  };

  const bcfg = BUDGET_CONFIG[budget] || BUDGET_CONFIG.Unknown;
  const cityData = city ? CITIES[city] : null;
  const isEmpty = messages.length === 0;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <div className="sidebar">
        <div className={`sidebar-hero ${cityData ? "" : "sidebar-hero-border sidebar-hero-default"}`}>
          {cityData && (
            <img src={cityData.img} alt={city} className="sidebar-hero-img" />
          )}
          {cityData && <div className="sidebar-hero-overlay" />}
          
          {!cityData && (
            <div className="sidebar-hero-content">
              <div className="sidebar-icon-wrapper">✦</div>
              <div className="sidebar-title">TripPlanner AI</div>
              <div className="sidebar-subtitle">RAG-powered city guide</div>
            </div>
          )}
          
          {cityData && (
            <div className="sidebar-city-info">
              <div className="sidebar-city-name">{cityData.emoji} {city}</div>
              <div className="sidebar-city-desc">{cityData.desc}</div>
            </div>
          )}
        </div>

        <div className="sidebar-body">
          {/* Trip info */}
          {(city || budget !== "Unknown") && (
            <div>
              <div className="section-title">Trip details</div>
              <div className="details-list">
                {startPointName && (
                  <div className="start-point-box">
                    <span style={{ fontSize: 15 }}>📍</span>
                    <div>
                      <div className="start-point-label">Start point</div>
                      <div className="start-point-name">{startPointName}</div>
                    </div>
                  </div>
                )}
                <div 
                  className="budget-badge" 
                  style={{ background: bcfg.bg, border: `1px solid ${bcfg.dot}30` }}
                >
                  <div className="budget-dot" style={{ background: bcfg.dot }} />
                  <span className="budget-text" style={{ color: bcfg.color }}>
                    {bcfg.label} budget
                  </span>
                </div>
              </div>
              <button className="btn-new-trip" onClick={reset}>
                ↩ New trip
              </button>
            </div>
          )}

          {/* City cards */}
          {!city && (
            <div>
              <div className="section-title">Destinations</div>
              <div className="destinations-grid">
                {Object.entries(CITIES).map(([name, data]) => (
                  <CityCard key={name} name={name} data={data} onClick={() => send(`Plan a 3-day trip to ${name}`)} />
                ))}
              </div>
            </div>
          )}

          <div className="sidebar-footer">
            Powered by Groq · ChromaDB · RAG<br/>
          </div>
        </div>
      </div>

      {/* Chat area */}
      <div className="chat-container">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-status">
            <div className={`status-dot ${loading ? 'loading' : 'ready'}`} />
            <span className="topbar-title">
              {loading ? "Planning your route…" : city ? `Exploring ${city}` : "AI Travel Planner"}
            </span>
          </div>
          <div className="topbar-filters">
            {Object.entries(BUDGET_CONFIG).filter(([k]) => k !== "Unknown").map(([k, v]) => (
              <span key={k} className="filter-badge" style={{
                background: budget === k ? v.bg : "transparent",
                border: `1px solid ${budget === k ? v.dot + "50" : "#e2e8f0"}`,
                color: budget === k ? v.color : "#94a3b8",
                fontWeight: budget === k ? 600 : 400,
              }}>
                {v.label}
              </span>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="messages-area">
          {isEmpty && (
            <div className="empty-state">
              <div className="empty-title">Where to next?</div>
              <div className="empty-subtitle">
                Tell me your destination, travel style, and budget —
                I'll plan a perfectly-routed, time-blocked itinerary.
              </div>
              <div className="prompts-container">
                {PROMPTS.map((p, i) => (
                  <button key={i} className="chip" onClick={() => send(p.text)}>
                    <span>{p.icon}</span>{p.text}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="messages-list">
            {messages.map((m, i) =>
              m.role === "user"
                ? <UserMessage key={i} content={m.content} />
                : <AiMessage key={i} content={m.content} loading={false} />
            )}
            {loading && <AiMessage content="" loading={true} />}
          </div>
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="textarea-wrapper">
            <textarea
              ref={textareaRef}
              className="chat-input"
              value={input}
              rows={2}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="e.g. 3 days in Budapest, moderate budget, start at Buda Castle…"
            />
            <button
              className="btn-send"
              onClick={() => send()}
              disabled={!input.trim() || loading}
            >
              ↑
            </button>
          </div>
          <div className="input-hint">
            Enter to send · Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
}