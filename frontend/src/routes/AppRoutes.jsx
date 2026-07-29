import { Navigate, Route, Routes } from "react-router-dom";
import Login from "../pages/Login.jsx";
import Register from "../pages/Register.jsx";
import Dashboard from "../pages/Dashboard.jsx";
import Predict from "../pages/Predict.jsx";
import History from "../pages/History.jsx";
import Report from "../pages/Report.jsx";
import DoctorDashboard from "../pages/DoctorDashboard.jsx";
import AdminDashboard from "../pages/AdminDashboard.jsx";
import Profile from "../pages/Profile.jsx";
import ChangePassword from "../pages/ChangePassword.jsx";
import Notifications from "../pages/Notifications.jsx";

function ProtectedRoute({ children, roles }) {
  const token = localStorage.getItem("token");
  const user = JSON.parse(localStorage.getItem("user") || "null");
  if (!token || !user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) {
    const target = user.role === "admin" ? "/admin" : user.role === "doctor" ? "/doctor" : "/dashboard";
    return <Navigate to={target} replace />;
  }
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<ProtectedRoute roles={["patient"]}><Dashboard /></ProtectedRoute>} />
      <Route path="/predict" element={<ProtectedRoute roles={["patient"]}><Predict /></ProtectedRoute>} />
      <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
      <Route path="/report/:reportId" element={<ProtectedRoute><Report /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
      <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
      <Route path="/doctor" element={<ProtectedRoute roles={["doctor"]}><DoctorDashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute roles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default AppRoutes;
