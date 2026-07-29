import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import { changePassword } from "../api/api.js";

function ChangePassword() {
  const [form, setForm] = useState({ old_password: "", new_password: "", confirm: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault(); setError(""); setMessage("");
    if (form.new_password !== form.confirm) return setError("New passwords do not match");
    try { const res = await changePassword({ old_password: form.old_password, new_password: form.new_password }); setMessage(res.data.message); setForm({ old_password: "", new_password: "", confirm: "" }); }
    catch (err) { setError(err.response?.data?.detail || "Password change failed"); }
  };
  return <><Navbar /><main className="container narrow"><h1>Change Password</h1><form className="form-panel" onSubmit={submit}>
    {error && <p className="error">{error}</p>}{message && <p className="success">{message}</p>}
    <input type="password" placeholder="Current password" value={form.old_password} onChange={(e) => setForm({ ...form, old_password: e.target.value })} required />
    <input type="password" placeholder="New password" minLength="6" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} required />
    <input type="password" placeholder="Confirm new password" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} required />
    <button>Change Password</button>
  </form></main></>;
}

export default ChangePassword;
