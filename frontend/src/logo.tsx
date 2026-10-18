// Pwnforge logo — a forged hexagonal emblem with a terminal prompt.
// The hex nods to the "techy badge" family; the >_ prompt is the pwn/terminal
// mark; the ember dots are the "forge". Theme-aware via CSS variables.

export function LogoMark({ size = 34, glow = true }: { size?: number; glow?: boolean }) {
  const id = "pf" + Math.random().toString(36).slice(2, 7);
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none"
      style={glow ? { filter: "drop-shadow(0 0 6px rgba(159,239,0,.45))" } : undefined} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--panel3)" />
          <stop offset="1" stopColor="var(--panel2)" />
        </linearGradient>
      </defs>
      {/* hex body */}
      <path d="M20 1.8 37.6 11.9 37.6 28.1 20 38.2 2.4 28.1 2.4 11.9Z"
        fill={`url(#${id})`} stroke="var(--brand)" strokeWidth="1.8" strokeLinejoin="round" />
      {/* top facet (forged sheen) */}
      <path d="M20 1.8 37.6 11.9 20 20 2.4 11.9Z" fill="var(--brand)" opacity="0.10" />
      {/* terminal prompt chevron */}
      <path d="M13 15.5 19 20 13 24.5" stroke="var(--brand)" strokeWidth="2.6"
        strokeLinecap="round" strokeLinejoin="round" />
      {/* cursor block */}
      <rect x="21.4" y="22.2" width="6.2" height="2.6" rx="1" fill="var(--brand)" />
      {/* forge embers */}
      <circle cx="28.5" cy="13.2" r="1.25" fill="var(--brand)" />
      <circle cx="31.2" cy="16.4" r="0.8" fill="var(--brand)" opacity="0.7" />
      <circle cx="26.3" cy="16.1" r="0.7" fill="var(--brand)" opacity="0.55" />
    </svg>
  );
}

const DIFF_COLOR: Record<string, string> = {
  orientation: "#9fb0cc", beginner: "#9fef00", easy: "#9fef00",
  intermediate: "#ffb01f", hard: "#ff9166", advanced: "#ff5c6c",
  expert: "#ff5c9c", mastery: "#ff5c9c",
};
const OS_LETTER: Record<string, string> = {
  debian: "D", kali: "K", ubuntu: "U", windows: "W", alpine: "A", freebsd: "F",
};

// Hexagonal machine avatar, tinted by difficulty, with the OS initial.
export function MachineAvatar({ os, difficulty, size = 46 }:
  { os: string; difficulty: string; size?: number }) {
  const c = DIFF_COLOR[difficulty] || "#9fb0cc";
  const letter = OS_LETTER[os] || (os ? os[0].toUpperCase() : "?");
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden>
      <path d="M20 2.5 36.9 12.25 36.9 27.75 20 37.5 3.1 27.75 3.1 12.25Z"
        fill={c} opacity="0.12" />
      <path d="M20 2.5 36.9 12.25 36.9 27.75 20 37.5 3.1 27.75 3.1 12.25Z"
        fill="none" stroke={c} strokeWidth="1.6" strokeLinejoin="round" />
      <text x="20" y="20" dominantBaseline="central" textAnchor="middle"
        fontSize="15" fontWeight="800" fill={c}
        fontFamily="ui-monospace, monospace">{letter}</text>
    </svg>
  );
}

export function Logo({ size = 34, className = "", word = true }:
  { size?: number; className?: string; word?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <LogoMark size={size} />
      {word && (
        <span className="font-extrabold tracking-tight leading-none"
          style={{ fontSize: size * 0.56 }}>
          Pwn<span className="text-brand glow-text">forge</span>
        </span>
      )}
    </span>
  );
}
