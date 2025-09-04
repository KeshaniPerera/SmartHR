import { useEffect, useState } from "react";
const apiBase = import.meta.env.VITE_API_BASE || "";

export default function TurnoverRank() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchRank = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${apiBase}/api/turnover/rank/?limit=200`);
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Request failed");
      setRows(data.results || []);
    } catch (e) {
      setError(e.message || "Network error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRank(); }, []);

  return (
    <div>
      <h1>Turnover Risk (from “Employee Insights”)</h1>
      <div style={{display:"flex", gap:12, alignItems:"center", marginBottom:12}}>
        <button className="btn" onClick={fetchRank} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh Ranking"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="panel" style={{overflowX:"auto"}}>
        <table style={{width:"100%", borderCollapse:"collapse"}}>
          <thead>
            <tr>
              <th align="left">#</th>
              <th align="left">Employee</th>
              <th align="left">Department</th>
              <th align="left">Job Role</th>
              <th align="right">Probability</th>
              <th align="left">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.emp_id || i} style={{borderTop:"1px solid #eee"}}>
                <td>{i+1}</td>
              <td>
                <div style={{fontWeight:600}}>{r.emp_id || r.employee_id || "-"}</div>
                <div style={{fontSize:12, color:"#64748b", fontWeight:400}}>
                  {(r.full_name ?? r.fullName ?? r.name ?? "-") || "-"}
                </div>
              </td>

                <td>{r.department}</td>
                <td>{r.job_role}</td>
                <td align="right">
                  {typeof r.probability === "number" ? (r.probability*100).toFixed(2) : "—"}%
                </td>
                <td style={{color: r.risk_flag==="High" ? "#b00020" : "#065f46"}}>
                  {r.risk_flag}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
