import { Link } from "react-router-dom";

function ResultCard({ result }) {
  if (!result) return <div className="empty-panel">Your prediction result will appear here.</div>;
  return (
    <div className="result-card">
      <div className="inline-heading">
        <h2>Prediction Result</h2>
        <span className={`badge ${result.review_status}`}>{result.review_status?.replaceAll("_", " ")}</span>
      </div>
      <div className="result-grid">
        <div><span>Predicted Class</span><strong>{result.predicted_class}</strong></div>
        <div><span>Confidence</span><strong>{result.confidence}%</strong></div>
        <div><span>Risk</span><strong>{result.risk_level?.replaceAll("_", " ")}</strong></div>
      </div>
      <p>{result.explanation}</p>
      {result.mock_mode && <p className="warning"><strong>Demo mode:</strong> Add your trained model at <code>backend/model/brain_tumor_model.keras</code> before using predictions for evaluation.</p>}
      <Link to={`/report/${result.report_id}`} className="primary-link">View Full Report</Link>
    </div>
  );
}

export default ResultCard;
