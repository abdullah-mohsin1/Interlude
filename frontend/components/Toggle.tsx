type ToggleMode = "original" | "modified";

type ToggleProps = {
  mode: ToggleMode;
  modifiedReady: boolean;
  onChange: (mode: ToggleMode) => void;
};

export default function Toggle({ mode, modifiedReady, onChange }: ToggleProps) {
  return (
    <section className="surface-card p-4">
      <p className="section-label">Playback Mode</p>
      <div className="mt-3 grid grid-cols-2 gap-2 rounded-xl bg-zinc-950/70 p-1">
        <button
          className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${
            mode === "original"
              ? "bg-white text-zinc-900"
              : "text-zinc-300 hover:bg-white/10 hover:text-white"
          }`}
          onClick={() => onChange("original")}
        >
          Original
        </button>
        <button
          className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${
            mode === "modified"
              ? "bg-spotify-accent text-zinc-950"
              : "text-zinc-300 hover:bg-white/10 hover:text-white"
          } disabled:cursor-not-allowed disabled:opacity-40`}
          onClick={() => onChange("modified")}
          disabled={!modifiedReady}
          title={modifiedReady ? "Play generated version" : "Generate an ad first"}
        >
          Modified
        </button>
      </div>
    </section>
  );
}
