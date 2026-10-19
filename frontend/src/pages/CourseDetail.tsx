import { useEffect, useState } from "react";
import { useParams, useSearchParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Bar, Diff, Markdown, Panel, Spinner } from "../ui";

export default function CourseDetail() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const pathId = params.get("path");
  const navigate = useNavigate();
  const [c, setC] = useState<any>(null);
  const [nextStep, setNextStep] = useState<any>(null);
  const [pathTitle, setPathTitle] = useState("");
  const load = () => api.get(`/api/courses/${id}`).then(setC);
  useEffect(() => { load(); }, [id]);

  // When arrived from a learning path, work out the next course so we can offer "Continue".
  useEffect(() => {
    setNextStep(null); setPathTitle("");
    if (!pathId) return;
    api.get(`/api/paths/${pathId}`).then(p => {
      setPathTitle(p.title || "");
      const steps = p.steps || [];
      const i = steps.findIndex((s: any) => s.course_id === id);
      const next = i >= 0 ? steps.slice(i + 1).find((s: any) => s.course_id) : null;
      setNextStep(next || null);
    }).catch(() => {});
  }, [pathId, id]);

  if (!c) return <Spinner />;

  const completed = c.progress?.status === "completed";
  const start = async () => { await api.post(`/api/courses/${id}/start`); load(); };
  const goNext = () => nextStep && navigate(`/courses/${nextStep.course_id}?path=${pathId}`);

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1"><Diff d={c.difficulty} />
            <span className="text-muted text-sm">{c.category} · {c.estimated_minutes}m</span></div>
          <h1 className="text-2xl font-bold">{c.title}</h1>
          <p className="text-muted mt-1 max-w-2xl">{c.description}</p>
        </div>
        <button className="btn btn-primary" onClick={start}>
          {completed ? "Revisit" : c.progress ? "Continue" : "Start course"}
        </button>
      </div>

      {pathId && (
        <Panel className={completed ? "border-brand" : ""}>
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="text-sm">
              <Link to={`/paths/${pathId}`} className="text-muted hover:text-brand">← {pathTitle || "Learning path"}</Link>
              <div className="mt-0.5">
                {completed
                  ? (nextStep ? <span className="text-ok">Course complete ✓ — ready for the next one.</span>
                              : <span className="text-ok">Course complete ✓ — that's the last course in this path!</span>)
                  : <span className="text-muted">Part of the <b>{pathTitle}</b> path. Finish it to continue.</span>}
              </div>
            </div>
            {completed && nextStep && (
              <button className="btn btn-primary text-sm" onClick={goNext}>
                Continue to {nextStep.title || "next course"} →
              </button>
            )}
          </div>
        </Panel>
      )}

      {c.progress && (
        <Panel>
          <div className="flex justify-between text-sm mb-2">
            <span>Progress</span><span>{Math.round(c.progress.percent)}%</span>
          </div>
          <Bar pct={c.progress.percent} />
        </Panel>
      )}

      {c.prerequisite_status && !c.prerequisite_status.met && (
        <div className="card p-3 border-l-4" style={{ borderLeftColor: "var(--warn)" }}>
          <div className="text-warn text-sm font-semibold">Prerequisites recommended</div>
          <div className="text-muted text-xs mt-1">
            Missing courses: {c.prerequisite_status.unmet_courses.join(", ") || "none"} ·
            competencies: {c.prerequisite_status.unmet_competencies.join(", ") || "none"}.
            You may still proceed.
          </div>
        </div>
      )}

      {c.objectives.length > 0 && (
        <Panel>
          <div className="font-semibold mb-2">Learning objectives</div>
          <ul className="list-disc pl-5 text-sm text-muted space-y-1">
            {c.objectives.map((o: string, i: number) => <li key={i}>{o}</li>)}
          </ul>
        </Panel>
      )}

      <div className="space-y-4">
        {c.lessons.map((l: any, i: number) => <Lesson key={l.id} lesson={l} n={i + 1} onDone={load} />)}
      </div>

      {c.assessments.map((a: any) => <Assessment key={a.id} a={a} onDone={load} />)}
    </div>
  );
}

