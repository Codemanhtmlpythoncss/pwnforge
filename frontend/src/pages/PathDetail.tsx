import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { Bar, Diff, Panel, Spinner } from "../ui";

export default function PathDetail() {
  const { id } = useParams();
  const [p, setP] = useState<any>(null);
  useEffect(() => { api.get(`/api/paths/${id}`).then(setP); }, [id]);
  if (!p) return <Spinner />;
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">{p.title}</h1>
        <p className="text-muted mt-1 max-w-2xl">{p.description}</p>
      </div>
      {p.certificate && (
        <Panel className="border-brand">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="text-sm"><span className="text-xl mr-2">🎓</span>
              <span className="text-ok font-semibold">Path complete!</span> You've earned a certificate.</div>
            <Link to="/certificates" className="btn btn-primary text-sm">View certificate</Link>
          </div>
        </Panel>
      )}
      <Panel>
        <div className="flex justify-between text-sm mb-2">
          <span>{p.completed_steps}/{p.steps.length} steps complete</span><span>{p.percent}%</span>
        </div>
        <Bar pct={p.percent} />
      </Panel>
      <div className="space-y-2">
        {p.steps.map((s: any) => (
          <div key={s.order} className={`card p-4 flex items-center gap-4 ${s.locked ? "opacity-60" : ""}`}>
            <span className={`w-7 h-7 grid place-items-center rounded-full text-xs ${
              s.status === "completed" ? "bg-brand text-black" : "bg-panel2 text-muted"}`}>
              {s.status === "completed" ? "✓" : s.order}
            </span>
            <div className="flex-1">
              <div className="font-medium flex items-center gap-2">
                {s.title}
                {s.difficulty && <Diff d={s.difficulty} />}
                {!s.required && <span className="tag">optional</span>}
                {s.locked && <span className="tag text-warn">locked</span>}
              </div>
              {s.note && <div className="text-muted text-xs mt-0.5">{s.note}</div>}
            </div>
            {s.course_id && <Link to={`/courses/${s.course_id}`} className="btn btn-ghost text-sm">Open</Link>}
            {s.lab_id && <Link to="/labs" className="btn btn-ghost text-sm">Lab</Link>}
          </div>
        ))}
      </div>
    </div>
  );
}
