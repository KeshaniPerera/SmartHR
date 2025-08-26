import { NavLink, Routes, Route } from "react-router-dom";
import Home from  "./home.jsx";
import PolicyChat from "./PolicyChat.jsx";
import PrehireForm from "./PrehireForm.jsx";
import TurnoverRank from "./TurnOverRank.jsx";
import NotFound from "./NotFound.jsx";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">SmartHR</div>
        <nav className="nav">
          <NavLink to="/" end className="navlink">Home</NavLink>
          <NavLink to="/policy-chat" className="navlink">Policy Chat</NavLink>
          <NavLink to="/prehire" className="navlink">Pre-Hire Prediction</NavLink>
          <NavLink to="/turnover" className="navlink">Turnover Risk</NavLink>

        </nav>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/policy-chat" element={<PolicyChat />} />
          <Route path="/prehire" element={<PrehireForm />} />
            <Route path="/turnover" element={<TurnoverRank />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">© {new Date().getFullYear()} SmartHR</footer>
    </div>
  );
}
