import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import { getPrediction, fetchProtectedBlob, downloadProtected } from "../api/api.js";

function Report() {
  const { reportId } = useParams();
  const [report, setReport] = useState(null);
  const [imageUrl, setImageUrl] = useState("");
  const [heatmapUrl, setHeatmapUrl] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const urls = [];
    (async () => {
      try {
        const response = await getPrediction(reportId);
        if (!mounted) return;
        setReport(response.data);
        if (response.data.has_image) {
          const url = await fetchProtectedBlob(`/prediction/${reportId}/image`);
          urls.push(url); if (mounted) setImageUrl(url);
        }
        if (response.data.has_heatmap) {
          const url = await fetchProtectedBlob(`/prediction/${reportId}/heatmap`);
          urls.push(url); if (mounted) setHeatmapUrl(url);
        }
      } catch (err) { if (mounted) setError(err.response?.data?.detail || "Failed to load report"); }
    })();
    return () => { mounted = false; urls.forEach((url) => URL.revokeObjectURL(url)); };
  }, [reportId]);

  const download = () => downloadProtected(`/report/${reportId}/download`, `brain_tumor_report_${reportId}.pdf`).catch(() => setError("Report download failed"));

  return <><Navbar /><main className="container"><h1>Brain Tumor Report</h1>{error && <p className="error">{error}</p>}
    {report && <section className="single-report print-area">
      <div className="report-header"><div><h2>{report.patient_name || "Patient"}</h2><p className="muted">Report #{report.id} • {new Date(report.created_at).toLocaleString()}</p></div><div className="action-row"><button onClick={download}>Download PDF</button><button className="secondary-btn" onClick={() => window.print()}>Print</button></div></div>
      <div className="result-grid">
        <div><span>Predicted Class</span><strong>{report.predicted_class}</strong></div>
        <div><span>Confidence</span><strong>{report.confidence}%</strong></div>
        <div><span>AI Status</span><strong>{report.status}</strong></div>
        <div><span>Review Status</span><strong>{report.review_status.replaceAll("_", " ")}</strong></div>
        <div><span>Risk Level</span><strong>{report.risk_level.replaceAll("_", " ")}</strong></div>
        <div><span>Assigned Doctor</span><strong>{report.assigned_doctor_name || "Not assigned"}</strong></div>
      </div>
      <div className="scan-grid">
        {imageUrl && <figure><img src={imageUrl} alt="Uploaded MRI" /><figcaption>Uploaded MRI scan</figcaption></figure>}
        {heatmapUrl && <figure><img src={heatmapUrl} alt="Grad-CAM heatmap" /><figcaption>Grad-CAM explainability visualization</figcaption></figure>}
      </div>
      <div className="remarks-box"><h3>Explainable AI Summary</h3><p>{report.explanation || "No AI explanation available."}</p></div>
      <div className="remarks-box"><h3>Doctor Remarks</h3><p>{report.doctor_remarks || "No remarks added yet."}</p></div>
      <div className="remarks-box"><h3>Recommendation and Follow-up</h3><p>{report.recommendation || "No recommendation added yet."}</p><p><strong>Follow-up date:</strong> {report.follow_up_date || "Not specified"}</p></div>
      <p className="warning">This AI result is not a final medical diagnosis. A qualified doctor or radiologist must review the original MRI and clinical findings.</p>
    </section>}
  </main></>;
}

export default Report;
