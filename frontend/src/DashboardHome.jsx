// src/DashboardHome.jsx
import { Link } from "react-router-dom";
import RoleGate from "./RoleGate";

export default function DashboardHome() {
  return (
    <>
      {/* Heading with bell on the right */}
      <section className="dash-head flex items-center justify-between">
        <div>
          <h1 className="font-bold text-2xl">Dashboard</h1>
          <p className="dash-subtitle">Choose a tool to continue</p>
        </div>

        {/* Bell icon -> Notifications */}
        <Link
          to="notifications"
          className="p-2 rounded-full hover:bg-gray-100"
          aria-label="Notifications"
          title="Notifications"
        >
          <span role="img" aria-hidden="true" className="text-xl">
            🔔
          </span>
        </Link>
      </section>

      {/* Cards */}
      <section className="grid-cards gap-5">
        {/* visible to everyone */}
        <Link to="policy-chat" className="card">
          <div className="card-accent" />
          <h3 className="font-semibold text-lg">Chat Bot</h3>
          <p>Ask policy questions and get instant answers.</p>
        </Link>

        <Link to="attendance" className="card">
          <div className="card-accent" />
          <h3 className="font-semibold text-lg">Attendance</h3>
          <p>Mark attendance or view today’s status.</p>
        </Link>

        {/* HR-only */}
        <RoleGate allow={["hr"]}>
          <Link to="prehire" className="card">
            <div className="card-accent" />
            <h3 className="font-semibold text-lg">Pre-Hire Attrition Prediction</h3>
            <p>Enter candidate details and predict attrition risk.</p>
          </Link>
        </RoleGate>

        <RoleGate allow={["hr"]}>
          <Link to="turnover" className="card">
            <div className="card-accent" />
            <h3 className="font-semibold text-lg">Turnover Risk</h3>
            <p>Rank employees by predicted turnover risk.</p>
          </Link>
        </RoleGate>

        <RoleGate allow={["hr"]}>
          <Link to="performance" className="card">
            <div className="card-accent" />
            <h3 className="font-semibold text-lg">Performance</h3>
            <p>Identify likely high performers for leadership & mentorship.</p>
          </Link>
        </RoleGate>
      </section>
    </>
  );
}
