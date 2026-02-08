import Head from "next/head";
import Link from "next/link";

export default function HomePage() {
  const cardCovers = [
    "https://i.scdn.co/image/ab67616d0000b273a3c5882b3f0f5a0bdfc3c4a4",
    "https://i.scdn.co/image/ab67616d0000b273c0b2c9e4d5f1f28a1d4a10cd",
    "https://i.scdn.co/image/ab67616d0000b2732a3d2d16983b62f8c6f1c6b6",
    "https://i.scdn.co/image/ab67616d0000b273a13a5e3c4be2e6f0c0f4c1b5",
    "https://i.scdn.co/image/ab67616d0000b273b3e09c1d92c45fb6c77d1ad8",
    "https://i.scdn.co/image/ab67616d0000b2730f9c4a7f2c4cc7e2db7a2a1f"
  ];

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

              <h2>Recently Played</h2>
              <div className="cards-container">
                <div className="card">
                  <img src={cardCovers[0]} className="card-img" alt="Card cover" />
                  <p className="card-title">Top 50 - Global</p>
                  <p className="card-info">Your daily updates of the most played ...</p>
                </div>
              </div>

              <h2>Trending now near you</h2>
              <div className="cards-container">
                {cardCovers.slice(1, 6).map((cover, index) => (
                  <div className="card" key={`trend-${index}`}>
                    <img src={cover} className="card-img" alt="Card cover" />
                    <p className="card-title">Top 50 - Global</p>
                    <p className="card-info">Your daily updates of the most played ...</p>
                  </div>
                ))}
              </div>

              <h2>Featured Charts</h2>
              <div className="cards-container">
                {cardCovers.slice(0, 3).map((cover, index) => (
                  <div className="card" key={`feat-${index}`}>
                    <img src={cover} className="card-img" alt="Card cover" />
                    <p className="card-title">Top 50 - Global</p>
                    <p className="card-info">Your daily updates of the most played ...</p>
                  </div>
                ))}
              </div>

              <div className="footer">
                <div className="line"></div>
              </div>
            </div>

            <div className="music-player">
              <div className="album"></div>
              <div className="player">
                <div className="player-controls">
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/271/271220.png"
                    className="player-control-icon"
                    alt="Prev"
                  />
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/271/271218.png"
                    className="player-control-icon"
                    alt="Pause"
                  />
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/727/727245.png"
                    className="player-control-icon"
                    alt="Play"
                    style={{ opacity: 1, height: "2rem" }}
                  />
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/271/271228.png"
                    className="player-control-icon"
                    alt="Next"
                  />
                  <img
                    src="https://cdn-icons-png.flaticon.com/512/860/860828.png"
                    className="player-control-icon"
                    alt="Queue"
                  />
                </div>
                <div className="playback-bar">
                  <span className="curr-time">00:00</span>
                  <input type="range" min="0" max="100" className="progress-bar" step={1} />
                  <span className="tot-time">03:50</span>
                </div>
              </div>
              <div className="controls"></div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
