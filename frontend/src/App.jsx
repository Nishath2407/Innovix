import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import TherapistApply from "./pages/TherapistApply";
import Dashboard from "./pages/Dashboard";
import Therapists from "./pages/Therapists";
import Match from "./pages/Match";
import CheckIn from "./pages/CheckIn";
import Journal from "./pages/Journal";
import Appointments from "./pages/Appointments";
import SessionRoom from "./pages/SessionRoom";
import Progress from "./pages/Progress";
import Recovery from "./pages/Recovery";
import SafetyPlanPage from "./pages/SafetyPlanPage";
import Privacy from "./pages/Privacy";
import Safety from "./pages/Safety";
import Resources from "./pages/Resources";
import TherapistDashboard from "./pages/TherapistDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import ComingSoon from "./pages/ComingSoon";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/therapists" element={<Therapists />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/safety" element={<Safety />} />
      <Route path="/resources" element={<Resources />} />
      <Route path="/faq" element={<ComingSoon title="FAQ" />} />
      <Route path="/terms" element={<ComingSoon title="Terms" />} />

      {/* Client auth */}
      <Route path="/login" element={<Login portal="user" />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ComingSoon title="Forgot password" />} />
      <Route path="/reset-password" element={<ComingSoon title="Reset password" />} />
      <Route path="/verify-email" element={<ComingSoon title="Verify email" />} />

      {/* Therapist auth */}
      <Route path="/therapist/login" element={<Login portal="therapist" />} />
      <Route path="/therapist/apply" element={<TherapistApply />} />

      {/* Admin auth */}
      <Route path="/admin/login" element={<Login portal="admin" />} />

      {/* Client app (protected) */}
      <Route path="/dashboard" element={<ProtectedRoute role="user"><Dashboard /></ProtectedRoute>} />
      <Route path="/match" element={<ProtectedRoute role="user"><Match /></ProtectedRoute>} />
      <Route path="/check-in" element={<ProtectedRoute role="user"><CheckIn /></ProtectedRoute>} />
      <Route path="/journal" element={<ProtectedRoute role="user"><Journal /></ProtectedRoute>} />
      <Route path="/appointments" element={<ProtectedRoute role="user"><Appointments /></ProtectedRoute>} />
      <Route path="/progress" element={<ProtectedRoute role="user"><Progress /></ProtectedRoute>} />
      <Route path="/recovery" element={<ProtectedRoute role="user"><Recovery /></ProtectedRoute>} />
      <Route path="/safety-plan" element={<ProtectedRoute role="user"><SafetyPlanPage /></ProtectedRoute>} />

      {/* Session room: reachable by client or therapist, checked server-side */}
      <Route path="/session/:id" element={<SessionRoom />} />

      {/* Therapist portal (protected) */}
      <Route path="/therapist/dashboard" element={<ProtectedRoute role="therapist"><TherapistDashboard /></ProtectedRoute>} />

      {/* Admin portal (protected) */}
      <Route path="/admin/dashboard" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />

      <Route path="*" element={<ComingSoon title="Page not found" />} />
    </Routes>
  );
}
