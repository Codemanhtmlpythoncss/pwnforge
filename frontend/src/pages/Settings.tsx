import { useEffect, useState } from "react";
import { api } from "../api";
import { Panel, Spinner } from "../ui";

export default function Settings() {
  const [items, setItems] = useState<any[]>([]);
  const [edited, setEdited] = useState<Record<string, any>>({});
  const [saved, setSaved] = useState("");
  const load = () => api.get("/api/settings").then(r => setItems(r.items));
  useEffect(() => { load(); }, []);
  if (!items.length) return <Spinner />;

  const groups: Record<string, any[]> = {};
  items.forEach(s => { (groups[s.category] ||= []).push(s); });

  const save = async (s: any) => {
    const v = edited[s.key] ?? s.value;
    setSaved("");
    try { await api.put(`/api/settings/${s.key}`, { value: v }); setSaved(`Saved ${s.key}`); load(); }
    catch (e: any) { setSaved(e.message); }
  };

  return (
    <div className="space-y-5">
      <div><h1 className="text-2xl font-bold">Settings</h1>
        <div className="text-muted text-sm mt-1">Every setting has a real backend effect. RAM and limits are live-configurable.</div></div>
      {saved && <div className="text-sm text-brand">{saved}</div>}
      {Object.entries(groups).map(([cat, list]) => (
        <Panel key={cat}>
          <div className="font-semibold capitalize mb-3">{cat}</div>
          <div className="space-y-3">
            {list.map(s => (
              <div key={s.key} className="flex items-start gap-4">
                <div className="flex-1">
                  <div className="text-sm font-medium font-mono">{s.key}</div>
                  <div className="text-muted text-xs">{s.description}</div>
                </div>
                <div className="w-48">
                  {s.type === "bool" ? (
                    <select className="input" value={String(edited[s.key] ?? s.value)}
                      onChange={e => setEdited({ ...edited, [s.key]: e.target.value === "true" })}>
                      <option value="true">true</option><option value="false">false</option>
                    </select>
                  ) : (
                    <input className="input" value={String(edited[s.key] ?? s.value)}
                      onChange={e => setEdited({ ...edited, [s.key]: e.target.value })} />
                  )}
                </div>
                <button className="btn text-sm" onClick={() => save(s)}>Save</button>
              </div>
            ))}
          </div>
        </Panel>
      ))}
    </div>
  );
}
