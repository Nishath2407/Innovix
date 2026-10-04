export default function ExitSafelyButton() {
  const handleExit = () => {
    try { sessionStorage.clear(); } catch (e) { /* ignore */ }
    window.location.href = "https://www.google.com";
  };
  return (
    <button
      onClick={handleExit}
      title="Leaves this site immediately. This does not clear your browser history or network logs."
      className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full bg-ink/90 px-4 py-2.5 text-sm font-medium text-white shadow-soft backdrop-blur hover:bg-ink"
    >
      <span className="h-2 w-2 rounded-sm bg-peach" />
      Exit Safely
    </button>
  );
}
