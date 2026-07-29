import { Link } from "react-router-dom";

function ReportCard({ report }) {
  return (
    <article className="report-card">
      <div>
        <div className="inline-heading">
          <h3>{report.patient_name || "Patient"}</h3>
          <span className={`badge ${report.review_status}`}>{report.review_status?.replaceAll("_", " ")}</span>
        </div>
        <p className="capitalize">{report.predicted_class} • {report.confidence}% • {report.status}</p>
        <small>{new Date(report.created_at).toLocaleString()} {report.assigned_doctor_name ? `• ${report.assigned_doctor_name}` : ""}</small>
      </div>
      <Link to={`/report/${report.id}`} className="small-btn">Open Report</Link>
    </article>
  );
}

export default ReportCard;
