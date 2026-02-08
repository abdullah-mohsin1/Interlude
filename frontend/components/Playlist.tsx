type InsertWindow = {
  start_ms: number;
  end_ms: number;
};

export type Song = {
  song_id: string;
  title: string;
  file: string;
  bpm: number;
  mood: string;
  insert_window: InsertWindow;
};

type PlaylistProps = {
  songs: Song[];
  selectedSongId: string | null;
  onSelect: (songId: string) => void;
};

export default function Playlist({ songs, selectedSongId, onSelect }: PlaylistProps) {
  return (
    <section className="surface-card p-4">
      <p className="section-label">Your Library</p>
      <h2 className="mt-2 text-lg font-bold text-white">Interlude Playlist</h2>

      <div className="mt-4 space-y-2">
        {songs.map((song, index) => {
          const selected = selectedSongId === song.song_id;
          return (
            <button
              key={song.song_id}
              className={`group flex w-full items-start gap-3 rounded-xl border p-3 text-left transition ${
                selected
                  ? "border-white/20 bg-white/10 shadow-glow"
                  : "border-transparent bg-white/[0.03] hover:border-white/10 hover:bg-white/[0.06]"
              }`}
              onClick={() => onSelect(song.song_id)}
            >
              <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-bold text-spotify-muted">
                {(index + 1).toString().padStart(2, "0")}
              </span>
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-white">{song.title}</span>
                <span className="mt-1 block truncate text-xs text-spotify-muted">
                  {song.mood} · {song.bpm} BPM
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
