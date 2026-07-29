import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import { getNotifications, markNotificationRead, markAllNotificationsRead } from "../api/api.js";

function Notifications() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
 const load = async () => {
  try {
    setError("");
    const response = await getNotifications();
    setItems(response.data);
  } catch (err) {
    setError(
      err.response?.data?.detail || "Failed to load notifications"
    );
  }
};

useEffect(() => {
  load();
}, []);
  const read = async (id) => { await markNotificationRead(id); load(); };
  const readAll = async () => { await markAllNotificationsRead(); load(); };
  return <><Navbar /><main className="container"><div className="section-heading"><h1>Notifications</h1><button onClick={readAll}>Mark All Read</button></div>{error && <p className="error">{error}</p>}
    <div className="history-list">{items.length ? items.map((item) => <article className={`notification-card ${item.is_read ? "" : "unread"}`} key={item.id}>
      <div><h3>{item.title}</h3><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small></div>
      <div className="action-row">{item.report_id && <Link className="small-btn" to={`/report/${item.report_id}`}>Open Report</Link>}{!item.is_read && <button className="secondary-btn" onClick={() => read(item.id)}>Mark Read</button>}</div>
    </article>) : <div className="empty-panel">No notifications.</div>}</div>
  </main></>;
}

export default Notifications;
