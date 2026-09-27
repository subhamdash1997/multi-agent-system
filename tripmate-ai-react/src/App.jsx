import React, { useState } from "react";
import { MapPinned, Plane, Sparkles, Search, Send, Globe2, LoaderCircle, AlertCircle } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const examples = [
  "Plan a complete 7 days Japan trip from India under 2 lakhs...",
  "Plan a 5 day Dubai trip including flights, hotels and sightseeing...",
  "Plan a Thailand vacation with flights, hotels and activities...",
  "Find global flight options and build a complete itinerary..."
];

const createThreadId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `thread-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
};

function App() {
  const [prompt, setPrompt] = useState("");
  const [active, setActive] = useState(null);
  const [result, setResult] = useState(null);
  const [threadId, setThreadId] = useState(() => createThreadId());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const chips = [
    { label: "Japan Trip", icon: <MapPinned size={12} /> },
    { label: "Dubai Trip", icon: <Globe2 size={12} /> },
    { label: "Thailand Trip", icon: <Plane size={12} /> },
    { label: "Global Flights", icon: <Search size={12} /> }
  ];

  const handleGenerate = async (event) => {
    event.preventDefault();
    const userInput = prompt.trim();

    if (!userInput || loading) {
      setError("Enter a travel request before generating a plan.");
      return;
    }

    const requestThreadId = threadId || createThreadId();
    if (!threadId) {
      setThreadId(requestThreadId);
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/travel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: userInput, thread_id: requestThreadId }),
      });
      const data = await response.json();

      if (!response.ok) {
        const detail = typeof data.detail === "string"
          ? data.detail
          : "The travel API could not create a plan.";
        throw new Error(response.status === 429
          ? `${detail} Please wait a minute and try again.`
          : detail);
      }

      setResult(data);
      setThreadId(data.thread_id);
    } catch (requestError) {
      setError(requestError.message || "Unable to connect to the travel API.");
    } finally {
      setLoading(false);
    }
  };

  const selectChip = (label) => {
    setActive(label);
    const index = chips.findIndex((chip) => chip.label === label);
    setPrompt(examples[index] || examples[0]);
  };

  return (
    <main className="page-shell">
      <div className="ambient ambient-blue" />
      <div className="ambient ambient-purple" />
      <div className="ambient ambient-cyan" />

      <section className="hero">
        <div className="eyebrow">
          <Sparkles size={11} />
          <span>TripMate AI — A Multi-Agent Travel Planner with LangGraph</span>
        </div>

        <h1>
          Plan Your Perfect Trip <span>with AI</span>
        </h1>

        <p className="subtitle">
          Search flights, discover hotels, and generate a complete travel itinerary using a multi-agent<br className="desktop-break" />
          LangGraph system.
        </p>

        <form className="planner-card" onSubmit={handleGenerate}>
          <div className="planner-top">
            <div>
              <h2>Where do you want to go?</h2>
              <p>Plan your trip</p>
            </div>
            <div className={`online-pill ${loading ? "working" : ""}`}>
              <span className="online-dot" />
              {loading ? "Planning" : "API ready"}
            </div>
          </div>

          <div className="input-row">
            <div className="prompt-wrap">
              <textarea
                aria-label="Travel request"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                spellCheck="false"
              />
              <div className="mini-tools">
                <button title="Search"><Search size={15} /></button>
                <button title="Travel map"><MapPinned size={15} /></button>
              </div>
            </div>

            <button className="generate-btn" type="submit" disabled={loading}>
              <span>{loading ? "Building plan" : "Generate Plan"}</span>
              {loading ? <LoaderCircle className="spin" size={17} /> : <Send size={15} />}
            </button>
          </div>

          <div className="chips">
            {chips.map((chip) => (
              <button
                key={chip.label}
                className={`chip ${active === chip.label ? "active" : ""}`}
                onClick={() => selectChip(chip.label)}
              >
                {chip.icon}
                {chip.label}
              </button>
            ))}
          </div>
          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </form>

        {result && (
          <section className="results-panel" aria-live="polite">
            <div className="results-heading">
              <div>
                <span className="results-kicker">Your TripMate brief</span>
                <h2>Plan generated</h2>
              </div>
              <span className="call-count">{result.llm_calls} agent calls</span>
            </div>
            <article className="answer-block">
              <pre>{result.answer}</pre>
            </article>
            <div className="result-grid">
              <article className="result-card"><h3>Flights</h3><pre>{result.flight_results || "No flight details returned."}</pre></article>
              <article className="result-card"><h3>Hotels</h3><pre>{result.hotel_results || "No hotel details returned."}</pre></article>
              <article className="result-card"><h3>Itinerary</h3><pre>{result.itinerary || "No itinerary returned."}</pre></article>
            </div>
          </section>
        )}

        <div className="tech-line">
          <span>Built with FastAPI, LangGraph, Groq, PostgreSQL, Tavily and AviationStack</span>
        </div>
      </section>

      <div className="bottom-fade" />
    </main>
  );
}

export default App;