function Lesson({ lesson, n, onDone }: { lesson: any; n: number; onDone: () => void }) {
  const [open, setOpen] = useState(n === 1);
  const [hints, setHints] = useState<string[]>([]);
  const [wt, setWt] = useState<any[] | null>(null);
  const [usedHints, setUsedHints] = useState(0);

  const revealHint = async () => {
    const r = await api.get(`/api/lessons/${lesson.id}/hint?index=${hints.length}`);
    setHints([...hints, r.text]); setUsedHints(hints.length + 1);
  };
  const revealWt = async () => {
    const r = await api.get(`/api/lessons/${lesson.id}/walkthrough`);
    setWt(r.steps);
  };
  const complete = async () => {
    await api.post(`/api/lessons/${lesson.id}/complete`,
      { hints_used: usedHints, walkthrough_opened: wt !== null });
    onDone();
  };

  const done = lesson.status === "completed";
  return (
    <div className="card overflow-hidden">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left">
        <div className="flex items-center gap-3">
          <span className={`w-6 h-6 grid place-items-center rounded-full text-xs ${done ? "bg-brand text-black" : "bg-panel2 text-muted"}`}>
            {done ? "✓" : n}
          </span>
          <span className="font-semibold">{lesson.title}</span>
          <Diff d={lesson.difficulty} />
        </div>
        <span className="text-muted text-sm">{lesson.estimated_minutes}m {open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 border-t border-line pt-4">
          <Markdown text={lesson.body} />

          {lesson.exercises.map((e: any) => <Exercise key={e.id} e={e} />)}

          <div className="flex flex-wrap gap-2 mt-4">
            {lesson.has_hints && (
              <button className="btn btn-ghost" onClick={revealHint} disabled={hints.length >= lesson.hint_count}>
                💡 Hint ({hints.length}/{lesson.hint_count}) <span className="text-muted">optional</span>
              </button>
            )}
            {lesson.has_walkthrough && !wt && (
              <button className="btn btn-ghost" onClick={revealWt}>📖 Show walkthrough <span className="text-muted">optional</span></button>
            )}
            <button className="btn btn-primary ml-auto" onClick={complete} disabled={done}>
              {done ? "Completed" : "Mark complete"}
            </button>
          </div>

          {hints.length > 0 && (
            <div className="mt-3 space-y-1">
              {hints.map((h, i) => <div key={i} className="text-sm text-warn bg-panel2 rounded p-2">💡 {h}</div>)}
            </div>
          )}
          {wt && (
            <div className="mt-3 card p-3 bg-panel2">
              <div className="font-semibold text-sm mb-2">Step-by-step walkthrough</div>
              <ol className="space-y-2 text-sm">
                {wt.map((s, i) => (
                  <li key={i}><span className="font-medium">{i + 1}. {s.title}</span>
                    <div className="text-muted">{s.detail}</div></li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Exercise({ e }: { e: any }) {
  const [answer, setAnswer] = useState("");
  const [res, setRes] = useState<any>(null);
  const [hints, setHints] = useState<string[]>([]);
  const submit = async () => setRes(await api.post(`/api/exercises/${e.id}/submit`, { answer }));
  const hint = async () => {
    const r = await api.get(`/api/exercises/${e.id}/hint?index=${hints.length}`);
    setHints([...hints, r.text]);
  };
  return (
    <div className="mt-4 card p-3 bg-panel2">
      <div className="text-sm font-medium mb-2">🧪 {e.prompt} <span className="text-muted">({e.points} pts)</span></div>
      {e.kind === "mcq" ? (
        <select className="input mb-2" value={answer} onChange={ev => setAnswer(ev.target.value)}>
          <option value="">Choose…</option>
          {e.choices.map((c: string) => <option key={c} value={c}>{c}</option>)}
        </select>
      ) : (
        <input className="input mb-2" value={answer} onChange={ev => setAnswer(ev.target.value)} placeholder="Your answer" />
      )}
      <div className="flex gap-2">
        <button className="btn" onClick={submit} disabled={!answer}>Submit</button>
        {e.has_hints && <button className="btn btn-ghost" onClick={hint}>💡 Hint</button>}
      </div>
      {hints.map((h, i) => <div key={i} className="text-xs text-warn mt-2">💡 {h}</div>)}
      {res && (
        <div className={`text-sm mt-2 ${res.correct ? "text-ok" : "text-bad"}`}>
          {res.correct ? "✓ Correct" : `✗ Not quite. ${res.explanation}`}
        </div>
      )}
    </div>
  );
}

function Assessment({ a, onDone }: { a: any; onDone: () => void }) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [hints, setHints] = useState<Record<string, string[]>>({});
  const [hintErrors, setHintErrors] = useState<Record<string, string>>({});
  const [loadingHint, setLoadingHint] = useState<string | null>(null);
  const [res, setRes] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const revealHint = async (q: any) => {
    const shown = hints[q.id] || [];
    if (!q.has_hints || shown.length >= q.hint_count || loadingHint) return;
    setLoadingHint(q.id);
    setHintErrors(current => ({ ...current, [q.id]: "" }));
    try {
      const result = await api.get(
        `/api/assessments/${a.id}/questions/${q.id}/hint?index=${shown.length}`
      );
      setHints(current => ({ ...current, [q.id]: [...(current[q.id] || []), result.text] }));
    } catch (error) {
      setHintErrors(current => ({
        ...current,
        [q.id]: error instanceof Error ? error.message : "Could not load hint.",
      }));
    } finally {
      setLoadingHint(null);
    }
  };
  const submit = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const r = await api.post(`/api/assessments/${a.id}/submit`, { answers });
      setRes(r); onDone();
    } finally {
      setSubmitting(false);
    }
  };
  return (
    <Panel>
      <div className="flex items-center justify-between mb-3">
        <div className="font-semibold">📋 {a.title}</div>
        <span className="text-muted text-sm">Pass ≥ {a.passing_score}%</span>
      </div>
      <div className="space-y-4">
        {a.questions.map((q: any, i: number) => (
          <div key={q.id} className="space-y-2">
            <div className="text-sm font-medium mb-1">{i + 1}. {q.prompt}</div>
            {q.kind === "mcq" ? (
              <div className="space-y-1">
                {q.choices.map((c: string) => (
                  <label key={c} className="flex items-center gap-2 text-sm">
                    <input type="radio" name={q.id} value={c} checked={answers[q.id] === c}
                      onChange={() => setAnswers(current => ({ ...current, [q.id]: c }))} />{c}
                  </label>
                ))}
              </div>
            ) : (
              <input className="input" placeholder="Answer" value={answers[q.id] || ""}
                onChange={e => setAnswers(current => ({ ...current, [q.id]: e.target.value }))} />
            )}
            {q.has_hints && (
              <button className="btn btn-ghost" onClick={() => revealHint(q)}
                disabled={loadingHint !== null || (hints[q.id] || []).length >= q.hint_count}>
                💡 Hint ({(hints[q.id] || []).length}/{q.hint_count}) <span className="text-muted">optional</span>
              </button>
            )}
            {(hints[q.id] || []).map((hint, hintIndex) => (
              <div key={hintIndex} className="text-sm text-warn bg-panel2 rounded p-2">💡 {hint}</div>
            ))}
            {hintErrors[q.id] && <div className="text-sm text-bad">{hintErrors[q.id]}</div>}
          </div>
        ))}
      </div>
      <button className="btn btn-primary mt-4" onClick={submit} disabled={submitting}>
        {submitting ? "Submitting…" : "Submit assessment"}
      </button>
      {res && (
        <div className={`mt-3 text-sm font-semibold ${res.passed ? "text-ok" : "text-bad"}`}>
          Score {res.score}% — {res.passed ? "passed ✓" : "not passed"}
        </div>
      )}
    </Panel>
  );
}
