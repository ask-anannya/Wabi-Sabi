/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#121014",
          card: "#1c1a1f",
          elevated: "#242229",
        },
        // Haven-matched accent palette (teal primary, lavender/coral for variety)
        brand: {
          50: "#eef8fc",
          400: "#5fb4d9",
          500: "#3a99c2",
          600: "#21809e",
        },
        lavender: "#b8a9c9",
        coral: "#d4807a",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 2px 8px rgba(20, 12, 10, 0.06)",
        lift: "0 12px 28px rgba(20, 12, 10, 0.12)",
        glass: "0 8px 32px rgba(20, 12, 10, 0.10)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      keyframes: {
        blobDrift: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%": { transform: "translate(4%, -6%) scale(1.05)" },
          "66%": { transform: "translate(-3%, 4%) scale(0.97)" },
        },
      },
      animation: {
        blob: "blobDrift 18s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
