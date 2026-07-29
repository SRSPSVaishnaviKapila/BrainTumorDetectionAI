import { useEffect, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import ReportCard from "../components/ReportCard.jsx";
import { getHistory } from "../api/api.js";

function History() {
  const [reports, setReports] = useState([]);
  const [filters, setFilters] = useState({ search: "", tumor_class: "", review_status: "", date_from: "", date_to: "" });
  const [error, setError] = useState("");
  const load = async () => {
    try { const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value)); const res = await getHistory(params); setReports(res.data); }
    catch (err) { setError(err.response?.data?.detail || "Failed to load history"); }
  };
  useEffect(() => { load(); }, []);
  const submit = (e) => { e.preventDefault(); load(); };
  return <><Navbar /><main className="container"><h1>Prediction Reports</h1>
    <form className="filter-bar" onSubmit={submit}>
      <input placeholder="Search patient or class" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
      <select value={filters.tumor_class} onChange={(e) => setFilters({ ...filters, tumor_class: e.target.value })}><option value="">All classes</option><option value="glioma">Glioma</option><option value="meningioma">Meningioma</option><option value="pituitary">Pituitary</option><option value="notumor">No Tumor</option></select>
      <select value={filters.review_status} onChange={(e) => setFilters({ ...filters, review_status: e.target.value })}><option value="">All review states</option><option value="pending_review">Pending</option><option value="needs_attention">Needs Attention</option><option value="under_review">Under Review</option><option value="completed">Completed</option></select>
      <input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
      <input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
      <button>Search</button>
    </form>
    {error && <p className="error">{error}</p>}
    <div className="history-list">{reports.length ? reports.map((report) => <ReportCard key={report.id} report={report} />) : <div className="empty-panel">No matching reports found.</div>}</div>
  </main></>;
}

export default History;
