const styles = {
  pending: "bg-amber-100 text-amber-700",
  requested: "bg-sky-100 text-sky-700",
  confirmed: "bg-emerald-100 text-emerald-700",
  completed: "bg-violet-100 text-violet-700",
  cancelled: "bg-rose-100 text-rose-700",
  declined: "bg-rose-100 text-rose-700",
  expired: "bg-gray-100 text-gray-600",
  no_show: "bg-gray-100 text-gray-600",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
};
export default function StatusPill({ status }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${styles[status] || "bg-gray-100 text-gray-600"}`}>
      {status?.replace("_", " ")}
    </span>
  );
}
