import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { Icon } from "./icons";

type Ach = { key: string; title: string; description: string; points: number; icon: string; earned: boolean };
type Toast = { key: string; title: string; description: string; points: number; icon: string };

const SEEN_KEY = "pwnforge-seen-achievements";

function loadSeen(): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]")); } catch { return new Set(); }
}
function saveSeen(s: Set<string>) {
  try { localStorage.setItem(SEEN_KEY, JSON.stringify([...s])); } catch { /* ignore */ }
}

/** Polls for earned achievements and pops a toast (top-right) for newly-earned ones. */
export default function AchievementToaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seeded = useRef(false);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      let items: Ach[];
      try { items = (await api.get("/api/achievements")).items; } catch { return; }
      if (!alive) return;
      const earned = items.filter(a => a.earned);
      const seen = loadSeen();
      if (!seeded.current) {
        // First poll after a (re)load: remember what's already earned without announcing it.
        earned.forEach(a => seen.add(a.key));
        saveSeen(seen);
        seeded.current = true;
        return;
      }
      const fresh = earned.filter(a => !seen.has(a.key));
      if (fresh.length) {
        fresh.forEach(a => seen.add(a.key));
        saveSeen(seen);
        setToasts(t => [...t, ...fresh.map(a => ({ key: a.key, title: a.title, description: a.description, points: a.points, icon: a.icon }))]);
      }
    };
    check();
    const t = setInterval(() => { if (!document.hidden) check(); }, 12000);
    const onVis = () => { if (!document.hidden) check(); };
    document.addEventListener("visibilitychange", onVis);
    return () => { alive = false; clearInterval(t); document.removeEventListener("visibilitychange", onVis); };
  }, []);

  const dismiss = (key: string) => setToasts(t => t.filter(x => x.key !== key));
  useEffect(() => {
    if (!toasts.length) return;
    const timers = toasts.map(t => setTimeout(() => dismiss(t.key), 6500));
    return () => timers.forEach(clearTimeout);
  }, [toasts]);

  if (!toasts.length) return null;
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
      {toasts.map(t => (
        <div key={t.key} role="status"
          className="flex items-start gap-3 p-3 rounded-xl border border-brand bg-[var(--panel3)] shadow-lg ach-toast-in cursor-pointer"
          onClick={() => dismiss(t.key)}>
          <div className="w-10 h-10 shrink-0 grid place-items-center rounded-lg bg-brand text-black">
            <Icon name={t.icon || "trophy"} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[11px] uppercase tracking-wider text-brand font-bold">Achievement unlocked</div>
            <div className="font-semibold text-sm text-ink truncate">{t.title}</div>
            <div className="text-muted text-xs mt-0.5">{t.description}{t.points ? ` · +${t.points} pts` : ""}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
