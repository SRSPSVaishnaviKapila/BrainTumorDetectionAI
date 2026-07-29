import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import UploadBox from "../components/UploadBox.jsx";
import ResultCard from "../components/ResultCard.jsx";
import { predictTumor } from "../api/api.js";

function Predict() {
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const [file, setFile] = useState(null);
  const [patient, setPatient] = useState({
    patient_name: user.name || "",
    age: user.age || "",
    gender: user.gender || "",
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handlePatientChange = (e) => {
    setPatient({ ...patient, [e.target.name]: e.target.value });
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);

    if (!file) {
      setError("Please upload an MRI image.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("patient_name", patient.patient_name);
    if (patient.age) formData.append("age", patient.age);
    formData.append("gender", patient.gender);

    try {
      setLoading(true);
      const response = await predictTumor(formData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />

      <main className="container">
        <h1>MRI Brain Tumor Prediction</h1>

        <form onSubmit={handlePredict} className="predict-layout">
          <div className="form-panel">
            <h2>Patient Details</h2>

            {error && <p className="error">{error}</p>}

            <input
              name="patient_name"
              placeholder="Patient Name"
              value={patient.patient_name}
              onChange={handlePatientChange}
              required
            />

            <input
              type="number"
              name="age"
              placeholder="Age"
              value={patient.age}
              onChange={handlePatientChange}
            />

            <select
              name="gender"
              value={patient.gender}
              onChange={handlePatientChange}
            >
              <option value="">Select Gender</option>
              <option value="Female">Female</option>
              <option value="Male">Male</option>
              <option value="Other">Other</option>
            </select>

            <UploadBox file={file} setFile={setFile} />

            <button type="submit" disabled={loading}>
              {loading ? "Predicting..." : "Predict Tumor"}
            </button>
          </div>

          <ResultCard result={result} />
        </form>
      </main>
    </>
  );
}

export default Predict;
