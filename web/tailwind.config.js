/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0f0f0f",
        primary: "#4F8CFF",
        accent: "#8E6FFF",
        active: "#4F8CFF",
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
        neutral: {
          50: "#fafafa",
          100: "#f5f5f5",
          200: "#e5e5e5",
          300: "#d4d4d4",
          400: "#a3a3a3",
          500: "#737373",
          600: "#525252",
          700: "#404040",
          750: "#2A2A2A",
          800: "#262626",
          900: "#171717",
          950: "#0A0A0A",
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
      keyframes: {
        flipTop: {
          "0%": { transform: "rotateX(0)" },
          "100%": { transform: "rotateX(-90deg)" },
        },
        flipBottom: {
          "0%": { transform: "rotateX(90deg)" },
          "100%": { transform: "rotateX(0)" },
        },
      },
      animation: {
        flipTop: "flipTop 0.5s ease forwards",
        flipBottom: "flipBottom 0.5s ease forwards",
      },
    },
  },
  plugins: [],
};
