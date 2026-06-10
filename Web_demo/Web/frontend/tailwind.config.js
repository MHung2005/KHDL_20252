/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f9ff",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
        },
        surface: {
          DEFAULT: "#ffffff",
          card:    "#f8fafc",
          hover:   "#f1f5f9",
          border:  "#e2e8f0",
        },
        ink: {
          DEFAULT: "#0f172a",
          muted:   "#64748b",
          faint:   "#cbd5e1",
        },
        accent: {
          violet: "#a78bfa",
          pink:   "#f472b6",
          teal:   "#34d399",
          amber:  "#fbbf24",
        },
      },
      fontFamily: {
        sans: ["'DM Sans'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      animation: {
        "fade-in":    "fadeIn 0.4s ease forwards",
        "slide-up":   "slideUp 0.4s ease forwards",
        "pulse-slow": "pulse 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: "translateY(12px)" }, to: { opacity: 1, transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};
