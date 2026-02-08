import { FormEvent, useState } from "react";

type AdPromptProps = {
  onGenerate: (prompt: string) => Promise<void>;
  loading: boolean;
};

export default function AdPrompt({ onGenerate, loading }: AdPromptProps) {
  const [prompt, setPrompt] = useState("Promote the campus food bank");

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) {
      return;
    }
    await onGenerate(trimmed);
  };

  return (
    <section className="panel">
      <p className="section-label">Ad Prompt</p>
      <h2 className="panel-title">Write the sponsored message</h2>

      <form className="mt-4 space-y-3" onSubmit={onSubmit}>
        <textarea
          className="prompt-input"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="What should the in-song ad promote?"
          rows={5}
        />
        <button
          className="action-button"
          type="submit"
          disabled={loading}
        >
          {loading ? "Generating Ad Segment..." : "Generate In-Song Ad"}
        </button>
      </form>
    </section>
  );
}
