// src/ProtectedRoute.jsx
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import api from "./api";

export default function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    let mounted = true;
    api.get("/auth/me")
      .then(({data}) => {
        if (data?.user && mounted) localStorage.setItem("user", JSON.stringify(data.user));
        if (mounted) { setOk(true); setLoading(false); }
      })
      .catch(() => { if (mounted) { setOk(false); setLoading(false); }});
    return () => (mounted = false);
  }, []);

  if (loading) return null;
  if (!ok) return <Navigate to="/login" replace />;
  return children;
}
