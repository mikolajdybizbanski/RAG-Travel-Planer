export const API_URL = "http://localhost:8001";

export const BUDGET_CONFIG = {
  OnlyFreePlaces:    { label: "Free",     color: "#065f46", bg: "#ecfdf5", dot: "#10b981" },
  LimitedBudget:     { label: "Budget",   color: "#92400e", bg: "#fffbeb", dot: "#f59e0b" },
  MostPlacesAllowed: { label: "Moderate", color: "#1e40af", bg: "#eff6ff", dot: "#3b82f6" },
  OnlyHighEndPlaces: { label: "Premium",  color: "#5b21b6", bg: "#f5f3ff", dot: "#8b5cf6" },
  Unknown:           { label: "Any",      color: "#374151", bg: "#f9fafb", dot: "#9ca3af" },
};

export const CITIES = {
  Prague:    { emoji: "🇨🇿", img: "https://images.unsplash.com/photo-1519677100203-a0e668c92439?w=800&q=80", desc: "City of a Hundred Spires" },
  Budapest:  { emoji: "🇭🇺", img: "https://images.unsplash.com/photo-1541849546-216549ae216d?w=800&q=80", desc: "Pearl of the Danube" },
  Rovaniemi: { emoji: "🇫🇮", img: "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800&q=80", desc: "Gateway to the Arctic" },
  Dublin:    { emoji: "🇮🇪", img: "https://images.unsplash.com/photo-1549918864-48ac978761a4?w=800&q=80", desc: "The Fair City" },
};

export const PROMPTS = [
  { city: "Prague",   text: "3-day Prague trip on a budget" },
  { city: "Budapest", text: "Weekend in Budapest, start at Buda Castle" },
  { city: "Rovaniemi",text: "Luxury 2 days in Rovaniemi" },
  { city: "Prague",   text: "Free walking tour of Prague" },
  // { city: "Rovaniemi", text: "2 days in Rovaniemi in winter" },
];

export const DAY_COLORS = ["#0ea5e9","#10b981","#f59e0b","#ef4444"];