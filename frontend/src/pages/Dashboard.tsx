import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Diff, Panel, Ring, Skeleton, Stat, rankFor } from "../ui";
import { Icon } from "../icons";

export default function Dashboard() {
  const [d, setD] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  const [host, setHost] = useState<any>(null);
  useEffect(() => {
    api.get("/api/dashboard").then(setD);
    api.get("/api/recommendations?limit=4").then(r => setRecs(r.items));
  }, []);
  // Keep the "live" host rings actually live — refresh just the metrics, not the whole dashboard.
  useEffect(() => {
    const poll = () => { if (!document.hidden) api.get("/api/host/stats").then(setHost).catch(() => {}); };
    const t = setInterval(poll, 5000);
    document.addEventListener("visibilitychange", poll);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", poll); };
  }, []);
  if (!d) return <DashboardSkeleton />;
  const h = host || d.host;
  const rank = rankFor(d.xp);

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="card p-5 flex flex-col md:flex-row md:items-center gap-5 overflow-hidden relative">
        <div className="absolute inset-0 pointer-events-none opacity-[0.07]"
          style={{ background: "radial-gradient(400px 200px at 90% -40%, var(--brand), transparent)" }} />
        <Ring pct={rank.pct} size={86} stroke={7} color={rank.color}>
          <div className="text-center">
            <div className="text-lg font-extrabold" style={{ color: rank.color }}>{d.xp}</div>
            <div className="text-[9px] text-muted -mt-0.5">XP</div>
          </div>
        </Ring>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xl font-extrabold" style={{ color: rank.color }}>{rank.name}</span>
            <Diff d={d.level} />
          </div>
          <div className="text-muted text-sm mt-0.5">
            {d.courses_completed}/{d.courses_total} courses complete
            {rank.name !== rank.next.name && <> · <span className="text-ink">{rank.toNext} XP</span> to {rank.next.name}</>}
          </div>
          <div className="mt-2 max-w-md"><div className="bar"><i style={{ width: `${rank.pct}%`, background: rank.color }} /></div></div>
        </div>
        {d.show_streak && d.gamification && (
          <div className="text-center px-5">
            <div className="text-3xl font-extrabold text-brand glow-text">{d.streak_days}</div>
            <div className="text-[11px] text-muted uppercase tracking-wide">day streak</div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link to="/courses"><Stat label="Courses done" value={d.courses_completed} sub={`${d.courses_in_progress} in progress`} /></Link>
        <Link to="/machines"><Stat label="Machines" value={d.profiles_available} sub="in catalogue" accent /></Link>
        <Link to="/labs"><Stat label="Running VMs" value={d.running_vms} sub={`${d.active_labs} active labs`} /></Link>
        <Stat label="VM failures" value={d.vm_failures} sub="recent errors" />
      </div>

      {/* Host metrics as rings */}
      <Panel>
        <div className="flex items-center gap-2 mb-4">
          <Icon name="server" className="text-brand" /><span className="font-semibold">Host resources</span>
          <span className="tag ml-auto">live</span>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <Metric label="CPU" pct={h.cpu.percent} sub={`${h.cpu.cores_logical} cores`} />
          <Metric label="Memory" pct={h.memory.percent}
            sub={`${Math.round(h.memory.used_mb/1024)} / ${Math.round(h.memory.total_mb/1024)} GB`} />
          <Metric label="Storage" pct={h.storage.percent} sub={`${h.storage.free_gb} GB free`} />
        </div>
      </Panel>

      <div className="grid md:grid-cols-2 gap-4">
        <Panel>
          <div className="flex items-center gap-2 mb-3"><Icon name="route" className="text-brand" /><span className="font-semibold">Recommended next</span></div>
          <div className="space-y-2">
            {recs.map(r => (
              <Link key={r.course.id} to={`/courses/${r.course.id}`}
                className="card card-hover p-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-medium truncate">{r.course.title}</div>
                  <div className="text-muted text-xs mt-0.5 truncate">{r.reasons.join(" · ")}</div>
                </div>
                <Diff d={r.course.difficulty} />
              </Link>
            ))}
            {recs.length === 0 && <div className="text-muted text-sm">Start a course to get recommendations.</div>}
          </div>
        </Panel>
        <Panel>
          <div className="flex items-center gap-2 mb-3"><Icon name="terminal" className="text-brand" /><span className="font-semibold">Recent activity</span></div>
          <div className="space-y-1 text-sm">
            {d.recent_activity.map((a: any, i: number) => (
              <div key={i} className="flex justify-between items-center py-1 border-b border-line last:border-0">
                <span className="mono text-brand text-xs">{a.action}</span>
                <span className="text-muted text-[11px]">{new Date(a.at).toLocaleString()}</span>
              </div>
            ))}
            {d.recent_activity.length === 0 && <div className="text-muted">No activity yet.</div>}
          </div>
          {d.recent_achievements.length > 0 && (
            <div className="mt-4 hairline pt-3">
              <div className="font-semibold mb-2 text-xs uppercase tracking-wide text-muted">Recent achievements</div>
              <div className="flex flex-wrap gap-2">
                {d.recent_achievements.map((a: any) => <span key={a.key} className="tag tag-green"><Icon name="trophy" size={12} /> {a.key}</span>)}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

function Metric({ label, pct, sub }: { label: string; pct: number; sub: string }) {
  const color = pct > 85 ? "var(--bad)" : pct > 65 ? "var(--warn)" : "var(--brand)";
  return (
    <div className="flex flex-col items-center gap-2">
      <Ring pct={pct} size={78} stroke={7} color={color}>
        <span className="font-extrabold text-sm">{Math.round(pct)}%</span>
      </Ring>
      <div className="text-center">
        <div className="text-sm font-semibold">{label}</div>
        <div className="text-muted text-[11px]">{sub}</div>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="card p-5 flex items-center gap-5">
        <Skeleton className="rounded-full shrink-0" style={{ width: 86, height: 86 }} />
        <div className="flex-1 space-y-2.5">
          <Skeleton style={{ height: 24, width: 200 }} />
          <Skeleton style={{ height: 14, width: 260 }} />
          <Skeleton style={{ height: 8, width: "60%" }} />
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="card p-4 space-y-2.5">
            <Skeleton style={{ height: 11, width: 80 }} />
            <Skeleton style={{ height: 28, width: 48 }} />
            <Skeleton style={{ height: 11, width: 90 }} />
          </div>
        ))}
      </div>
      <div className="card p-5">
        <Skeleton style={{ height: 16, width: 140 }} className="mb-5" />
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-2.5">
              <Skeleton className="rounded-full" style={{ width: 78, height: 78 }} />
              <Skeleton style={{ height: 12, width: 64 }} />
            </div>
          ))}
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <Skeleton style={{ height: 170 }} />
        <Skeleton style={{ height: 170 }} />
      </div>
    </div>
  );
}
