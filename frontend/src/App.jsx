import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import SignIn from "./SignIn";

import Home from "./Home";
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
      <header className="topbar">
        <div className="brand">SmartHR</div>
        <nav className="nav">

        </nav>
      </header>

      <main className="container">
        <Routes>
           <Route path="/login" element={<SignIn />} />

        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/policy-chat" element={<ProtectedRoute><PolicyChat /></ProtectedRoute>} />
        <Route path="/attendance" element={<ProtectedRoute><AttendanceScan /></ProtectedRoute>} />
        <Route path="/prehire" element={<ProtectedRoute><PrehireForm /></ProtectedRoute>} />
        <Route path="/turnover" element={<ProtectedRoute><TurnoverRank /></ProtectedRoute>} />
        <Route path="/performance" element={<ProtectedRoute><PerformanceRank /></ProtectedRoute>} />

        <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">© {new Date().getFullYear()} SmartHR</footer>
    </div>
  );
}
