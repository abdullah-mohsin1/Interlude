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
        <script
          src="https://kit.fontawesome.com/23cecef777.js"
          crossOrigin="anonymous"
        ></script>
      </Head>

      <main>
        <div className="sidebar">
          <div className="logo">
            Interlude <span>AI</span>
          </div>

          <div className="navigation">
            <ul>
              <li>
                <a href="#">
                  <span className="fa fa-home"></span>
                  <span>Home</span>
                </a>
              </li>
              <li>
                <a href="#">
                  <span className="fa fa-search"></span>
                  <span>Explore</span>
                </a>
              </li>
              <li>
                <a href="#">
                  <span className="fa fas fa-book"></span>
                  <span>Library</span>
                </a>
              </li>
            </ul>
          </div>

          <div className="navigation">
            <ul>
              <li>
                <a href="#">
                  <span className="fa fas fa-plus-square"></span>
                  <span>Create Playlist</span>
                </a>
              </li>
              <li>
                <a href="#">
                  <span className="fa fas fa-heart"></span>
                  <span>Liked Songs</span>
                </a>
              </li>
            </ul>
          </div>

          <div className="policies">
            <ul>
              <li>
                <a href="#">Cookies</a>
              </li>
              <li>
                <a href="#">Privacy</a>
              </li>
            </ul>
          </div>
        </div>

        <div className="main-container">
          <div className="topbar">
            <div className="prev-next-buttons">
              <button type="button" className="fa fas fa-chevron-left"></button>
              <button type="button" className="fa fas fa-chevron-right"></button>
            </div>

            <div className="navbar">
              <ul>
                <li>
                  <a href="#">Premium</a>
                </li>
                <li>
                  <a href="#">Support</a>
                </li>
                <li>
                  <a href="#">Download</a>
                </li>
                <li className="divider">|</li>
                <li>
                  <a href="#">Sign Up</a>
                </li>
              </ul>
              <button type="button">Log In</button>
            </div>
          </div>

          <div className="content">
            <section className="hero-card">
              <p className="section-label">Interlude AI</p>
              <h1>Ads that live inside the music</h1>
              <p>
                Build voice-matched ad moments that feel native to the track. Select a song,
                generate a segment, and switch between original and injected versions instantly.
              </p>
            </section>

            <section className="section">
              <h2>Studio</h2>
              <div className="grid-split">
                <div>
                  <Playlist
                    songs={songs}
                    selectedSongId={selectedSongId}
                    onSelect={onSelectSong}
                  />
                  <Toggle mode={mode} modifiedReady={modifiedReady} onChange={setMode} />
                  <AdPrompt onGenerate={onGenerate} loading={loading} />
                </div>

                <div>
                  <Player
                    title={selectedSong?.title || "No song selected"}
                    sourceUrl={sourceUrl}
                    isModified={mode === "modified" && modifiedReady}
                  />

                  <section className="panel">
                    <p className="section-label">Generated Lyrics</p>
                    <div className="lyrics-box">
                      {generatedLyrics || "Generate an ad to see rhythmic lyric output."}
                    </div>
                    {error ? (
                      <p className="error-text">{error}</p>
                    ) : null}
                  </section>
                </div>
              </div>
            </section>
          </div>

          <div className="preview">
            <div className="text">
              <h6>Preview of Interlude</h6>
              <p>Generate in-song ad moments with occasional demos. No credit card needed.</p>
            </div>
            <div className="button">
              <button type="button">Sign up free</button>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
