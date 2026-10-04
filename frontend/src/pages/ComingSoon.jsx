import Navbar from "../components/Navbar";

export default function ComingSoon({ title }) {
  return (
    <div>
      <Navbar />
      <div className="mx-auto flex max-w-2xl flex-col items-center px-6 py-32 text-center">
        <h1 className="mb-4 font-display text-3xl font-extrabold">{title}</h1>
        <p className="text-ink-soft">
          This part of SafeVoice is coming soon. We'd rather show you an honest "not built yet"
          than a fake feature.
        </p>
      </div>
    </div>
  );
}
