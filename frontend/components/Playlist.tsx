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
    <section className="panel">
      <p className="section-label">Your Library</p>
      <h2 className="panel-title">Interlude Playlist</h2>

      <div className="playlist-list">
        {songs.map((song, index) => {
          const selected = selectedSongId === song.song_id;
          return (
            <button
              key={song.song_id}
              className={`playlist-item${selected ? " selected" : ""}`}
              onClick={() => onSelect(song.song_id)}
            >
              <span className="playlist-index">
                {(index + 1).toString().padStart(2, "0")}
              </span>
              <span>
                <span className="playlist-title">{song.title}</span>
                <span className="playlist-meta">
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
