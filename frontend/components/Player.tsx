import { ChangeEvent, useEffect, useRef, useState } from "react";

type PlayerProps = {
  title: string;
  sourceUrl: string;
  isModified: boolean;
};

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${mins}:${secs}`;
}

export default function Player({ title, sourceUrl, isModified }: PlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onLoaded = () => setDuration(audio.duration || 0);
    const onTimeUpdate = () => setCurrentTime(audio.currentTime || 0);
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener("loadedmetadata", onLoaded);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("ended", onEnded);
    };
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    setCurrentTime(0);
    setIsPlaying(false);
  }, [sourceUrl]);

  const togglePlayback = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    await audio.play();
    setIsPlaying(true);
  };

  const onSeek = (event: ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio || !duration) return;
    const nextTime = (Number(event.target.value) / 100) * duration;
    audio.currentTime = nextTime;
    setCurrentTime(nextTime);
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <section className="surface-card p-5">
      <p className="section-label">Now Playing</p>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="max-w-[28ch] truncate text-lg font-bold text-white">{title}</h2>
          <p className="mt-1 text-xs font-medium text-spotify-muted">Interlude Demo Session</p>
        </div>

        <span
          className={`rounded-full border px-3 py-1 text-xs font-semibold ${
            isModified
              ? "border-spotify-accent/50 bg-spotify-accent/15 text-spotify-accent"
              : "border-white/15 bg-white/5 text-zinc-300"
          }`}
        >
          {isModified ? "Modified Mix" : "Original Mix"}
        </span>
      </div>

      <audio ref={audioRef} src={sourceUrl} preload="metadata" />

      <div className="mt-6 flex items-center gap-4">
        <button
          className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-spotify-accent text-lg text-zinc-950 transition hover:scale-105 hover:bg-[#22ca5d]"
          onClick={togglePlayback}
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? "❚❚" : "▶"}
        </button>

        <div className="w-full">
          <input
            className="spotify-range"
            type="range"
            min={0}
            max={100}
            value={progress}
            onChange={onSeek}
            aria-label="Track progress"
          />
          <div className="mt-2 flex items-center justify-between text-[11px] text-spotify-muted">
            <span className="font-mono">{formatTime(currentTime)}</span>
            <span className="font-mono">{formatTime(duration)}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
