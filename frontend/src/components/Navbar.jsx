import { Link, useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const home = user.role === "admin" ? "/admin" : user.role === "doctor" ? "/doctor" : "/dashboard";

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to={home} className="brand">🧠 NeuroScan AI</Link>
      <div className="nav-links">
        <Link to={home}>Dashboard</Link>
        {user.role === "patient" && <Link to="/predict">Upload MRI</Link>}
        <Link to="/history">Reports</Link>
        <Link to="/notifications">Notifications</Link>
        <Link to="/profile">Profile</Link>
        <Link to="/change-password">Password</Link>
        <button onClick={logout} className="logout-btn">Logout</button>
      </div>
    </nav>
  );
}

export default Navbar;
