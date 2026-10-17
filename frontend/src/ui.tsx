import { ReactNode } from "react";
import { diffClass } from "./api";

export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card p-4 ${className}`}>{children}</div>;
}

export function Diff({ d }: { d: string }) {
  return <span className={diffClass(d)}>{d}</span>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-muted text-sm py-6 justify-center">
      <span className="inline-block w-4 h-4 border-2 border-muted border-t-transparent rounded-full animate-spin" />
      {label || "Loading…"}
    </div>
  );
}

export function Stat({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return (
    <div className="card p-4">
      <div className="text-muted text-xs uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      {sub && <div className="text-muted text-xs mt-1">{sub}</div>}
    </div>
  );
}

export function Bar({ pct }: { pct: number }) {
  return (
    <div className="h-2 rounded-full bg-panel2 overflow-hidden">
      <div className="h-full bg-brand" style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} />
    </div>
  );
}

function esc(s: string) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Small, safe markdown renderer for trusted lesson content.
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
    else if (line.startsWith("- ")) {
      if (!inList) { html.push("<ul>"); inList = true; }
      html.push(`<li>${inline(line.slice(2))}</li>`);
    } else { flushList(); html.push(`<p>${inline(line)}</p>`); }
  }
  if (inCode) html.push("</code></pre>");
  flushList();
  return <div className="prose-body" dangerouslySetInnerHTML={{ __html: html.join("") }} />;
}

function inline(s: string) {
  let out = esc(s);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  return out;
}

export function Empty({ msg }: { msg: string }) {
  return <div className="text-muted text-sm py-8 text-center">{msg}</div>;
}
