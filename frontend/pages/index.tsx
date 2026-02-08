import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import Head from "next/head";
import Link from "next/link";

import { Song } from "../components/Playlist";
import { DEFAULT_SONGS, fetchConnectedSongs } from "../lib/defaultSongs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${mins}:${secs}`;
}

export default function HomePage() {
  const [songs, setSongs] = useState<Song[]>(DEFAULT_SONGS);
  const [activeSongId, setActiveSongId] = useState<string | null>(
    DEFAULT_SONGS[0]?.song_id || null
  );
  const [usingFallbackSongs, setUsingFallbackSongs] = useState(true);
  const [pendingAutoplay, setPendingAutoplay] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const loadSongs = async () => {
      try {
        const connectedSongs = await fetchConnectedSongs(API_BASE_URL);
        if (connectedSongs.length === 0) {
          return;
        }
        setSongs(connectedSongs);
        setUsingFallbackSongs(false);
        setActiveSongId((currentSongId) => {
          if (currentSongId && connectedSongs.some((song) => song.song_id === currentSongId)) {
            return currentSongId;
          }
          return connectedSongs[0].song_id;
        });
        setError(null);
      } catch (err) {
        setSongs(DEFAULT_SONGS);
        setUsingFallbackSongs(true);
        setActiveSongId((currentSongId) => currentSongId || DEFAULT_SONGS[0]?.song_id || null);
        setError(
          err instanceof Error
            ? `${err.message}. Using local song list.`
            : "Using local song list."
        );
      }
    };

    void loadSongs();
  }, []);

  const activeSong = useMemo(
    () => songs.find((song) => song.song_id === activeSongId) || null,
    [activeSongId, songs]
  );

  const resolveSongSrc = (song: Song | null) => {
    if (!song) return "";
    if (usingFallbackSongs && song.local_audio) {
      return song.local_audio;
    }
    return `${API_BASE_URL}/audio/originals/${song.file}`;
  };

  const activeSongSrc = resolveSongSrc(activeSong);
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onLoadedMetadata = () => setDuration(audio.duration || 0);
    const onTimeUpdate = () => setCurrentTime(audio.currentTime || 0);
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
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
    setDuration(0);
    setIsPlaying(false);

    if (!activeSongSrc) {
      setPendingAutoplay(false);
      return;
    }

    audio.load();
    if (!pendingAutoplay) {
      return;
    }

    const playSelected = async () => {
      try {
        await audio.play();
        setIsPlaying(true);
      } catch {
        setIsPlaying(false);
      } finally {
        setPendingAutoplay(false);
      }
    };

    void playSelected();
  }, [activeSongSrc, pendingAutoplay]);

  const onCardClick = async (song: Song) => {
    const audio = audioRef.current;
    if (!audio) return;

    if (song.song_id === activeSongId) {
      if (audio.paused) {
        await audio.play();
        setIsPlaying(true);
      } else {
        audio.currentTime = 0;
      }
      return;
    }

    setActiveSongId(song.song_id);
    setPendingAutoplay(true);
  };

  const togglePlayPause = async () => {
    const audio = audioRef.current;
    if (!audio || !activeSong) return;

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

  return (
    <>
      <Head>
        <title>Interlude AI</title>
        <meta
          name="description"
          content="Interlude AI home: Spotify-inspired library layout."
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
                <Link href="/">
                  <span className="fa fa-home"></span>
                  <span>Home</span>
                </Link>
              </li>
              <li>
                <Link href="/create">
                  <span className="fa fa-plus-square"></span>
                  <span>Create</span>
                </Link>
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
          <div className="home-layout">
            <div className="home-content">
              <div className="sticky-nav">
                <div className="nav-icons">
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/271/271220.png"
                    alt="Back"
                  />
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/271/271228.png"
                    alt="Forward"
                    className="hide"
                  />
                </div>
                <div className="sticky-nav-options">
                  <button className="badge nav-item hide">Explore Premium</button>
                  <button className="badge nav-item dark-badge">
                    <i className="fa-regular fa-circle-down" style={{ marginRight: 5 }}></i>
                    Install App
                  </button>
                  <i className="fa-regular fa-user nav-item"></i>
                </div>
              </div>

              <h2>Main Menu Songs</h2>
              <div className="cards-container">
                {songs.map((song) => (
                  <button
                    key={song.song_id}
                    type="button"
                    className={`card playable${song.song_id === activeSongId ? " active" : ""}`}
                    onClick={() => void onCardClick(song)}
                  >
                    <img
                      src={song.cover_image || "/images/love-yourself.jpeg"}
                      className="card-img"
                      alt={`${song.title} cover`}
                    />
                    <p className="card-title">{song.title}</p>
                    <p className="card-info">{song.artist || song.mood}</p>
                    <span className="card-badge">Playable</span>
                  </button>
                ))}
              </div>
              {error ? <p className="error-text">{error}</p> : null}

              <div className="footer">
                <div className="line"></div>
              </div>
            </div>

            <div className="music-player">
              <div className="album">
                <img
                  src={activeSong?.cover_image || "/images/love-yourself.jpeg"}
                  className="album-art"
                  alt={`${activeSong?.title || "song"} cover`}
                />
                <div className="album-meta">
                  <p className="album-title">{activeSong?.title || "No song selected"}</p>
                  <p className="album-artist">{activeSong?.artist || "Interlude"}</p>
                </div>
              </div>

              <div className="player">
                <div className="player-controls">
                  <button
                    type="button"
                    className="player-control-btn"
                    onClick={() => void togglePlayPause()}
                    disabled={!activeSong}
                  >
                    {isPlaying ? "Pause" : "Play"}
                  </button>
                </div>
                <div className="playback-bar">
                  <span className="curr-time">{formatTime(currentTime)}</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    className="progress-bar"
                    step={1}
                    value={progress}
                    onChange={onSeek}
                    disabled={!activeSong || duration === 0}
                  />
                  <span className="tot-time">{formatTime(duration)}</span>
                </div>
              </div>
              <div className="controls"></div>
            </div>
          </div>
        </div>
      </main>

      <audio ref={audioRef} src={activeSongSrc} preload="metadata" />
    </>
  );
}
