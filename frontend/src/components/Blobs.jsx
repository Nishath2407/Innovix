export default function Blobs({ variant = "default" }) {
  const sets = {
    default: [
      "blob top-[-10%] left-[-8%] w-[420px] h-[420px] bg-lavender animate-float",
      "blob top-[10%] right-[-10%] w-[380px] h-[380px] bg-mint animate-float [animation-delay:1.5s]",
      "blob bottom-[-15%] left-[20%] w-[360px] h-[360px] bg-peach animate-float [animation-delay:3s]",
    ],
    quiet: [
      "blob top-[-10%] right-[10%] w-[320px] h-[320px] bg-blush animate-float",
      "blob bottom-[5%] left-[-10%] w-[300px] h-[300px] bg-sky animate-float [animation-delay:2s]",
    ],
  };
  return (
    <div className="absolute inset-0 overflow-hidden -z-10">
      {sets[variant].map((cls, i) => <div key={i} className={cls} />)}
    </div>
  );
}
