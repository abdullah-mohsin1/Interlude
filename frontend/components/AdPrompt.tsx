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
    <section className="surface-card p-4">
      <p className="section-label">Ad Prompt</p>
      <h2 className="mt-2 text-lg font-semibold text-white">Write the sponsored message</h2>

      <form className="mt-4 space-y-3" onSubmit={onSubmit}>
        <textarea
          className="min-h-32 w-full resize-y rounded-xl border border-white/10 bg-zinc-950/80 px-4 py-3 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-500 focus:border-spotify-accent focus:ring-2 focus:ring-spotify-accent/30"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="What should the in-song ad promote?"
          rows={5}
        />
        <button
          className="inline-flex w-full items-center justify-center rounded-xl bg-spotify-accent px-4 py-3 text-sm font-extrabold text-zinc-950 transition hover:bg-[#21cc5d] disabled:cursor-wait disabled:opacity-60"
          type="submit"
          disabled={loading}
        >
          {loading ? "Generating Ad Segment..." : "Generate In-Song Ad"}
        </button>
      </form>
    </section>
  );
}
