import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import ReportCard from "../components/ReportCard.jsx";
import { getPatientDashboard } from "../api/api.js";

function Dashboard() {
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getPatientDashboard().then((res) => setData(res.data)).catch((err) => setError(err.response?.data?.detail || "Failed to load dashboard"));
  }, []);

  return (
    <><Navbar /><main className="container">
      <section className="hero-section">
        <div><h1>Welcome, {user.name}</h1><p>Track MRI uploads from prediction through doctor review and follow-up.</p></div>
        <Link className="hero-action" to="/predict">Upload MRI Scan</Link>
      </section>
      {error && <p className="error">{error}</p>}
      {data && <>
        <section className="dashboard-grid">
          <div className="stat-card"><span>Total Reports</span><strong>{data.total_reports}</strong></div>
          <div className="stat-card"><span>Pending Reviews</span><strong>{data.pending_reviews}</strong></div>
          <div className="stat-card"><span>Completed Reviews</span><strong>{data.completed_reviews}</strong></div>
          <div className="stat-card"><span>Unread Notifications</span><strong>{data.unread_notifications}</strong></div>
        </section>
        {data.latest_prediction && <section className="single-report dashboard-section">
          <div className="section-heading"><div><h2>Latest Prediction</h2><p className="muted">Your most recent MRI result and review status.</p></div><Link className="small-btn" to={`/report/${data.latest_prediction.id}`}>View</Link></div>
          <div className="result-grid">
            <div><span>Class</span><strong>{data.latest_prediction.predicted_class}</strong></div>
            <div><span>Confidence</span><strong>{data.latest_prediction.confidence}%</strong></div>
            <div><span>Review</span><strong>{data.latest_prediction.review_status.replaceAll("_", " ")}</strong></div>
          </div>
          <p><strong>Doctor remarks:</strong> {data.latest_prediction.doctor_remarks || "Waiting for doctor review."}</p>
        </section>}
        <section className="dashboard-section">
          <div className="section-heading"><h2>Recent MRI Timeline</h2><Link to="/history">Search all reports</Link></div>
          <div className="history-list">{data.recent_reports.length ? data.recent_reports.map((report) => <ReportCard key={report.id} report={report} />) : <div className="empty-panel">No reports yet.</div>}</div>
        </section>
      </>}
    </main></>
  );
}

export default Dashboard;
