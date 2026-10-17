import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Diff, Panel, Spinner } from "../ui";

export default function Labs() {
  const [labs, setLabs] = useState<any[]>([]);
  const [instances, setInstances] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const nav = useNavigate();

  const load = () => Promise.all([
    api.get("/api/labs"), api.get("/api/lab-instances"),
  ]).then(([l, i]) => { setLabs(l.items); setInstances(i.items); setLoading(false); });
  useEffect(() => { load(); const t = setInterval(load, 3000); return () => clearInterval(t); }, []);

  const start = async (labId: string) => {
    setMsg("");
    try { const r = await api.post("/api/lab-instances", { lab_id: labId }); setMsg(`Starting ${labId}…`); load(); }
    catch (e: any) { setMsg(e.message); }
  };
  const stop = async (id: string) => { await api.post(`/api/lab-instances/${id}/stop`); load(); };
  const del = async (id: string) => { await api.del(`/api/lab-instances/${id}`); load(); };

  if (loading) return <Spinner />;
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold">Labs</h1>
        <div className="text-muted text-sm mt-1">Multi-machine environments on isolated networks</div></div>
      {msg && <div className="text-sm text-brand">{msg}</div>}

      {instances.length > 0 && (
        <div>
          <div className="font-semibold mb-2">Active lab instances</div>
          <div className="space-y-3">
            {instances.map(li => (
              <Panel key={li.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{li.lab_id}</span>
                    <span className={`tag ml-2 ${li.status === "running" ? "text-ok" : li.status === "error" ? "text-bad" : ""}`}>{li.status}</span>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/labs/instance/${li.id}`} className="btn btn-primary text-sm">Open workspace</Link>
                    <button className="btn text-sm" onClick={() => stop(li.id)}>Stop</button>
                    <button className="btn btn-ghost text-sm" onClick={() => del(li.id)}>Delete</button>
                  </div>
                </div>
                {li.last_error && <div className="text-bad text-xs mt-2">{li.last_error}</div>}
                <div className="flex flex-wrap gap-2 mt-2">
                  {li.machines.map((m: any) => (
                    <span key={m.id} className="tag">{m.name.split("-").pop()}: {m.status} {m.ip_address || ""}</span>
                  ))}
                </div>
              </Panel>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="font-semibold mb-2">Lab catalogue</div>
        <div className="grid md:grid-cols-2 gap-4">
          {labs.map(l => (
            <Panel key={l.id}>
              <div className="flex items-center justify-between mb-1">
                <Diff d={l.difficulty} />
                <span className="text-muted text-xs">{l.machine_count} machines · {l.estimated_minutes}m</span>
              </div>
              <div className="font-semibold">{l.title}</div>
              <p className="text-muted text-sm mt-1">{l.description}</p>
              <button className="btn btn-primary mt-3 text-sm" onClick={() => start(l.id)}>Start lab</button>
            </Panel>
          ))}
        </div>
      </div>
    </div>
  );
}
