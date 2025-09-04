import { Link } from "react-router-dom";
import RoleGate from "./RoleGate";

export default function DashboardHome() {
  return (
    <>
      {/* Heading (page-level, below the persistent top bar) */}
      <section className="dash-head">
        <h1 className="font-bold text-2xl">Dashboard</h1>
        <p className="dash-subtitle">Choose a tool to continue</p>
      </section>

      {/* Cards */}
      <section className="grid-cards gap-5">
        {/* visible to everyone */}
        <Link to="policy-chat" className="card">
          <div className="card-accent" />
          <h3 className="font-semibold text-lg">Policy Chat</h3>
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
