import { useEffect, useState } from "react";

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [isHr, setIsHr] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch("/api/common/notifications", { credentials: "include" }) // <- session cookie
      .then((r) => r.json().then((d) => (r.ok ? d : Promise.reject(d))))
      .then((data) => {
        setIsHr(Boolean(data.is_hr));
        setItems(data.results || []);
      })
      .catch((e) => setErr(e?.error || "Failed to load notifications"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading notifications...</div>;
  if (err) return <div className="text-red-600">Error: {err}</div>;

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">
        {isHr ? "HR Notifications" : "My Notifications"}
      </h2>

      {items.length === 0 && <div>No notifications.</div>}

      <ul className="space-y-3">
        {items.map((n) => (
          <li key={n.id || `${n.type}-${n.to || n.empId}-${n.createdAt || n.date}`} className="border rounded p-3">
            <div className="text-sm text-gray-600">
              {n.createdAt || n.date ? new Date(n.createdAt || n.date).toLocaleString() : ""}
            </div>
            <div className="font-medium">{n.reason || "Notification"}</div>
            <div className="text-xs text-gray-500 mt-1">
              type: {n.type}
              {n.to ? ` | to: ${n.to}` : ""}
              {n.empId ? ` | empId: ${n.empId}` : ""}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
