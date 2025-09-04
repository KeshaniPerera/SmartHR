// src/Home.jsx
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "./api";
import RoleGate from "./RoleGate";

export default function Home() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("user") || "{}"));

  useEffect(() => {
    api.get("/auth/me")
      .then(({data}) => { if (data?.user) { setUser(data.user); localStorage.setItem("user", JSON.stringify(data.user)); }})
      .catch(() => {});
  }, []);

  const logout = async () => {
    await api.post("/auth/logout");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between">
        <h1>SmartHR Dashboard</h1>
        <div className="text-sm">
          Signed in as <b>{user?.emp_id}</b> ({user?.account_type})
          <button onClick={logout} className="ml-3 border px-3 py-1 rounded">Logout</button>
        </div>
      </div>

      <p>Select a tool to continue:</p>

      <div className="grid" style={{display:"grid", gap:"12px", gridTemplateColumns:"repeat(auto-fit, minmax(220px, 1fr))"}}>
        {/* visible to everyone */}
        <Link to="/policy-chat" className="card">
          <h3>Policy Chat</h3>
          <p>Ask policy questions and get instant answers.</p>
        </Link>

        <Link to="/attendance" className="card">
          <h3>Attendance</h3>
          <p>Mark attendance or view today’s status.</p>
        </Link>

        {/* HR-only */}
        <RoleGate allow={["hr"]}>
          <Link to="/prehire" className="card">
            <h3>Pre-Hire Attrition Prediction</h3>
            <p>Enter candidate details and predict attrition risk.</p>
          </Link>
        </RoleGate>

        <RoleGate allow={["hr"]}>
          <Link to="/turnover" className="card">
            <h3>Turnover Risk</h3>
            <p>Rank employees by predicted turnover risk.</p>
          </Link>
        </RoleGate>

        <RoleGate allow={["hr"]}>
          <Link to="/performance" className="card">
            <h3>Performance</h3>
            <p>Identify likely high performers for leadership & mentorship.</p>
          </Link>
        </RoleGate>
      </div>
    </div>
  );
}
