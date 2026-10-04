const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? match[2] : null;
}

async function request(path, { method = "GET", body, headers = {} } = {}) {
  const isWrite = ["POST", "PUT", "DELETE", "PATCH"].includes(method);
  const csrfToken = isWrite ? getCookie("csrf_access_token") : null;

  const res = await fetch(`${API_URL}${path}`, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "X-CSRF-TOKEN": csrfToken } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const error = new Error(data.message || "Something went wrong.");
    error.status = res.status;
    error.payload = data;
    throw error;
  }
  return data;
}

const qs = (params = {}) => {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""));
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
};

export const api = {
  // Auth
  register: (payload) => request("/api/auth/register", { method: "POST", body: payload }),
  login: (payload) => request("/api/auth/login", { method: "POST", body: payload }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  me: () => request("/api/auth/me"),
  forgotPassword: (email) => request("/api/auth/forgot-password", { method: "POST", body: { email } }),
  resetPassword: (token, password) => request("/api/auth/reset-password", { method: "POST", body: { token, password } }),
  changePassword: (current_password, new_password) => request("/api/auth/change-password", { method: "POST", body: { current_password, new_password } }),
  verifyEmail: (token) => request("/api/auth/verify-email", { method: "POST", body: { token } }),

  // User account
  getProfile: () => request("/api/users/me/profile"),
  updateProfile: (payload) => request("/api/users/me/profile", { method: "PUT", body: payload }),
  deleteAccount: (password) => request("/api/users/me", { method: "DELETE", body: { password } }),

  // Public therapist directory
  listTherapists: (params = {}) => request(`/api/therapists${qs(params)}`),
  getTherapist: (id) => request(`/api/therapists/${id}`),
  getSlots: (id, days = 7) => request(`/api/therapists/${id}/slots${qs({ days })}`),
  match: (preferences) => request("/api/matching", { method: "POST", body: preferences }),

  // Appointments (client)
  listAppointments: () => request("/api/appointments"),
  getAppointment: (id) => request(`/api/appointments/${id}`),
  createAppointment: (payload) => request("/api/appointments", { method: "POST", body: payload }),
  cancelAppointment: (id) => request(`/api/appointments/${id}`, { method: "DELETE" }),
  rescheduleAppointment: (id, scheduled_start) => request(`/api/appointments/${id}`, { method: "PUT", body: { action: "reschedule", scheduled_start } }),
  shareSummary: (id, share) => request(`/api/appointments/${id}`, { method: "PUT", body: { action: "share_summary", share } }),
  reviewAppointment: (id, rating, comment) => request(`/api/appointments/${id}/review`, { method: "POST", body: { rating, comment } }),

  // AI
  checkIn: (text) => request("/api/check-in", { method: "POST", body: { text } }),
  checkInHistory: () => request("/api/check-in/history"),
  checkInSummary: (payload) => request("/api/check-in/summary", { method: "POST", body: payload }),

  // Journal
  listJournal: () => request("/api/journal"),
  createJournalEntry: (payload) => request("/api/journal", { method: "POST", body: payload }),
  updateJournalEntry: (id, payload) => request(`/api/journal/${id}`, { method: "PUT", body: payload }),
  deleteJournalEntry: (id) => request(`/api/journal/${id}`, { method: "DELETE" }),

  // Safety
  getSafetyPlan: () => request("/api/safety-plan"),
  updateSafetyPlan: (payload) => request("/api/safety-plan", { method: "PUT", body: payload }),

  // Resources
  listResources: (category) => request(`/api/resources${qs({ category })}`),

  // Wellness
  getProgress: () => request("/api/progress"),
  getRecovery: () => request("/api/recovery"),
  completeRecoveryDay: (day, note) => request("/api/recovery/complete", { method: "POST", body: { day, note } }),
  resetRecovery: () => request("/api/recovery/reset", { method: "POST" }),

  // Notifications
  listNotifications: () => request("/api/notifications"),
  markNotificationRead: (id) => request(`/api/notifications/${id}/read`, { method: "POST" }),
  markAllNotificationsRead: () => request("/api/notifications/read-all", { method: "POST" }),

  // Payments
  paymentConfig: () => request("/api/payments/config"),
  createPaymentOrder: (appointment_id) => request("/api/payments/create-order", { method: "POST", body: { appointment_id } }),
  verifyPayment: (payload) => request("/api/payments/verify", { method: "POST", body: payload }),
  confirmTestPayment: (payment_id) => request("/api/payments/test-confirm", { method: "POST", body: { payment_id } }),

  // Sessions & chat
  getSessionByAppointment: (appointmentId) => request(`/api/sessions/by-appointment/${appointmentId}`),
  getSession: (id) => request(`/api/sessions/${id}`),
  startSession: (id) => request(`/api/sessions/${id}/start`, { method: "POST" }),
  endSession: (id) => request(`/api/sessions/${id}/end`, { method: "POST" }),
  saveSessionNotes: (id, notes) => request(`/api/sessions/${id}/notes`, { method: "PUT", body: { notes } }),
  getMessages: (sessionId, after) => request(`/api/messages/${sessionId}${qs({ after })}`),
  sendMessage: (sessionId, body) => request(`/api/messages/${sessionId}`, { method: "POST", body: { body } }),

  // Therapist portal
  therapistMe: () => request("/api/therapist/me"),
  updateTherapistProfile: (payload) => request("/api/therapist/me", { method: "PUT", body: payload }),
  therapistOverview: () => request("/api/therapist/overview"),
  getAvailability: () => request("/api/therapist/availability"),
  setAvailability: (availability) => request("/api/therapist/availability", { method: "PUT", body: { availability } }),
  therapistAppointments: (status) => request(`/api/therapist/appointments${qs({ status })}`),
  respondToAppointment: (id, action) => request(`/api/therapist/appointments/${id}/respond`, { method: "POST", body: { action } }),
  preSessionSummary: (appointmentId) => request(`/api/therapist/appointments/${appointmentId}/pre-session`),
  therapistEarnings: () => request("/api/therapist/earnings"),

  // Admin portal
  adminAnalytics: () => request("/api/admin/analytics"),
  adminSystem: () => request("/api/admin/system"),
  adminUsers: (params) => request(`/api/admin/users${qs(params)}`),
  suspendUser: (id) => request(`/api/admin/users/${id}/suspend`, { method: "POST" }),
  activateUser: (id) => request(`/api/admin/users/${id}/activate`, { method: "POST" }),
  adminTherapists: (params) => request(`/api/admin/therapists${qs(params)}`),
  verifyTherapist: (id, approve, note) => request(`/api/admin/therapists/${id}/verify`, { method: "POST", body: { approve, note } }),
  adminAppointments: (params) => request(`/api/admin/appointments${qs(params)}`),
  adminPayments: (params) => request(`/api/admin/payments${qs(params)}`),
  markRefunded: (id) => request(`/api/admin/payments/${id}/mark-refunded`, { method: "POST" }),
  auditLogs: (params) => request(`/api/admin/audit-logs${qs(params)}`),
  adminResources: () => request("/api/admin/resources"),
  createResource: (payload) => request("/api/admin/resources", { method: "POST", body: payload }),
  updateResource: (id, payload) => request(`/api/admin/resources/${id}`, { method: "PUT", body: payload }),
  deleteResource: (id) => request(`/api/admin/resources/${id}`, { method: "DELETE" }),
  adminReviews: (params) => request(`/api/admin/reviews${qs(params)}`),
  flagReview: (id, flag) => request(`/api/admin/reviews/${id}/flag`, { method: "POST", body: { flag } }),
};

export default api;
