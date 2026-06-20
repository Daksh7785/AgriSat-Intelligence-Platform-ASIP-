/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#0B0F19",
        cardBg: "rgba(22, 28, 45, 0.7)",
        borderBg: "rgba(255, 255, 255, 0.08)",
        primaryGreen: "#10B981",
        accentBlue: "#3B82F6",
        alertRed: "#EF4444",
        alertOrange: "#F59E0B"
      },
      backdropBlur: {
        xs: "2px"
      }
    },
  },
  plugins: [],
}
