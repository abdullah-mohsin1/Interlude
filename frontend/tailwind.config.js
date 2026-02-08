/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        spotify: {
          bg: "#070707",
          surface: "#121212",
          panel: "#181818",
          elevated: "#202020",
          muted: "#a7a7a7",
          accent: "#1db954",
          accentDark: "#169c46"
        }
      },
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      boxShadow: {
        panel: "0 20px 40px rgba(0, 0, 0, 0.35)",
        glow: "0 0 0 1px rgba(29, 185, 84, 0.35), 0 12px 36px rgba(29, 185, 84, 0.25)"
      }
    }
  },
  plugins: []
};
