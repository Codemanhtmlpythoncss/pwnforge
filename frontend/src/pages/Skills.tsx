import { useEffect, useState } from "react";
import { api } from "../api";
import { Panel, Spinner } from "../ui";

const LEVELS = ["Not started", "Beginner", "Easy", "Intermediate", "Advanced"];
const COLORS = ["var(--line)", "#3b82f6", "var(--brand2)", "var(--warn)", "var(--brand)"];

export default function Skills() {
  const [d, setD] = useState<any>(null);
  useEffect(() => { api.get("/api/skills").then(setD); }, []);
  if (!d) return <Spinner />;
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-bold">Skills</h1>
        <div className="text-muted text-sm mt-1">Demonstrated competencies (mastery ≥ level {d.mastery_threshold})</div></div>
      <div className="grid md:grid-cols-2 gap-4">
        {d.domains.map((dom: any) => (
          <Panel key={dom.domain}>
            <div className="flex items-center justify-between mb-3">
              <span className="font-semibold capitalize">{dom.domain}</span>
              <span className="text-muted text-sm">{dom.mastered} mastered · {dom.in_progress} in progress</span>
            </div>
            <div className="space-y-2">
              {dom.competencies.map((c: any) => (
                <div key={c.key} className="flex items-center gap-3">
                  <span className="text-sm flex-1">{c.name}</span>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4].map(lv => (
                      <span key={lv} className="w-5 h-2 rounded-full"
                        style={{ background: c.level >= lv ? COLORS[c.level] : "var(--panel2)" }} />
                    ))}
                  </div>
                  <span className="text-muted text-xs w-20 text-right">{LEVELS[c.level]}</span>
                </div>
              ))}
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
