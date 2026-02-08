import { Song } from "../components/Playlist";

export const DEFAULT_SONGS: Song[] = [
  {
    song_id: "song_1",
    title: "Love Yourself",
    artist: "Justin Bieber",
    cover_image: "/images/love-yourself.jpeg",
    local_audio: "/audio/love-yourself.mp3",
    file: "love_yourself.mp3",
    bpm: 100,
    mood: "acoustic pop",
    insert_window: {
      start_ms: 47000,
      end_ms: 55000
    }
  },
  {
    song_id: "song_2",
    title: "Blinding Lights",
    artist: "The Weeknd",
    cover_image: "https://i.scdn.co/image/ab67616d0000b273f63d0f44d2f9bca1dc8f6d5f",
    local_audio: "/audio/love-yourself.mp3",
    file: "blinding_lights.wav",
    bpm: 171,
    mood: "synth-pop",
    insert_window: {
      start_ms: 36000,
      end_ms: 44000
    }
  },
  {
    song_id: "song_3",
    title: "Levitating",
    artist: "Dua Lipa",
    cover_image: "https://i.scdn.co/image/ab67616d0000b273d4daf28d55fe4197ede848be",
    local_audio: "/audio/love-yourself.mp3",
    file: "levitating.wav",
    bpm: 103,
    mood: "dance-pop",
    insert_window: {
      start_ms: 52000,
      end_ms: 60000
    }
  },
  {
    song_id: "song_4",
    title: "Sunflower",
    artist: "Post Malone, Swae Lee",
    cover_image: "https://i.scdn.co/image/ab67616d0000b2731c959d50f1f9f7ad2f6f7f8a",
    local_audio: "/audio/love-yourself.mp3",
    file: "sunflower.wav",
    bpm: 90,
    mood: "melodic hip-hop",
    insert_window: {
      start_ms: 42000,
      end_ms: 50000
    }
  },
  {
    song_id: "song_5",
    title: "STAY",
    artist: "The Kid LAROI, Justin Bieber",
    cover_image: "https://i.scdn.co/image/ab67616d0000b273f8f5f7db89f72f6f35d57f56",
    local_audio: "/audio/love-yourself.mp3",
    file: "stay.wav",
    bpm: 170,
    mood: "pop",
    insert_window: {
      start_ms: 30000,
      end_ms: 38000
    }
  }
];

export async function fetchConnectedSongs(apiBaseUrl: string): Promise<Song[]> {
  const response = await fetch(`${apiBaseUrl}/api/songs`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load songs: ${response.status}`);
  }
  const data = (await response.json()) as Song[];
  return data.slice(0, 5);
}
