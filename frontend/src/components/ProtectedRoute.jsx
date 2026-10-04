import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const loginFor = { user: "/login", therapist: "/therapist/login", admin: "/admin/login" };

export default function ProtectedRoute({ children, role = "user" }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid h-[60vh] place-items-center text-ink-soft">Loading…</div>;
  if (!user) return <Navigate to={loginFor[role]} replace />;
  if (user.role !== role) return <Navigate to={loginFor[user.role] || "/login"} replace />;
  return children;
}
