import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { Bar, Diff, Panel, Spinner } from "../ui";

export default function PathDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [p, setP] = useState<any>(null);
  const [startingLab, setStartingLab] = useState("");
  const [error, setError] = useState("");
  const load = () => api.get(`/api/paths/${id}`).then(setP);
  useEffect(() => { setP(null); load(); }, [id]);
  if (!p) return <Spinner />;

  const openStep = async (step: any) => {
    if (step.locked) return;
    if (step.course_id) {
      navigate(`/courses/${step.course_id}?path=${id}`);
      return;
    }
    if (!step.lab_id || startingLab) return;
    setError(""); setStartingLab(step.lab_id);
    try {
      const result = await api.post("/api/lab-instances", { lab_id: step.lab_id });
      navigate(`/labs/instance/${result.lab_instance_id}?path=${id}`);
    } catch (e: any) {
      setError(e?.message || "Could not start this lab. Please try again.");
    } finally {
      setStartingLab("");
    }
  };

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
          <span>{p.completed_required_steps}/{p.required_step_count} required steps complete</span><span>{p.percent}%</span>
        </div>
        <Bar pct={p.percent} />
      </Panel>
      {p.outcomes?.length > 0 && (
        <Panel>
          <div className="font-semibold mb-2">What you will be able to do</div>
          <ul className="list-disc pl-5 text-sm text-muted space-y-1">
            {p.outcomes.map((outcome: string, i: number) => <li key={i}>{outcome}</li>)}
          </ul>
        </Panel>
      )}
      {p.capstone && (
        <Panel className="border-brand">
          <div className="font-semibold">Final practical: {p.capstone.title}</div>
          <p className="text-sm text-muted mt-1">{p.capstone.scenario}</p>
          {p.capstone.success_criteria?.length > 0 && (
            <>
              <div className="text-sm font-medium mt-3 mb-1">You are ready when you can:</div>
              <ul className="list-disc pl-5 text-sm text-muted space-y-1">
                {p.capstone.success_criteria.map((criterion: string, i: number) => <li key={i}>{criterion}</li>)}
              </ul>
            </>
          )}
        </Panel>
      )}
      {p.next_step && (
        <Panel className="flex items-center justify-between gap-3 flex-wrap">
          <div className="text-sm"><span className="text-muted">Next in order:</span> <b>{p.next_step.title}</b></div>
          <button className="btn btn-primary text-sm" onClick={() => openStep(p.next_step)} disabled={p.next_step.locked || !!startingLab}>
            {startingLab === p.next_step.lab_id ? "Starting lab…" : p.next_step.lab_id ? "Start next lab" : "Continue course"}
          </button>
        </Panel>
      )}
      {error && <div className="text-bad text-sm">{error}</div>}
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
            {(s.course_id || s.lab_id) && (
              <button onClick={() => openStep(s)} disabled={s.locked || !!startingLab}
                className="btn btn-ghost text-sm disabled:cursor-not-allowed disabled:opacity-50">
                {startingLab === s.lab_id ? "Starting…" : s.lab_id ? (s.status === "completed" ? "Start again" : "Start lab") : "Open course"}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
