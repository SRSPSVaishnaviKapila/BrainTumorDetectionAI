import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import { getDoctorDashboard, getDoctorReports, getDoctorPatients, reviewDoctorReport, comparePatientReports, downloadProtected } from "../api/api.js";

function DoctorDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [reports, setReports] = useState([]);
  const [patients, setPatients] = useState([]);
  const [filters, setFilters] = useState({ search: "", review_status: "", risk_level: "" });
  const [drafts, setDrafts] = useState({});
  const [comparison, setComparison] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
      const [dashRes, reportRes, patientRes] = await Promise.all([getDoctorDashboard(), getDoctorReports(params), getDoctorPatients()]);
      setDashboard(dashRes.data); setReports(reportRes.data); setPatients(patientRes.data);
      const next = {};
      reportRes.data.forEach((r) => { next[r.id] = { remarks: r.doctor_remarks || "", recommendation: r.recommendation || "", follow_up_date: r.follow_up_date || "", review_status: r.review_status === "completed" ? "completed" : "under_review" }; });
      setDrafts(next);
    } catch (err) { setError(err.response?.data?.detail || "Failed to load doctor dashboard"); }
  };
  useEffect(() => { load(); }, []);

  const save = async (reportId) => {
    setMessage(""); setError("");
    try { const res = await reviewDoctorReport(reportId, drafts[reportId]); setMessage(res.data.message); load(); }
    catch (err) { setError(err.response?.data?.detail || "Review update failed"); }
  };
  const updateDraft = (id, field, value) => setDrafts({ ...drafts, [id]: { ...drafts[id], [field]: value } });
  const compare = async (patientId) => {
    try { const res = await comparePatientReports(patientId); setComparison(res.data); }
    catch (err) { setError(err.response?.data?.detail || "Comparison failed"); }
  };

  return <><Navbar /><main className="container"><div className="section-heading"><div><h1>Doctor Dashboard</h1><p className="muted">Manage assigned patients, review MRI reports, and recommend follow-up.</p></div></div>
    {error && <p className="error">{error}</p>}{message && <p className="success">{message}</p>}
    {dashboard && <section className="dashboard-grid five-grid">
      <div className="stat-card"><span>Total Patients</span><strong>{dashboard.total_patients}</strong></div>
      <div className="stat-card"><span>Total Reports</span><strong>{dashboard.total_reports}</strong></div>
      <div className="stat-card"><span>Pending</span><strong>{dashboard.pending_reviews}</strong></div>
      <div className="stat-card"><span>Completed</span><strong>{dashboard.completed_reviews}</strong></div>
      <div className="stat-card"><span>High-Risk</span><strong>{dashboard.high_risk_cases}</strong></div>
    </section>}

    <section className="dashboard-section"><h2>Assigned Patients</h2><div className="patient-chip-list">{patients.map((p) => <button className="patient-chip" key={p.id} onClick={() => compare(p.id)}>{p.name}<small>{p.report_count} reports</small></button>)}</div>
      {comparison && <div className="comparison-box"><div className="section-heading"><h3>{comparison.patient_name} — Report Comparison</h3><button className="secondary-btn" onClick={() => setComparison(null)}>Close</button></div>{comparison.patient && <p className="muted">{comparison.patient.email} • Age: {comparison.patient.age || "N/A"} • Gender: {comparison.patient.gender || "N/A"} • Phone: {comparison.patient.phone || "N/A"}</p>}<p>{comparison.trend}</p><div className="timeline">{comparison.reports.map((r) => <div key={r.id}><strong>{r.predicted_class}</strong><span>{r.confidence}%</span><small>{new Date(r.created_at).toLocaleDateString()}</small></div>)}</div></div>}
    </section>

    <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); load(); }}>
      <input placeholder="Search patient or class" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
      <select value={filters.review_status} onChange={(e) => setFilters({ ...filters, review_status: e.target.value })}><option value="">All review states</option><option value="pending_review">Pending</option><option value="needs_attention">Needs Attention</option><option value="under_review">Under Review</option><option value="completed">Completed</option></select>
      <select value={filters.risk_level} onChange={(e) => setFilters({ ...filters, risk_level: e.target.value })}><option value="">All risk levels</option><option value="high">High</option><option value="moderate">Moderate</option><option value="low">Low</option><option value="review_required">Review Required</option></select>
      <button>Search</button>
    </form>

    <section className="review-list">{reports.length ? reports.map((report) => <article className="review-card" key={report.id}>
      <div className="review-summary"><div className="inline-heading"><h3>{report.patient_name}</h3><span className={`badge ${report.review_status}`}>{report.review_status.replaceAll("_", " ")}</span></div>
        <p className="capitalize"><strong>{report.predicted_class}</strong> • {report.confidence}% • Risk: {report.risk_level.replaceAll("_", " ")}</p><small>{new Date(report.created_at).toLocaleString()}</small>
        <div className="action-row"><Link className="small-btn" to={`/report/${report.id}`}>View MRI & Report</Link><button className="secondary-btn" onClick={() => downloadProtected(`/report/${report.id}/download`, `patient_report_${report.id}.pdf`)}>Download</button></div>
      </div>
      <div className="review-form">
        <textarea placeholder="Diagnosis / clinical remarks" value={drafts[report.id]?.remarks || ""} onChange={(e) => updateDraft(report.id, "remarks", e.target.value)} />
        <textarea placeholder="Recommendation" value={drafts[report.id]?.recommendation || ""} onChange={(e) => updateDraft(report.id, "recommendation", e.target.value)} />
        <div className="two-column"><label>Follow-up date<input type="date" value={drafts[report.id]?.follow_up_date || ""} onChange={(e) => updateDraft(report.id, "follow_up_date", e.target.value)} /></label><label>Review status<select value={drafts[report.id]?.review_status || "under_review"} onChange={(e) => updateDraft(report.id, "review_status", e.target.value)}><option value="under_review">Under Review</option><option value="completed">Completed</option></select></label></div>
        <button onClick={() => save(report.id)}>Save Review</button>
      </div>
    </article>) : <div className="empty-panel">No assigned reports match the filters.</div>}</section>
  </main></>;
}

export default DoctorDashboard;
