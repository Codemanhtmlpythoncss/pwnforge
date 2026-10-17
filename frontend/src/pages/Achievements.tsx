import { useEffect, useState } from "react";
import { api } from "../api";
import { Spinner } from "../ui";

export default function Achievements() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { api.get("/api/achievements").then(r => { setItems(r.items); setLoading(false); }); }, []);
  if (loading) return <Spinner />;
  const earned = items.filter(a => a.earned).length;
  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-bold">Achievements</h1>
        <div className="text-muted text-sm mt-1">{earned}/{items.length} unlocked</div></div>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(a => (
          <div key={a.key} className={`card p-4 flex gap-3 ${a.earned ? "" : "opacity-55"}`}>
            <div className={`w-11 h-11 grid place-items-center rounded-xl text-xl ${a.earned ? "bg-brand text-black" : "bg-panel2"}`}>★</div>
            <div className="flex-1">
              <div className="font-semibold">{a.title}</div>
              <div className="text-muted text-sm">{a.description}</div>
              <div className="text-xs text-muted mt-1">
                {a.earned ? `Unlocked ${new Date(a.awarded_at).toLocaleDateString()}` : `${a.points} pts · ${a.category}`}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
