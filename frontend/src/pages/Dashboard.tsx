import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Bar, Diff, Panel, Spinner, Stat } from "../ui";

export default function Dashboard() {
  const [d, setD] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  useEffect(() => {
    api.get("/api/dashboard").then(setD);
    api.get("/api/recommendations?limit=4").then(r => setRecs(r.items));
  }, []);
  if (!d) return <Spinner />;
  const h = d.host;
  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <div className="text-muted text-sm mt-1">
            Current level <Diff d={d.level} /> · {d.courses_completed}/{d.courses_total} courses complete
          </div>
        </div>
        {d.gamification && (
          <div className="text-right">
            <div className="text-3xl font-extrabold text-brand">{d.xp} XP</div>
            {d.show_streak && <div className="text-muted text-xs">{d.streak_days}-day streak</div>}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Courses done" value={d.courses_completed} sub={`${d.courses_in_progress} in progress`} />
        <Stat label="Profiles" value={d.profiles_available} sub="catalogue" />
        <Stat label="Running VMs" value={d.running_vms} sub={`${d.active_labs} active labs`} />
        <Stat label="VM failures" value={d.vm_failures} sub="recent errors" />
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <Panel>
          <div className="text-xs uppercase text-muted mb-2">CPU</div>
          <div className="text-2xl font-bold">{h.cpu.percent}%</div>
          <Bar pct={h.cpu.percent} />
          <div className="text-muted text-xs mt-1">{h.cpu.cores_logical} logical cores</div>
        </Panel>
        <Panel>
          <div className="text-xs uppercase text-muted mb-2">Memory</div>
          <div className="text-2xl font-bold">{h.memory.percent}%</div>
          <Bar pct={h.memory.percent} />
          <div className="text-muted text-xs mt-1">
            {Math.round(h.memory.used_mb / 1024)}GB / {Math.round(h.memory.total_mb / 1024)}GB used
          </div>
        </Panel>
        <Panel>
          <div className="text-xs uppercase text-muted mb-2">Storage ({h.storage.path.split("/").pop()})</div>
          <div className="text-2xl font-bold">{h.storage.percent}%</div>
          <Bar pct={h.storage.percent} />
          <div className="text-muted text-xs mt-1">{h.storage.free_gb}GB free of {h.storage.total_gb}GB (physical)</div>
        </Panel>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Panel>
          <div className="font-semibold mb-3">Recommended next</div>
          <div className="space-y-2">
            {recs.map(r => (
              <Link key={r.course.id} to={`/courses/${r.course.id}`}
                className="block p-3 rounded-lg bg-panel2 hover:ring-1 hover:ring-brand">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{r.course.title}</span>
                  <Diff d={r.course.difficulty} />
                </div>
                <div className="text-muted text-xs mt-1">{r.reasons.join(" · ")}</div>
              </Link>
            ))}
            {recs.length === 0 && <div className="text-muted text-sm">Start a course to get recommendations.</div>}
          </div>
        </Panel>
        <Panel>
          <div className="font-semibold mb-3">Recent activity</div>
          <div className="space-y-1 text-sm">
            {d.recent_activity.map((a: any, i: number) => (
              <div key={i} className="flex justify-between text-muted">
                <span>{a.action}</span>
                <span className="text-xs">{new Date(a.at).toLocaleString()}</span>
              </div>
            ))}
            {d.recent_activity.length === 0 && <div className="text-muted">No activity yet.</div>}
          </div>
          {d.recent_achievements.length > 0 && (
            <div className="mt-4">
              <div className="font-semibold mb-2 text-sm">Recent achievements</div>
              <div className="flex flex-wrap gap-2">
                {d.recent_achievements.map((a: any) => <span key={a.key} className="tag">★ {a.key}</span>)}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
