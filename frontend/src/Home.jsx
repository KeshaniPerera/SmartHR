import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div>
      <h1>SmartHR Dashboard</h1>
      <p>Select a tool to continue:</p>

      <div className="grid">
        <Link to="/policy-chat" className="card">
          <h3>Policy Chat</h3>
          <p>Ask policy questions and get instant answers.</p>
        </Link>

        <Link to="/prehire" className="card">
          <h3>Pre-Hire Attrition Prediction</h3>
          <p>Enter candidate details and predict attrition risk.</p>
        </Link>
      </div>
    </div>
  );
}
