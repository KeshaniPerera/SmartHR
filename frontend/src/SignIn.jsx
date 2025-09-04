// src/SignIn.jsx
import { useEffect, useState } from "react";
import api from "./api";

const Eye = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);
const EyeOff = (props) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" {...props}>
    <path d="M3 3l18 18M10.6 10.6a3 3 0 104.2 4.2M9.88 4.26A9.93 9.93 0 0112 4c7 0 11 8 11 8a18.2 18.2 0 01-4.06 5.14M6.6 6.6C3.6 8.33 1 12 1 12a18.25 18.25 0 005.12 5.22" />
  </svg>
);

export default function SignIn() {
  const [empId, setEmpId] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  useEffect(() => {
    const prev = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    return () => { document.documentElement.style.overflow = prev; };
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", {
        emp_id: empId.trim(),
        password,
      });
      localStorage.setItem("user", JSON.stringify(data.user));
      window.location.href = "/";
    } catch (e) {
      setErr(e?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
  <div className="h-dvh overflow-hidden bg-white">
    <div className="grid md:grid-cols-2 h-full w-full m-0">
      {/* Left: green panel with content */}
      <div className="h-full bg-[var(--brand-50)] flex flex-col justify-center px-6 sm:px-12 ">
        <div className="max-w-sm w-full mx-auto">
          {/* centered brand + headings */}
          <div className="mb-6 flex flex-col items-center text-center">
            <img src="/logo.png" alt="SmartHR" className="h-14 sm:h-16 object-contain" />
            <h1 className="mt-4 text-3xl font-semibold tracking-tight">SIGN IN</h1>
            <p className="mt-1 text-sm text-[var(--muted)]">Welcome back</p>
          </div>

          <form onSubmit={submit} className="mt-4 space-y-4">
            <div>
              <label className="label">Employee ID</label>
              <input
                className="input"
                placeholder="E001"
                value={empId}
                autoComplete="username"
                onChange={(e) => setEmpId(e.target.value)}
              />
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  className="input pr-12"
                  type={showPw ? "text" : "password"}
                  value={password}
                  autoComplete="current-password"
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 p-2 rounded-md text-slate-500 hover:bg-slate-100"
                >
                  {showPw ? <EyeOff /> : <Eye />}
                </button>
              </div>
            </div>

            {err && <div className="error">{err}</div>}

            <button className="btn btn-primary w-full rounded-full h-11" disabled={loading || !empId || !password}>
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>
        </div>
      </div>

      {/* Right: full-bleed hero image */}
      <div className="hidden md:block relative">
        <img src="/auth-hero.jpg" alt="" className="absolute inset-0 w-full h-full object-cover" />
        <div className="relative h-full w-full p-10 flex items-center">
          <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-6 max-w-xs ml-auto shadow-[0_10px_30px_-10px_rgba(0,0,0,.15)]">
            <div className="text-sm tracking-wide text-[var(--muted)] mb-2">SMART • HR</div>
            <p className="text-2xl leading-snug font-semibold text-slate-800">
              A Reliable Solution For <span className="text-[var(--brand-700)]">HR services</span>
            </p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Predictive Analytics, Natural Communication, Company Insights and More
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
);

}
