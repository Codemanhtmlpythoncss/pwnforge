import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Diff, Spinner, Empty } from "../ui";

const DIFFS = ["", "beginner", "easy", "intermediate", "hard", "advanced", "expert", "mastery"];

export default function Courses() {
  const [data, setData] = useState<any>(null);
  const [q, setQ] = useState("");
  const [diff, setDiff] = useState("");
  const [cat, setCat] = useState("");
  const [cats, setCats] = useState<string[]>([]);

  const load = () => {
    const p = new URLSearchParams({ limit: "60" });
    if (q) p.set("q", q);
    if (diff) p.set("difficulty", diff);
    if (cat) p.set("category", cat);
    api.get(`/api/courses?${p}`).then(setData);
  };
  useEffect(() => { load(); }, [q, diff, cat]);
  useEffect(() => {
    api.get("/api/courses?limit=200").then(d =>
      setCats([...new Set<string>(d.items.map((c: any) => c.category))].sort()));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Course Catalogue</h1>
        <div className="text-muted text-sm mt-1">{data?.total ?? "…"} courses across all disciplines</div>
      </div>
      <div className="flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Search courses…" value={q} onChange={e => setQ(e.target.value)} />
        <select className="input max-w-[180px]" value={diff} onChange={e => setDiff(e.target.value)}>
          {DIFFS.map(d => <option key={d} value={d}>{d || "All difficulties"}</option>)}
        </select>
        <select className="input max-w-[200px]" value={cat} onChange={e => setCat(e.target.value)}>
          <option value="">All categories</option>
          {cats.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      {!data ? <Spinner /> : data.items.length === 0 ? <Empty msg="No courses match." /> : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((c: any) => (
            <Link key={c.id} to={`/courses/${c.id}`} className="card p-4 hover:ring-1 hover:ring-brand flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <Diff d={c.difficulty} />
                <span className="text-muted text-xs">{c.estimated_minutes}m</span>
              </div>
              <div className="font-semibold">{c.title}</div>
              <div className="text-muted text-sm mt-1 flex-1 line-clamp-3">{c.description}</div>
              <div className="flex flex-wrap gap-1 mt-3">
                {c.tags.slice(0, 3).map((t: string) => <span key={t} className="tag">{t}</span>)}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
