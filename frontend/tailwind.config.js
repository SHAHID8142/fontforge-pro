/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          50: "#f6f6f7",
          100: "#e2e3e5",
          200: "#c4c5ca",
          300: "#9fa1a8",
          400: "#7a7c86",
          500: "#5d5f68",
          600: "#484a52",
          700: "#37383f",
          800: "#25262c",
          900: "#18191d",
          950: "#0d0e11",
        },
        accent: {
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
        },
      },
    },
  },
  plugins: [],
};
