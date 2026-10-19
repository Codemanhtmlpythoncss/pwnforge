import { useEffect, useState } from "react";
import { api } from "../api";
import { Panel, Spinner } from "../ui";

function Updates() {
  const [v, setV] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api.get("/api/admin/version").then(setV).catch(() => {});
  useEffect(() => { load(); }, []);

  const update = async () => {
    setMsg(""); setBusy(true);
    try {
      const { job_id } = await api.post("/api/admin/update");
      setMsg("Updating… (the service restarts when it's done)");
      for (let i = 0; i < 400; i++) {
        await new Promise(r => setTimeout(r, 2000));
        let j;
        try { j = await api.get(`/api/jobs/${job_id}`); } catch { setMsg("Update finished (the server restarted). Reload the page."); break; }
        if (j.status === "succeeded") { setMsg("Update complete. Reload the page."); break; }
        if (j.status === "failed") { setMsg(j.error || "Update failed."); break; }
      }
    } catch (e: any) { setMsg(e.message); }
    finally { setBusy(false); load(); }
  };

  if (!v) return null;
  return (
    <Panel>
      <div className="font-semibold mb-2">Updates</div>
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex-1 min-w-[12rem]">
          <div className="text-sm">PwnForge <span className="font-mono">v{v.version}</span>
            {v.commit && <span className="text-muted font-mono"> · {v.branch ? v.branch + "@" : ""}{v.commit}</span>}</div>
          <div className="text-muted text-xs mt-1">
            {v.update_enabled
              ? "Updates PwnForge on this server (pull, reinstall, migrate, rebuild) and restarts it."
              : "Updates are managed by the host (the nodeyard dashboard's PwnForge page, or re-running the installer). Set admin.update_command below to enable this button."}
          </div>
        </div>
        <button className="btn btn-primary text-sm" disabled={!v.update_enabled || busy} onClick={update}>
          {busy ? "Updating…" : "Update PwnForge"}
        </button>
      </div>
      {msg && <div className="text-sm text-brand mt-2">{msg}</div>}
    </Panel>
  );
}

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
      <Updates />
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
