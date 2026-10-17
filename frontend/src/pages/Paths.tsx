import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Diff, Spinner } from "../ui";

export default function Paths() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.get("/api/paths").then(r => { setItems(r.items); setLoading(false); }); }, []);
  if (loading) return <Spinner />;
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-bold">Learning Paths</h1>
        <div className="text-muted text-sm mt-1">Structured beginner-to-expert progressions</div></div>
      <div className="grid md:grid-cols-2 gap-4">
        {items.map(p => (
          <Link key={p.id} to={`/paths/${p.id}`} className="card p-5 hover:ring-1 hover:ring-brand">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-lg">{p.title}</span>
              <span className="text-muted text-sm">{p.step_count} steps</span>
            </div>
            <p className="text-muted text-sm">{p.description}</p>
            <div className="flex items-center gap-2 mt-3">
              <Diff d={p.difficulty_min} /> <span className="text-muted">→</span> <Diff d={p.difficulty_max} />
              {p.specialization && <span className="tag ml-auto">{p.specialization}</span>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
