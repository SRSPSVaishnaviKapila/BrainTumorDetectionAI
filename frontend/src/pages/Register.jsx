import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api/api.js";

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", age: "", gender: "", phone: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await registerUser({ ...form, age: form.age ? Number(form.age) : null });
      setSuccess("Patient account created. You can now sign in.");
      setTimeout(() => navigate("/login"), 900);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div className="auth-page">
      <form onSubmit={submit} className="auth-form register-form">
        <h2>Create Patient Account</h2>
        <p className="muted">Doctor accounts are created securely by an administrator.</p>
        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}
        <input name="name" placeholder="Full Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <input type="email" name="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input type="password" name="password" placeholder="Password (minimum 6 characters)" minLength="6" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <input type="number" name="age" placeholder="Age" min="1" max="120" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} />
        <select name="gender" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
          <option value="">Select Gender</option><option>Female</option><option>Male</option><option>Other</option>
        </select>
        <input name="phone" placeholder="Phone (optional)" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <button type="submit">Register</button>
        <p>Already registered? <Link to="/login">Login</Link></p>
      </form>
    </div>
  );
}

export default Register;
