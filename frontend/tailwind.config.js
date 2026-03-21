/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f4ff",
          100: "#e0eaff",
          200: "#c1d5ff",
          300: "#98b8ff",
          400: "#6690ff",
          500: "#4169ff",
          600: "#2a4fff",
          700: "#1a3ae0",
          800: "#1730b8",
          900: "#182b91",
          950: "#0d1657",
        },
        accent: {
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
        },
        success: "#10b981",
        warning: "#f59e0b",
        danger:  "#ef4444",
        surface: {
          DEFAULT: "#0f1117",
          card:    "#1a1d27",
          border:  "#2a2d3a",
          hover:   "#222535",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "gradient-brand": "linear-gradient(135deg, #4169ff 0%, #8b5cf6 100%)",
        "gradient-dark":  "linear-gradient(180deg, #1a1d27 0%, #0f1117 100%)",
        "gradient-card":  "linear-gradient(135deg, #1a1d27 0%, #222535 100%)",
      },
      boxShadow: {
        glow:     "0 0 20px rgba(65, 105, 255, 0.35)",
        "glow-sm":"0 0 10px rgba(65, 105, 255, 0.25)",
        card:     "0 4px 24px rgba(0,0,0,0.4)",
      },
      animation: {
        "fade-in":    "fadeIn 0.3s ease-out",
        "slide-up":   "slideUp 0.4s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "spin-slow":  "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn:  { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: { "0%": { opacity: "0", transform: "translateY(16px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};
