import { useState } from "react";

export default function PolicyChat() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState(null);
  const [error, setError] = useState("");

  async function ask(e) {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true); setResp(null); setError("");
    try {
      const r = await fetch("/api/nlp/policy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ q })
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.error || "Request failed");
      setResp(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{maxWidth: 720, margin: "32px auto", padding: 16}}>
      <h2 style={{marginBottom: 12}}>Ask HR Policies</h2>
      <form onSubmit={ask} style={{display: "flex", gap: 8}}>
        <input
          style={{flex: 1, padding: 10, border: "1px solid #ccc", borderRadius: 8}}
          placeholder="e.g., What are the company leave policies?"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          style={{padding: "10px 16px", borderRadius: 8}}
          disabled={loading || !q.trim()}
        >
          {loading ? "Searching..." : "Ask"}
        </button>
      </form>

      {error && <p style={{color: "crimson", marginTop: 12}}>{error}</p>}

      {resp && (
        <div style={{marginTop: 16, padding: 12, border: "1px solid #eee", borderRadius: 8}}>
          <div style={{fontSize: 12, color: "#666"}}>
            Match: <b>{resp.title}</b> ({resp.method}, confidence {resp.confidence})
          </div>
          <p style={{whiteSpace: "pre-wrap", marginTop: 8}}>
            {resp.policy_description}
          </p>
        </div>
      )}
    </div>
  );
}
