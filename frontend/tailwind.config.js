/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)", panel: "var(--panel)", panel2: "var(--panel2)",
        ink: "var(--ink)", muted: "var(--muted)", line: "var(--line)",
        brand: "var(--brand)", brand2: "var(--brand2)", ok: "var(--ok)",
        warn: "var(--warn)", bad: "var(--bad)",
      },
      fontFamily: { mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"] },
    },
  },
  plugins: [],
};
