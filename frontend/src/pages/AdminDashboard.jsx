import { useEffect, useRef, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import {
  getAdminDashboard, getAdminUsers, getAdminPredictions, createDoctor,
  updateAdminUser, setUserActive, deleteDoctor, assignDoctor, getAuditLogs,
  getSystemSettings, updateSystemSettings, downloadProtected, restoreDatabase,
} from "../api/api.js";

const emptyDoctor = { name: "", email: "", password: "", phone: "", specialization: "", registration_number: "" };

function AdminDashboard() {
  const [tab, setTab] = useState("overview");
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [settings, setSettings] = useState({ system_name: "Brain Tumor AI", maintenance_mode: "false", confidence_threshold: "70" });
  const [doctorForm, setDoctorForm] = useState(emptyDoctor);
  const [editing, setEditing] = useState(null);
  const editFormRef = useRef(null);
  const [userFilters, setUserFilters] = useState({ search: "", role: "", active: "" });
  const [predictionFilters, setPredictionFilters] = useState({ search: "", tumor_class: "", review_status: "" });
  const [assignments, setAssignments] = useState({});
  const [restoreFile, setRestoreFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const userParams = Object.fromEntries(Object.entries(userFilters).filter(([, value]) => value !== ""));
      if (userParams.active) userParams.active = userParams.active === "true";
      const predictionParams = Object.fromEntries(Object.entries(predictionFilters).filter(([, value]) => value));
      const [dashRes, usersRes, predictionsRes, logsRes, settingsRes] = await Promise.all([
        getAdminDashboard(), getAdminUsers(userParams), getAdminPredictions(predictionParams), getAuditLogs(), getSystemSettings(),
      ]);
      setDashboard(dashRes.data); setUsers(usersRes.data); setPredictions(predictionsRes.data); setLogs(logsRes.data); setSettings({ ...settingsRes.data });
    } catch (err) { setError(err.response?.data?.detail || "Failed to load admin dashboard"); }
  };
  useEffect(() => { load(); }, []);

  const action = async (runner, success) => {
  setError("");
  setMessage("");

  try {
    await runner();
    setMessage(success);
    await load();
    return true;
  } catch (err) {
    setError(
      err.response?.data?.detail ||
      err.message ||
      "Action failed"
    );
    return false;
  }
};
const openEditForm = (user) => {
  setEditing({
    ...user,
    age: user.age || "",
    gender: user.gender || "",
    phone: user.phone || "",
    specialization: user.specialization || "",
    registration_number: user.registration_number || "",
  });

  setTimeout(() => {
    editFormRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, 100);
};

  const addDoctor = (e) => { e.preventDefault(); action(() => createDoctor(doctorForm), "Doctor account created").then(() => setDoctorForm(emptyDoctor)); };
  const saveUser = async (e) => {
  e.preventDefault();

  if (!editing) {
    return;
  }

  const payload = {
    name: editing.name.trim(),
    phone: editing.phone?.trim() || null,
    age: editing.age ? Number(editing.age) : null,
    gender: editing.gender || null,
    specialization:
      editing.role === "doctor"
        ? editing.specialization?.trim() || null
        : null,
    registration_number:
      editing.role === "doctor"
        ? editing.registration_number?.trim() || null
        : null,
  };

  const success = await action(
    () => updateAdminUser(editing.id, payload),
    "User updated successfully"
  );

  if (success) {
    setEditing(null);
  }
};
  const saveSettings = (e) => { e.preventDefault(); action(() => updateSystemSettings({ system_name: settings.system_name, maintenance_mode: settings.maintenance_mode === "true", confidence_threshold: Number(settings.confidence_threshold) }), "Settings updated"); };
  const restore = (e) => {
    e.preventDefault();
    if (!restoreFile) return setError("Choose a SQLite backup file first");
    const formData = new FormData(); formData.append("file", restoreFile);
    action(() => restoreDatabase(formData), "Database restored. Restart the backend before continuing.");
  };

  const doctors = users.filter((user) => user.role === "doctor" && user.is_active);
  const formatBytes = (bytes = 0) => bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(2)} MB`;

  return <><Navbar /><main className="container"><div className="section-heading"><div><h1>Admin Dashboard</h1><p className="muted">Manage users, doctors, predictions, model status, exports, logs, and backups.</p></div></div>
    {error && <p className="error">{error}</p>}{message && <p className="success">{message}</p>}
    <div className="tabs">
      {[["overview", "Overview"], ["users", "Users & Doctors"], ["predictions", "Predictions"], ["system", "System & Logs"]].map(([key, label]) => <button key={key} className={tab === key ? "active" : "secondary-btn"} onClick={() => setTab(key)}>{label}</button>)}
    </div>

    {tab === "overview" && dashboard && <>
      <section className="dashboard-grid five-grid">
        <div className="stat-card"><span>Total Users</span><strong>{dashboard.total_users}</strong></div>
        <div className="stat-card"><span>Doctors</span><strong>{dashboard.total_doctors}</strong></div>
        <div className="stat-card"><span>Patients</span><strong>{dashboard.total_patients}</strong></div>
        <div className="stat-card"><span>MRI Scans</span><strong>{dashboard.total_mri_scans}</strong></div>
        <div className="stat-card"><span>Pending Reviews</span><strong>{dashboard.pending_reviews}</strong></div>
      </section>
      <section className="admin-grid dashboard-section">
        <div className="single-report"><h2>AI Model Performance</h2><dl className="detail-list">
          <div><dt>Mode</dt><dd>{dashboard.model.mock_mode ? "Demo mode" : "Trained model loaded"}</dd></div>
          <div><dt>Version</dt><dd>{dashboard.model.model_version}</dd></div>
          <div><dt>Accuracy</dt><dd>{dashboard.model.configured_accuracy ? `${dashboard.model.configured_accuracy}%` : "Not configured"}</dd></div>
          <div><dt>Low-confidence threshold</dt><dd>{dashboard.model.low_confidence_threshold}%</dd></div>
          <div><dt>System health</dt><dd>{dashboard.system_health}</dd></div>
          <div><dt>Storage usage</dt><dd>{formatBytes(dashboard.storage_usage_bytes)}</dd></div>
        </dl>{dashboard.model.mock_mode && <p className="warning">The trained Keras model is not included. Predictions remain clearly marked as demo outputs.</p>}</div>
        <div className="single-report"><h2>Review Workflow</h2><div className="result-grid"><div><span>Active Users</span><strong>{dashboard.active_users}</strong></div><div><span>Inactive Users</span><strong>{dashboard.inactive_users}</strong></div><div><span>Completed Reviews</span><strong>{dashboard.completed_reviews}</strong></div></div></div>
      </section>
      <section className="dashboard-section"><h2>Tumor Class Analytics</h2><div className="dashboard-grid">{Object.entries(dashboard.class_counts).map(([key, value]) => <div className="feature-card" key={key}><h3 className="capitalize">{key === "notumor" ? "No Tumor" : key}</h3><strong className="big-number">{value}</strong></div>)}</div></section>
      <section className="admin-grid dashboard-section"><div className="single-report"><h2>Daily Prediction Statistics</h2>{dashboard.daily_predictions.length ? <div className="bar-chart">{dashboard.daily_predictions.map((item) => <div className="bar-row" key={item.date}><span>{item.date}</span><div><i style={{ width: `${Math.max(5, Math.min(100, item.count * 10))}%` }} /></div><strong>{item.count}</strong></div>)}</div> : <p className="muted">No prediction activity in the last 30 days.</p>}</div><div className="single-report"><h2>Monthly Prediction Statistics</h2>{dashboard.monthly_predictions?.length ? <div className="bar-chart">{dashboard.monthly_predictions.map((item) => <div className="bar-row" key={item.month}><span>{item.month}</span><div><i style={{ width: `${Math.max(5, Math.min(100, item.count * 10))}%` }} /></div><strong>{item.count}</strong></div>)}</div> : <p className="muted">No monthly prediction activity.</p>}</div></section>
    </>}

    {tab === "users" && <>
      <section className="admin-grid">
        <form className="form-panel" onSubmit={addDoctor}><h2>Add Doctor</h2>
          <input placeholder="Doctor name" value={doctorForm.name} onChange={(e) => setDoctorForm({ ...doctorForm, name: e.target.value })} required />
          <input type="email" placeholder="Email" value={doctorForm.email} onChange={(e) => setDoctorForm({ ...doctorForm, email: e.target.value })} required />
          <input type="password" minLength="6" placeholder="Temporary password" value={doctorForm.password} onChange={(e) => setDoctorForm({ ...doctorForm, password: e.target.value })} required />
          <input placeholder="Specialization" value={doctorForm.specialization} onChange={(e) => setDoctorForm({ ...doctorForm, specialization: e.target.value })} />
          <input placeholder="Medical registration number" value={doctorForm.registration_number} onChange={(e) => setDoctorForm({ ...doctorForm, registration_number: e.target.value })} />
          <input placeholder="Phone" value={doctorForm.phone} onChange={(e) => setDoctorForm({ ...doctorForm, phone: e.target.value })} />
          <button>Create Doctor</button>
        </form>
        {editing ? <form ref={editFormRef} className="form-panel" onSubmit={saveUser}><div className="section-heading"><h2>Edit User</h2><button type="button" className="secondary-btn" onClick={() => setEditing(null)}>Cancel</button></div>
          <input value={editing.name || ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} required />
          <input value={editing.phone || ""} placeholder="Phone" onChange={(e) => setEditing({ ...editing, phone: e.target.value })} />
          <input type="number" value={editing.age || ""} placeholder="Age" onChange={(e) => setEditing({ ...editing, age: e.target.value ? Number(e.target.value) : null })} />
          <select value={editing.gender || ""} onChange={(e) => setEditing({ ...editing, gender: e.target.value })}><option value="">Gender</option><option>Female</option><option>Male</option><option>Other</option></select>
          {editing.role === "doctor" && <><input value={editing.specialization || ""} placeholder="Specialization" onChange={(e) => setEditing({ ...editing, specialization: e.target.value })} /><input value={editing.registration_number || ""} placeholder="Registration number" onChange={(e) => setEditing({ ...editing, registration_number: e.target.value })} /></>}
          <button>Save Changes</button>
        </form> : <div className="empty-panel"><h2>Edit User</h2><p>Select Edit from the users table.</p></div>}
      </section>
      <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <input placeholder="Search name or email" value={userFilters.search} onChange={(e) => setUserFilters({ ...userFilters, search: e.target.value })} />
        <select value={userFilters.role} onChange={(e) => setUserFilters({ ...userFilters, role: e.target.value })}><option value="">All roles</option><option value="patient">Patients</option><option value="doctor">Doctors</option><option value="admin">Admins</option></select>
        <select value={userFilters.active} onChange={(e) => setUserFilters({ ...userFilters, active: e.target.value })}><option value="">All status</option><option value="true">Active</option><option value="false">Inactive</option></select><button>Search</button>
      </form>
      <section className="table-wrapper"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Specialization</th><th>Actions</th></tr></thead><tbody>{users.map((user) => <tr key={user.id}><td>{user.name}</td><td>{user.email}</td><td className="capitalize">{user.role}</td><td><span className={`badge ${user.is_active ? "completed" : "needs_attention"}`}>{user.is_active ? "Active" : "Inactive"}</span></td><td>{user.specialization || "—"}</td><td><div className="action-row"><button
  type="button"
  className="small-btn"
  onClick={() => openEditForm(user)}
>
  Edit
</button><button className="secondary-btn" onClick={() => action(() => setUserActive(user.id, !user.is_active), `User ${user.is_active ? "deactivated" : "activated"}`)}>{user.is_active ? "Deactivate" : "Activate"}</button>{user.role === "doctor" && <button className="danger-btn" onClick={() => action(() => deleteDoctor(user.id), "Doctor deleted")}>Delete</button>}</div></td></tr>)}</tbody></table></section>
    </>}

    {tab === "predictions" && <>
      <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); load(); }}><input placeholder="Search patient or class" value={predictionFilters.search} onChange={(e) => setPredictionFilters({ ...predictionFilters, search: e.target.value })} /><select value={predictionFilters.tumor_class} onChange={(e) => setPredictionFilters({ ...predictionFilters, tumor_class: e.target.value })}><option value="">All classes</option><option value="glioma">Glioma</option><option value="meningioma">Meningioma</option><option value="pituitary">Pituitary</option><option value="notumor">No Tumor</option></select><select value={predictionFilters.review_status} onChange={(e) => setPredictionFilters({ ...predictionFilters, review_status: e.target.value })}><option value="">All review states</option><option value="pending_review">Pending</option><option value="needs_attention">Needs Attention</option><option value="under_review">Under Review</option><option value="completed">Completed</option></select><button>Search</button></form>
      <div className="action-row export-row"><button onClick={() => downloadProtected("/admin/export/predictions.csv", "prediction_reports.csv")}>Export CSV</button><button onClick={() => downloadProtected("/admin/export/summary.pdf", "system_summary.pdf")}>Export PDF</button></div>
      <section className="table-wrapper"><table><thead><tr><th>Report</th><th>Patient</th><th>Prediction</th><th>Confidence</th><th>Review</th><th>Assigned Doctor</th><th>Reassign</th></tr></thead><tbody>{predictions.map((report) => <tr key={report.id}><td>#{report.id}</td><td>{report.patient_name}</td><td className="capitalize">{report.predicted_class}</td><td>{report.confidence}%</td><td><span className={`badge ${report.review_status}`}>{report.review_status.replaceAll("_", " ")}</span></td><td>{report.assigned_doctor_name || "Unassigned"}</td><td><div className="action-row"><select value={assignments[report.id] || report.assigned_doctor_id || ""} onChange={(e) => setAssignments({ ...assignments, [report.id]: e.target.value })}><option value="">Choose doctor</option>{doctors.map((doctor) => <option key={doctor.id} value={doctor.id}>{doctor.name}</option>)}</select><button disabled={!assignments[report.id]} onClick={() => action(() => assignDoctor(report.id, assignments[report.id]), "Doctor assigned")}>Assign</button></div></td></tr>)}</tbody></table></section>
    </>}

    {tab === "system" && <section className="admin-grid">
      <div><form className="form-panel" onSubmit={saveSettings}><h2>System Settings</h2><label>System name<input value={settings.system_name || ""} onChange={(e) => setSettings({ ...settings, system_name: e.target.value })} /></label><label>Maintenance mode<select value={settings.maintenance_mode || "false"} onChange={(e) => setSettings({ ...settings, maintenance_mode: e.target.value })}><option value="false">Disabled</option><option value="true">Enabled</option></select></label><label>Low-confidence threshold<input type="number" min="1" max="100" value={settings.confidence_threshold || "70"} onChange={(e) => setSettings({ ...settings, confidence_threshold: e.target.value })} /></label><button>Save Settings</button></form>
        <div className="form-panel dashboard-section"><h2>Database Backup & Restore</h2><button onClick={() => downloadProtected("/admin/backup", "brain_tumor_backup.db")}>Download Backup</button><form onSubmit={restore}><input type="file" accept=".db,application/octet-stream" onChange={(e) => setRestoreFile(e.target.files?.[0] || null)} /><button className="danger-btn">Restore Backup</button></form><p className="warning">Restore replaces the current SQLite database. The backend must be restarted afterward.</p></div>
      </div>
      <section className="table-wrapper no-margin"><h2>Audit Logs</h2><table><thead><tr><th>Date</th><th>Actor</th><th>Action</th><th>Entity</th></tr></thead><tbody>{logs.map((log) => <tr key={log.id}><td>{new Date(log.created_at).toLocaleString()}</td><td>{log.actor_email || "System"}</td><td>{log.action.replaceAll("_", " ")}</td><td>{log.entity_type || "—"} {log.entity_id ? `#${log.entity_id}` : ""}</td></tr>)}</tbody></table></section>
    </section>}
  </main></>;
}

export default AdminDashboard;
