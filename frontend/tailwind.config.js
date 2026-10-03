/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        slate: { 50: "#f8f9ff" },
        academic: {
          canvas: "#f8f9ff",
          surface: "#ffffff",
          muted: "#eff4ff",
          blue: "#0051d5",
          navy: "#091426",
          emerald: "#059669",
          amber: "#d97706",
        },
      },
      fontFamily: { sans: ["Inter", "sans-serif"] },
    },
  },
  plugins: [],
};
