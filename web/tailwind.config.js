/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#000000",
        primary: "#4F8CFF",
        accent: "#8E6FFF",
        surface: "#1A1A2E",
        card: "#262638",
        textPrimary: "#FFFFFF",
        textSecondary: "#C6C6D9",
        success: "#4CD964",
        warning: "#FFC043",
        error: "#E53E3E",
        taskColors: {
          high: "#E53E3E",
          medium: "#FFC043",
          low: "#4CD964",
          default: "#8E6FFF",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};
