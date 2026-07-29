import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginUser } from "../api/api.js";

function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      setLoading(true);
      const response = await loginUser(form);
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));
      const role = response.data.user.role;
      navigate(role === "admin" ? "/admin" : role === "doctor" ? "/doctor" : "/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-left">
          <h1>BrainTumor Detection AI</h1>
          <p>Upload MRI scans, receive an AI-assisted result, and continue through a secure doctor-review workflow.</p>
          <div className="demo-box">
            <strong>Project demonstration</strong>
            <p>Demo accounts are seeded by the backend. Credentials are documented in the project README for local development only.</p>
          </div>
        </div>
        <form onSubmit={handleLogin} className="auth-form">
          <h2>Login</h2>
          {error && <p className="error">{error}</p>}
          <input type="email" name="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <input type="password" name="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <button type="submit" disabled={loading}>{loading ? "Signing in..." : "Login"}</button>
          <p>New patient? <Link to="/register">Create account</Link></p>
        </form>
      </div>
    </div>
  );
}

export default Login;
