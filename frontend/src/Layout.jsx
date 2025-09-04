import { useEffect, useState } from "react";
import { Outlet, useNavigate, Link } from "react-router-dom";
import api from "./api";
// If your logo lives in src/assets, uncomment the next line and use `src={logo}` below
// import logo from "./assets/smarthr-logo.svg";

export default function Layout() {
  const [user, setUser] = useState(() =>
    JSON.parse(localStorage.getItem("user") || "{}")
  );
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/auth/me")
      .then(({ data }) => {
        if (data?.user) {
          setUser(data.user);
          localStorage.setItem("user", JSON.stringify(data.user));
        }
      })
      .catch(() => {
        navigate("/login", { replace: true });
      });
  }, [navigate]);

  const logout = async () => {
    await api.post("/auth/logout");
    localStorage.removeItem("user");
    navigate("/login", { replace: true });
  };

  const role = user?.account_type || "employee";

  return (
    <div className="dash">
      {/* Top bar (persists across all nested pages) */}
      <header className="dash-topbar">
        {/* Brand logo linking to dashboard */}
        <Link to="/" className="dash-brand" aria-label="Go to SmartHR dashboard">
          {/* If your logo is in /public, use the next line: */}
          <img src="/logo.png" alt="SmartHR" className="dash-logo-img" />
          {/* If you imported from src/assets, use: <img src={logo} alt="SmartHR" className="dash-logo-img" /> */}
        </Link>

        <div className="dash-user">
          <span className={`dash-badge ${role === "hr" ? "hr" : "emp"}`}>{role}</span>
          <span className="dash-empid">{user?.emp_id}</span>
          <button onClick={logout} className="dash-btn dash-btn-logout">Logout</button>
        </div>
      </header>

      {/* Child routes render here */}
      <Outlet />
    </div>
  );
}
