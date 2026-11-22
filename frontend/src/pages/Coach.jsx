import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useConfig } from "../context.jsx";

const SUGGESTIONS = ["What should I eat for dinner?", "How much protein do I need?", "How am I doing today?", "Explain my calorie target"];

export default function Coach() {
  const cfg = useConfig();
  const [msgs, setMsgs] = useState([{ role: "model", text: "Hi! I'm your AI nutrition coach. I know your profile, targets and what you've eaten today. Ask me anything." }]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [source, setSource] = useState("");
  const end = useRef();
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const send = async (text) => {
    if (!text.trim() || busy) return;
    const history = msgs.slice(1).map(({ role, text }) => ({ role, text }));
    setMsgs((m) => [...m, { role: "user", text }]); setInput(""); setBusy(true);
    try {
      const r = await api.post("/chat", { message: text, history });
      setMsgs((m) => [...m, { role: "model", text: r.reply }]); setSource(r.source);
    } catch (e) { setMsgs((m) => [...m, { role: "model", text: `⚠ ${e.message}` }]); } finally { setBusy(false); }
  };

  return (
    <>
      <div className="row-between">
        <h2>AI Nutrition Coach</h2>
        <span className="pill">{source || cfg.ai_provider || "offline-coach"}</span>
      </div>
      <div className="card chat">
        <div className="msgs">
          {msgs.map((m, i) => <div key={i} className={`msg ${m.role}`}>{m.text.split("\n").map((l, j) => <p key={j}>{l.replace(/^_|_$/g, "")}</p>)}</div>)}
          {busy && <div className="msg model"><p>Thinking…</p></div>}
          <div ref={end} />
        </div>
        <div className="chips">{SUGGESTIONS.map((s) => <button key={s} className="chip" onClick={() => send(s)}>{s}</button>)}</div>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about meals, macros, goals…" />
          <button className="btn" disabled={busy}>Send</button>
        </form>
      </div>
    </>
  );
}
