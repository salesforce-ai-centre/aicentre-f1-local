import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        f1: {
          red: "#E10600",
          black: "#15151E",
          white: "#FFFFFF",
          grey: "#38383F",
        },
        accent: {
          blue: "#0090FF",
          green: "#00D735",
          yellow: "#FFD700",
          orange: "#FF6700",
          purple: "#9333EA",
        },
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
      },
      fontFamily: {
        display: ["'Exo 2'", "system-ui", "sans-serif"],
        mono: ["'Roboto Mono'", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-warning": "pulse-warning 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-shift": "gradient-shift 3s ease infinite",
        "float": "float 20s ease-in-out infinite",
      },
      keyframes: {
        "pulse-warning": {
          "0%, 100%": {
            opacity: "1",
            transform: "scale(1)"
          },
          "50%": {
            opacity: "0.8",
            transform: "scale(1.05)"
          },
        },
        "gradient-shift": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "float": {
          "0%, 100%": { transform: "translate(0, 0) rotate(0deg)" },
          "33%": { transform: "translate(30px, -30px) rotate(120deg)" },
          "66%": { transform: "translate(-20px, 20px) rotate(240deg)" },
        }
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "f1-gradient": "linear-gradient(135deg, #E10600 0%, #0090FF 100%)",
        "grid-pattern": "url(\"data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23E10600' stroke-width='0.5' opacity='0.03'%3E%3Cpath d='M0 0l50 50M50 0l50 50M0 50l50 50M50 50l50 50'/%3E%3C/g%3E%3C/svg%3E\")",
      },
      boxShadow: {
        "f1": "0 10px 40px rgba(225, 6, 0, 0.1), 0 2px 12px rgba(0, 0, 0, 0.05)",
        "f1-hover": "0 20px 60px rgba(225, 6, 0, 0.15), 0 10px 20px rgba(0, 0, 0, 0.1)",
        "glow-red": "0 0 30px rgba(225, 6, 0, 0.5)",
        "glow-green": "0 0 30px rgba(0, 215, 53, 0.5)",
        "glow-blue": "0 0 30px rgba(0, 144, 255, 0.5)",
      },
    },
  },
  plugins: [],
} satisfies Config;