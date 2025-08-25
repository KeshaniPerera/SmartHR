import { useState } from "react";

export default function PolicyChat() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState("");
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState("");

  async function ask(e) {
    e?.preventDefault?.();
    if (!q.trim()) return;
    setLoading(true); setError(""); setAnswer(""); setMeta(null);

    try {
      const r = await fetch("/api/nlp/query", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ q })
      });

      const ct = r.headers.get("content-type") || "";
      const data = ct.includes("application/json") ? await r.json() : { error: await r.text() };

      if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);

      // unified endpoint returns: { text, meta? }
      setAnswer(data.text || "");
      setMeta(data.meta || null);
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{maxWidth: 720, margin: "32px auto", padding: 16}}>
      <h2 style={{marginBottom: 8}}>Ask HR</h2>

      <form onSubmit={ask} style={{display: "flex", gap: 8}}>
        <input
          style={{flex: 1, padding: 10, border: "1px solid #ccc", borderRadius: 8}}
          placeholder="e.g., Hi I am Bob, how many leaves do I have left?"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          style={{padding: "10px 16px", borderRadius: 8}}
          disabled={loading || !q.trim()}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {/* quick examples (optional) */}
      <div style={{marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap"}}>
        {[
          "Any policies in leaving the company?",
          "How many policies do we have?",
          "List policies under workplace rules",
          "Hi I am Bob, how many leaves do I have left?",
          "What is my last leave request status?"
        ].map((ex) => (
          <button
            key={ex}
            onClick={() => { setQ(ex); }}
            style={{fontSize: 12, padding: "6px 10px", borderRadius: 999, border: "1px solid #ddd", background: "#f8f8f8"}}
          >
            {ex}
          </button>
        ))}
      </div>

      {error && <p style={{color: "crimson", marginTop: 12}}>{error}</p>}

      {answer && (
        <div style={{marginTop: 16, padding: 12, border: "1px solid #eee", borderRadius: 8, whiteSpace: "pre-wrap"}}>
          {answer}
          {/* optional: show source/meta if present */}
          {meta?.policy?.title && (
            <div style={{marginTop: 8, fontSize: 12, color: "#666"}}>
              Source: <b>{meta.policy.title}</b>
            </div>
          )}
          {Array.isArray(meta?.items) && meta.items.length > 0 && (
            <div style={{marginTop: 8}}>
              <div style={{fontSize: 12, color: "#666", marginBottom: 4}}>Items:</div>
              <ul style={{margin: 0, paddingLeft: 18}}>
                {meta.items.map((it) => (
                  <li key={it.slug || it.title}>{it.title}{it.slug ? ` (${it.slug})` : ""}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
