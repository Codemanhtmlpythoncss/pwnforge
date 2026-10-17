/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)", bg2: "var(--bg2)",
        panel: "var(--panel)", panel2: "var(--panel2)", panel3: "var(--panel3)",
        ink: "var(--ink)", ink2: "var(--ink2)", muted: "var(--muted)",
        line: "var(--line)", line2: "var(--line2)", accent: "var(--accent)",
        brand: "var(--brand)", brand2: "var(--brand2)", ok: "var(--ok)",
        warn: "var(--warn)", bad: "var(--bad)",
      },
      fontFamily: { mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"] },
    },
  },
  plugins: [],
};
