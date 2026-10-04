/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#241B33",
        "ink-soft": "#544468",
        cloud: "#FDFBFF",
        surface: "#FFFFFF",
        lavender: "#A78BFA",
        "lavender-deep": "#7C5CFC",
        mint: "#5EEAD4",
        peach: "#FFB4A2",
        sky: "#93C5FD",
        blush: "#FBCFE8",
        line: "rgba(36,27,51,0.08)",
      },
      fontFamily: {
        display: ["Plus Jakarta Sans", "sans-serif"],
        sans: ["Plus Jakarta Sans", "sans-serif"],
      },
      borderRadius: { "4xl": "2rem", "5xl": "2.5rem" },
      boxShadow: {
        soft: "0 8px 30px rgba(124,92,252,0.12)",
        glow: "0 0 0 1px rgba(255,255,255,0.5), 0 20px 40px rgba(124,92,252,0.18)",
      },
    },
  },
  plugins: [],
};
