/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        // Legacy
        darkBg: "#060D18",
        // Design Tokens
        void:    "#020408",
        base:    "#060D18",
        surface: "#0A1628",
        elevated:"#0F2040",
        card:    "#111D35",
        // Accent palette
        brand: {
          indigo:  "#6366F1",
          violet:  "#8B5CF6",
          emerald: "#10B981",
          amber:   "#F59E0B",
          rose:    "#F43F5E",
          sky:     "#38BDF8",
          cyan:    "#22D3EE",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      backdropBlur: {
        xs: "2px",
        "2xl": "40px",
      },
      animation: {
        "spin-slow": "spin 15s linear infinite",
        "breathe": "breathe 2s ease-in-out infinite",
      },
      keyframes: {
        breathe: {
          "0%, 100%": { boxShadow: "0 0 8px rgba(99,102,241,0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(99,102,241,0.7)" },
        },
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
}
