import Head from "next/head";
import { useEffect, useMemo, useState } from "react";

import AdPrompt from "../components/AdPrompt";
import Player from "../components/Player";
import Playlist, { Song } from "../components/Playlist";
import Toggle from "../components/Toggle";

type GenerateResponse = {
  lyrics: string;
  audio_url: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function HomePage() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [selectedSongId, setSelectedSongId] = useState<string | null>(null);
  const [mode, setMode] = useState<"original" | "modified">("original");
  const [generatedBySong, setGeneratedBySong] = useState<Record<string, string>>({});
  const [generatedLyrics, setGeneratedLyrics] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSongs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/songs`);
        if (!response.ok) {
          throw new Error(`Failed to load songs: ${response.status}`);
        }
        const data: Song[] = await response.json();
        setSongs(data);
        if (data.length > 0) {
          setSelectedSongId(data[0].song_id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    };

    void loadSongs();
  }, []);

  const selectedSong = useMemo(
    () => songs.find((song) => song.song_id === selectedSongId) || null,
    [songs, selectedSongId]
  );

  const modifiedReady = Boolean(selectedSongId && generatedBySong[selectedSongId]);

  const sourceUrl = useMemo(() => {
    if (!selectedSong) return "";
    if (mode === "modified" && modifiedReady && selectedSongId) {
      return `${API_BASE_URL}${generatedBySong[selectedSongId]}`;
    }
    return `${API_BASE_URL}/audio/originals/${selectedSong.file}`;
  }, [generatedBySong, mode, modifiedReady, selectedSong, selectedSongId]);

  const onSelectSong = (songId: string) => {
    setSelectedSongId(songId);
    setGeneratedLyrics("");
    setMode("original");
    setError(null);
  };

  const onGenerate = async (prompt: string) => {
    if (!selectedSongId) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          song_id: selectedSongId,
          ad_prompt: prompt
        })
      });

      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }

      const data: GenerateResponse = await response.json();
      setGeneratedLyrics(data.lyrics);
      setGeneratedBySong((prev) => ({ ...prev, [selectedSongId]: data.audio_url }));
      setMode("modified");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Interlude AI</title>
        <meta
          name="description"
          content="Interlude AI demo: in-song AI ads that blend into creator tracks."
        />
      </Head>

      <main className="mx-auto min-h-screen w-full max-w-[1400px] p-4 md:p-6">
        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <aside className="space-y-4">
            <section className="surface-card p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-spotify-accent">
                Interlude AI
              </p>
              <h1 className="mt-3 text-2xl font-extrabold leading-tight text-white">
                Ads that live inside the music
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-spotify-muted">
                Build voice-matched ad moments that feel native to the track. Select a song,
                generate a segment, and switch between original and injected versions instantly.
              </p>
            </section>

            <Playlist songs={songs} selectedSongId={selectedSongId} onSelect={onSelectSong} />
          </aside>

          <section className="space-y-4">
            <section className="surface-card relative overflow-hidden p-6">
              <div className="pointer-events-none absolute -top-24 right-[-50px] h-56 w-56 rounded-full bg-spotify-accent/25 blur-3xl" />
              <div className="relative z-10">
                <p className="section-label">Studio</p>
                <h2 className="mt-2 text-3xl font-extrabold text-white md:text-4xl">
                  Generate in-song placements in one click
                </h2>
                <p className="mt-3 max-w-2xl text-sm text-spotify-muted md:text-base">
                  Interlude composes short rhythmic ad lyrics, voices them in the creator style,
                  and prepares a modified mix for playback.
                </p>
              </div>
            </section>

            <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
              <div className="space-y-4">
                <Toggle mode={mode} modifiedReady={modifiedReady} onChange={setMode} />
                <AdPrompt onGenerate={onGenerate} loading={loading} />
              </div>

              <div className="space-y-4">
                <Player
                  title={selectedSong?.title || "No song selected"}
                  sourceUrl={sourceUrl}
                  isModified={mode === "modified" && modifiedReady}
                />

                <section className="surface-card p-5">
                  <p className="section-label">Generated Lyrics</p>
                  <pre className="mt-3 min-h-36 whitespace-pre-wrap rounded-xl border border-white/10 bg-zinc-950/70 p-4 font-mono text-sm leading-relaxed text-zinc-200">
                    {generatedLyrics || "Generate an ad to see rhythmic lyric output."}
                  </pre>
                  {error ? (
                    <p className="mt-3 rounded-lg border border-red-300/20 bg-red-400/10 px-3 py-2 text-sm text-red-300">
                      {error}
                    </p>
                  ) : null}
                </section>
              </div>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
