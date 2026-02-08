type ToggleMode = "original" | "modified";

type ToggleProps = {
  mode: ToggleMode;
  modifiedReady: boolean;
  onChange: (mode: ToggleMode) => void;
};

export default function Toggle({ mode, modifiedReady, onChange }: ToggleProps) {
  return (
    <section className="panel">
      <p className="section-label">Playback Mode</p>
      <div className="toggle-group">
        <button
          className={`toggle-button${mode === "original" ? " active" : ""}`}
          onClick={() => onChange("original")}
        >
          Original
        </button>
        <button
          className={`toggle-button modified${mode === "modified" ? " active" : ""}`}
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
