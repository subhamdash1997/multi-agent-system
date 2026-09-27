import React, { useState } from "react";
import { MapPinned, Plane, Sparkles, Search, Send, Globe2 } from "lucide-react";
import "./styles.css";

const examples = [
  "Plan a complete 7 days Japan trip from India under 2 lakhs...",
  "Plan a 5 day Dubai trip including flights, hotels and sightseeing...",
  "Plan a Thailand vacation with flights, hotels and activities...",
  "Find global flight options and build a complete itinerary..."
];

function App() {
  const [prompt, setPrompt] = useState(examples[0]);
  const [active, setActive] = useState("Japan Trip");
  const [generated, setGenerated] = useState(false);

  const chips = [
    { label: "Japan Trip", icon: <MapPinned size={12} /> },
    { label: "Dubai Trip", icon: <Globe2 size={12} /> },
    { label: "Thailand Trip", icon: <Plane size={12} /> },
    { label: "Global Flights", icon: <Search size={12} /> }
  ];

  const handleGenerate = () => {
    setGenerated(true);
    setTimeout(() => setGenerated(false), 1800);
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

        <div className="planner-card">
          <div className="planner-top">
            <div>
              <h2>Where do you want to go?</h2>
              <p>Example: Plan a complete 7 days Japan trip from India under 2 lakhs...</p>
            </div>
            <div className="online-pill">
              <span className="online-dot" />
              Online
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

            <button className={`generate-btn ${generated ? "success" : ""}`} onClick={handleGenerate}>
              <span>{generated ? "Plan Ready" : "Generate Plan"}</span>
              {generated ? <Sparkles size={17} /> : <Send size={15} />}
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
        </div>

        <div className="tech-line">
          <span>Built with FastAPI, LangGraph, Groq, PostgreSQL, Tavily and AviationStack</span>
        </div>
      </section>

      <div className="bottom-fade" />
    </main>
  );
}

export default App;