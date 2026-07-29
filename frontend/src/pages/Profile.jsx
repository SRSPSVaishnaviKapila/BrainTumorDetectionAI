import { useEffect, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import { getMe, updateProfile } from "../api/api.js";

function Profile() {
  const [form, setForm] = useState({ name: "", age: "", gender: "", phone: "", email: "", role: "", specialization: "", registration_number: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getMe().then((res) => setForm({ ...res.data, age: res.data.age || "", phone: res.data.phone || "" })).catch((err) => setError(err.response?.data?.detail || "Failed to load profile"));
  }, []);

  const save = async (e) => {
    e.preventDefault(); setError(""); setMessage("");
    try {
      const res = await updateProfile({ name: form.name, age: form.age ? Number(form.age) : null, gender: form.gender || null, phone: form.phone || null });
      localStorage.setItem("user", JSON.stringify(res.data.user));
      setMessage(res.data.message);
    } catch (err) { setError(err.response?.data?.detail || "Profile update failed"); }
  };

  return <><Navbar /><main className="container narrow"><h1>My Profile</h1><form className="form-panel" onSubmit={save}>
    {error && <p className="error">{error}</p>}{message && <p className="success">{message}</p>}
    <label>Full Name<input value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
    <label>Email<input value={form.email || ""} disabled /></label>
    <label>Role<input className="capitalize" value={form.role || ""} disabled /></label>
    {form.role === "doctor" && <><label>Specialization<input value={form.specialization || ""} disabled /></label><label>Registration Number<input value={form.registration_number || ""} disabled /></label></>}
    <label>Age<input type="number" min="1" max="120" value={form.age || ""} onChange={(e) => setForm({ ...form, age: e.target.value })} /></label>
    <label>Gender<select value={form.gender || ""} onChange={(e) => setForm({ ...form, gender: e.target.value })}><option value="">Select</option><option>Female</option><option>Male</option><option>Other</option></select></label>
    <label>Phone<input value={form.phone || ""} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
    <button>Update Profile</button>
  </form></main></>;
}

export default Profile;
