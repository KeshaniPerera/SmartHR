import { useState } from "react";
const apiBase = import.meta.env.VITE_API_BASE || "";

const initial = {
  // NEW meta fields
  CandidateID: "",
  CandidateName: "",

  // existing features
  Age: 28,
  Gender: "Female",
  BusinessTravel: "Travel_Rarely",
  Department: "Research & Development",
  Education: 3,
  EducationField: "Life Sciences",
  JobRole: "Research Scientist",
  MaritalStatus: "Single",
  DistanceFromHome: 12,
  TotalWorkingYears: 5,
  NumCompaniesWorked: 2,
  StockOptionLevel: 1,
  TrainingTimesLastYear: 3,
};

export default function PrehireForm() {
  const [form, setForm] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [errors, setErrors] = useState(null);

  const asNumber = (k, v) =>
    ["Age","Education","DistanceFromHome","TotalWorkingYears","NumCompaniesWorked","StockOptionLevel","TrainingTimesLastYear"].includes(k)
      ? Number(v)
      : v;

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: asNumber(name, value) }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(""); setErrors(null); setResult(null);
    try {
      const res = await fetch(`${apiBase}/api/prehire/predict/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { setErrors(data?.errors || { _: "Validation failed" }); return; }
      setResult(data);
    } catch (err) {
      setError(err?.message || "Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Pre-Hire Attrition Prediction</h1>

      <form className="form" onSubmit={submit}>
        <div className="grid2">
          {/* NEW: candidate meta */}
          <label>Candidate ID
            <input name="CandidateID" value={form.CandidateID} onChange={onChange} placeholder="CND-001" required />
          </label>
          <label>Candidate Name
            <input name="CandidateName" value={form.CandidateName} onChange={onChange} placeholder="Jane Doe" required />
          </label>

          {/* existing fields below */}
          <label>Age
            <input type="number" name="Age" value={form.Age} onChange={onChange} min={16} max={80} required />
          </label>
          <label>Gender
            <select name="Gender" value={form.Gender} onChange={onChange}>
              <option>Female</option><option>Male</option>
            </select>
          </label>
          <label>Business Travel
            <select name="BusinessTravel" value={form.BusinessTravel} onChange={onChange}>
              <option>Travel_Rarely</option>
              <option>Travel_Frequently</option>
              <option>Non-Travel</option>
            </select>
          </label>
          <label>Department
            <select name="Department" value={form.Department} onChange={onChange}>
              <option>Sales</option>
              <option>Research & Development</option>
              <option>Human Resources</option>
            </select>
          </label>
          <label>Education (1–5)
            <input type="number" name="Education" value={form.Education} onChange={onChange} min={1} max={5} required />
          </label>
          <label>Education Field
            <select name="EducationField" value={form.EducationField} onChange={onChange}>
              <option>Life Sciences</option><option>Medical</option><option>Marketing</option>
              <option>Technical Degree</option><option>Human Resources</option><option>Other</option>
            </select>
          </label>
          <label>Job Role
            <select name="JobRole" value={form.JobRole} onChange={onChange}>
              <option>Sales Executive</option><option>Research Scientist</option>
              <option>Laboratory Technician</option><option>Manufacturing Director</option>
              <option>Healthcare Representative</option><option>Manager</option>
              <option>Sales Representative</option><option>Research Director</option>
              <option>Human Resources</option>
            </select>
          </label>
          <label>Marital Status
            <select name="MaritalStatus" value={form.MaritalStatus} onChange={onChange}>
              <option>Single</option><option>Married</option><option>Divorced</option>
            </select>
          </label>
          <label>Distance From Home (km)
            <input type="number" name="DistanceFromHome" value={form.DistanceFromHome} onChange={onChange} min={0} max={100} />
          </label>
          <label>Total Working Years
            <input type="number" name="TotalWorkingYears" value={form.TotalWorkingYears} onChange={onChange} min={0} max={60} />
          </label>
          <label>Num Companies Worked
            <input type="number" name="NumCompaniesWorked" value={form.NumCompaniesWorked} onChange={onChange} min={0} max={20} />
          </label>
          <label>Stock Option Level (0–3)
            <input type="number" name="StockOptionLevel" value={form.StockOptionLevel} onChange={onChange} min={0} max={3} />
          </label>
          <label>Training Times Last Year
            <input type="number" name="TrainingTimesLastYear" value={form.TrainingTimesLastYear} onChange={onChange} min={0} max={20} />
          </label>
        </div>

        <button className="btn" disabled={loading}>
          {loading ? "Predicting..." : "Predict & Save"}
        </button>
      </form>

      {errors && (<div className="error"><h3>Validation Errors</h3><pre>{JSON.stringify(errors, null, 2)}</pre></div>)}
      {error && <div className="error">{error}</div>}

      {result && (
        <div className="panel">
          <h2>Result</h2>
          <p><b>Candidate:</b> {result.candidate_name} ({result.candidate_id})</p>
          <p><b>Risk:</b> {result.risk_flag}</p>
          <p><b>Probability:</b> {(result.probability * 100).toFixed(2)}%</p>
          <p><b>Model:</b> {result.model_version}</p>
          <p><b>Saved:</b> {String(result.saved)} {result.id ? `(id: ${result.id})` : ""}</p>
        </div>
      )}
    </div>
  );
}
