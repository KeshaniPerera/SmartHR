// src/App.jsx
import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import Layout from "./Layout";

import SignIn from "./SignIn";
import Home from "./DashboardHome";        // dashboard body (no header)
import PolicyChat from "./PolicyChat";
import PrehireForm from "./PrehireForm";
import TurnoverRank from "./TurnoverRank";
import PerformanceRank from "./PerformanceRank";
import AttendanceScan from "./AttendanceScan";
import NotFound from "./NotFound";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <main className="container">
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<SignIn />} />

          {/* Protected layout with persistent SmartHR header */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Index dashboard (under the persistent header) */}
            <Route index element={<Home />} />

            {/* Nested feature routes (render inside Layout) */}
            <Route path="policy-chat" element={<PolicyChat />} />
            <Route path="attendance" element={<AttendanceScan />} />
            <Route path="prehire" element={<PrehireForm />} />
            <Route path="turnover" element={<TurnoverRank />} />
            <Route path="performance" element={<PerformanceRank />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      <footer className="footer">© {new Date().getFullYear()} SmartHR</footer>
    </div>
  );
}
