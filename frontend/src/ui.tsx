import { KeyboardEvent, ReactNode, useState } from "react";
import { diffClass } from "./api";

export function Panel({ children, className = "", hover = false }:
  { children: ReactNode; className?: string; hover?: boolean }) {
  return <div className={`card ${hover ? "card-hover card-lift" : ""} p-4 ${className}`}>{children}</div>;
}

export function Diff({ d }: { d: string }) {
  return <span className={diffClass(d)}>{d}</span>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-muted text-sm py-10 justify-center">
      <span className="inline-block w-4 h-4 border-2 border-muted border-t-brand rounded-full animate-spin" />
      {label || "Loading…"}
    </div>
  );
}

export function Stat({ label, value, sub, accent }:
  { label: string; value: ReactNode; sub?: ReactNode; accent?: boolean }) {
  return (
    <div className="card p-4 fade-in">
      <div className="text-muted text-[11px] uppercase tracking-wider font-semibold">{label}</div>
      <div className={`text-2xl font-extrabold mt-1 ${accent ? "text-brand glow-text" : ""}`}>{value}</div>
      {sub && <div className="text-muted text-xs mt-1">{sub}</div>}
    </div>
  );
}

export function Bar({ pct }: { pct: number }) {
  return <div className="bar"><i style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} /></div>;
}

export function Empty({ msg }: { msg: string }) {
  return <div className="text-muted text-sm py-10 text-center">{msg}</div>;
}

/* ---- HTB-style rank derived from XP ---- */
// Thresholds are deliberately demanding so a rank reflects real progress — roughly
// ~8,150 XP is available across all courses, labs and achievements, so "Hacker" (600)
// is several courses deep and "Omniscient" (7,000) is near-total mastery.
const RANKS = [
  { min: 0, name: "Noob", color: "#8a97b1" },
  { min: 150, name: "Script Kiddie", color: "#9fb0cc" },
  { min: 600, name: "Hacker", color: "#9fef00" },
  { min: 1400, name: "Pro Hacker", color: "#2ee6a6" },
  { min: 2800, name: "Elite Hacker", color: "#5cb2ff" },
  { min: 4500, name: "Guru", color: "#ffb01f" },
  { min: 7000, name: "Omniscient", color: "#ff5c9c" },
];
export function rankFor(xp: number) {
  let cur = RANKS[0], next = RANKS[RANKS.length - 1];
  for (let i = 0; i < RANKS.length; i++) {
    if (xp >= RANKS[i].min) { cur = RANKS[i]; next = RANKS[i + 1] || RANKS[i]; }
  }
  const span = next.min - cur.min || 1;
  const pct = next === cur ? 100 : Math.min(100, ((xp - cur.min) / span) * 100);
  return { ...cur, next, pct, toNext: Math.max(0, next.min - xp) };
}

export function RankBadge({ xp, size = 44 }: { xp: number; size?: number }) {
  const r = rankFor(xp);
  return (
    <div className="flex items-center gap-2">
      <Ring pct={r.pct} size={size} color={r.color}>
        <span className="text-[10px] font-bold" style={{ color: r.color }}>{xp}</span>
      </Ring>
      <div className="leading-tight">
        <div className="text-xs text-muted">Rank</div>
        <div className="font-bold text-sm" style={{ color: r.color }}>{r.name}</div>
      </div>
    </div>
  );
}

export function Ring({ pct, size = 48, stroke = 5, color = "var(--brand)", children }:
  { pct: number; size?: number; stroke?: number; color?: string; children?: ReactNode }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c - (Math.max(0, Math.min(100, pct)) / 100) * c;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="ring">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="var(--line2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke}
          strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: "stroke-dashoffset .6s ease", filter: "drop-shadow(0 0 4px " + color + "66)" }} />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}

export function Section({ title, right, children }:
  { title: string; right?: ReactNode; children: ReactNode }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-bold uppercase tracking-wider text-muted">{title}</h2>
        {right}
      </div>
      {children}
    </div>
  );
}

/* ---- Small, safe markdown renderer for trusted lesson content ---- */
function esc(s: string) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inline(s: string) {
  let out = esc(s);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  return out;
}
export function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const html: string[] = [];
  let inCode = false, inList = false;
  const flushList = () => { if (inList) { html.push("</ul>"); inList = false; } };
  for (const raw of lines) {
    if (raw.trim().startsWith("```")) {
      if (inCode) { html.push("</code></pre>"); inCode = false; }
      else { flushList(); html.push("<pre><code>"); inCode = true; }
      continue;
    }
    if (inCode) { html.push(esc(raw) + "\n"); continue; }
    const line = raw.trim();
    if (!line) { flushList(); continue; }
    if (line.startsWith("### ")) { flushList(); html.push(`<h3>${inline(line.slice(4))}</h3>`); }
    else if (line.startsWith("## ")) { flushList(); html.push(`<h2>${inline(line.slice(3))}</h2>`); }
    else if (line.startsWith("# ")) { flushList(); html.push(`<h1>${inline(line.slice(2))}</h1>`); }
    else if (line.startsWith("> ")) { flushList(); html.push(`<p class="pf-quote">${inline(line.slice(2))}</p>`); }
    else if (line.startsWith("- ")) {
      if (!inList) { html.push("<ul>"); inList = true; }
      html.push(`<li>${inline(line.slice(2))}</li>`);
    } else { flushList(); html.push(`<p>${inline(line)}</p>`); }
  }
  if (inCode) html.push("</code></pre>");
  flushList();
  return <div className="prose-body" dangerouslySetInnerHTML={{ __html: html.join("") }} />;
}

/* ---- docs building blocks: copyable code, tabs, callouts ---- */
export function CodeBlock({ code, label, lang }: { code: string; label?: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch {}
  };
  return (
    <div className="code-block">
      <div className="code-head">
        <span>{label || lang || "shell"}</span>
        <button type="button" className="btn btn-ghost py-0.5 px-2 text-xs" onClick={copy} aria-label={`Copy ${label || "code"}`}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre tabIndex={0}><code>{code}</code></pre>
    </div>
  );
}

export function Tabs({ tabs, active, onChange, label }:
  { tabs: [string, string][]; active: string; onChange: (id: string) => void; label: string }) {
  const keyNav = (e: KeyboardEvent, i: number) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length][0];
    onChange(next);
    (document.getElementById("tab-" + next) as HTMLElement | null)?.focus();
  };
  return (
    <div role="tablist" aria-label={label} className="flex flex-wrap gap-1 border-b border-line mb-4">
      {tabs.map(([id, text], i) => (
        <button key={id} id={"tab-" + id} role="tab" aria-selected={active === id} tabIndex={active === id ? 0 : -1}
          onKeyDown={e => keyNav(e, i)} onClick={() => onChange(id)}
          className={`px-3 py-2 text-sm -mb-px border-b-2 ${active === id ? "border-[var(--brand)] text-ink font-semibold" : "border-transparent text-muted hover:text-ink"}`}>
          {text}
        </button>
      ))}
    </div>
  );
}

export function Callout({ kind = "info", title, children }: { kind?: "info" | "warn" | "danger"; title?: string; children: ReactNode }) {
  return (
    <div role={kind === "info" ? "note" : "alert"} className={`callout callout-${kind}`}>
      {title && <div className="font-semibold mb-1">{title}</div>}
      <div className="text-sm">{children}</div>
    </div>
  );
}
