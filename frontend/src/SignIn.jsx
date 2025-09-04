// src/SignIn.jsx
import { useState } from "react";
import api from "./api";

export default function SignIn() {
  const [empId, setEmpId] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const { data } = await api.post("/auth/login", { emp_id: empId, password });
      localStorage.setItem("user", JSON.stringify(data.user)); // light cache
      window.location.href = "/"; // dashboard (Home)
    } catch (e) {
      setErr(e?.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 border rounded-xl p-6 shadow">
        <h1 className="text-2xl font-semibold">SmartHR Login</h1>
        <label className="block text-sm">Employee ID</label>
        <input className="w-full border rounded p-2" value={empId} onChange={e=>setEmpId(e.target.value)} />
        <label className="block text-sm">Password</label>
        <input className="w-full border rounded p-2" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        {err && <p className="text-red-600 text-sm">{err}</p>}
        <button className="w-full rounded p-2 border">Sign In</button>
      </form>
    </div>
  );
}
