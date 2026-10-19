import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Panel, Spinner, Empty } from "../ui";

type VM = {
  id: string; name: string; profile_id: string; status: string; driver: string;
  ip_address: string | null; vcpu: number; memory_mb: number; simulated: boolean;
  lab_instance_id: string | null; last_error: string | null;
};
type Lab = { id: string; lab_id: string; status: string; last_error: string | null; machines: VM[] };

const RUNNING = new Set(["running", "starting", "creating"]);
const chipClass = (s: string) =>
  s === "running" ? "tag tag-green" : s === "error" ? "tag text-bad"
    : RUNNING.has(s) ? "tag text-warn" : "tag";

export default function Running() {
  const [vms, setVms] = useState<VM[] | null>(null);
  const [labs, setLabs] = useState<Lab[]>([]);
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const [msg, setMsg] = useState("");
  const timer = useRef<any>(null);

  const load = async () => {
    try {
      const [v, l] = await Promise.all([api.get("/api/vms"), api.get("/api/lab-instances")]);
      setVms(v.items);
      setLabs(l.items);
    } catch (e: any) { setMsg(e.message); }
  };
  useEffect(() => {
    load();
    // Poll only while the tab is visible; refresh at once when it comes back.
    timer.current = setInterval(() => { if (!document.hidden) load(); }, 4000);
    const onVis = () => { if (!document.hidden) load(); };
    document.addEventListener("visibilitychange", onVis);
    return () => { clearInterval(timer.current); document.removeEventListener("visibilitychange", onVis); };
  }, []);

  const act = async (key: string, fn: () => Promise<any>, note = "") => {
    setBusy(b => ({ ...b, [key]: true })); setMsg("");
    try { await fn(); if (note) setMsg(note); await load(); }
    catch (e: any) { setMsg(e.message); }
    finally { setBusy(b => ({ ...b, [key]: false })); }
  };

  const standalone = (vms || []).filter(v => !v.lab_instance_id);
  const runningVms = (vms || []).filter(v => RUNNING.has(v.status));
  const runningLabs = labs.filter(l => RUNNING.has(l.status));
  const runningCount = runningVms.length;

  const stopAll = () => act("all", async () => {
    for (const l of runningLabs) await api.post(`/api/lab-instances/${l.id}/stop`).catch(() => {});
    for (const v of runningVms.filter(v => !v.lab_instance_id)) await api.post(`/api/vms/${v.id}/stop`).catch(() => {});
  }, "Stopping everything that's running…");

  if (vms === null) return <Spinner />;

  const vmRow = (v: VM) => (
    <div key={v.id} className="flex items-center gap-3 py-2.5 border-b border-line last:border-0">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">{v.name.includes("-") ? v.name.split("-").slice(1).join("-") : v.name}</span>
          <span className={chipClass(v.status)}>{v.status}</span>
          {v.simulated && <span className="tag">simulated</span>}
        </div>
        <div className="text-muted text-[11px] mono mt-0.5">
          {v.profile_id} · {v.vcpu} vCPU · {v.memory_mb} MB{v.ip_address ? ` · ${v.ip_address}` : ""}
        </div>
        {v.last_error && <div className="text-bad text-xs mt-0.5">{v.last_error}</div>}
      </div>
      <div className="flex gap-2 shrink-0">
        {RUNNING.has(v.status)
          ? <button className="btn text-xs" disabled={busy[v.id]} onClick={() => act(v.id, () => api.post(`/api/vms/${v.id}/stop`))}>Stop</button>
          : <button className="btn text-xs" disabled={busy[v.id]} onClick={() => act(v.id, () => api.post(`/api/vms/${v.id}/reset`), "Starting…")}>Start</button>}
        {v.status === "running" && <button className="btn text-xs" disabled={busy[v.id]} onClick={() => act(v.id, () => api.post(`/api/vms/${v.id}/reboot`))}>Reboot</button>}
        <button className="btn btn-danger text-xs" disabled={busy[v.id]} onClick={() => act(v.id, () => api.del(`/api/vms/${v.id}`))}>Delete</button>
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold">Running</h1>
          <div className="text-muted text-sm mt-1">
            Your active machines and labs. {runningCount} machine{runningCount === 1 ? "" : "s"} running.
          </div>
        </div>
        <button className="btn btn-danger text-sm" disabled={busy.all || (!runningVms.length && !runningLabs.length)} onClick={stopAll}>
          {busy.all ? "Stopping…" : "Stop all running"}
        </button>
      </div>
      {msg && <div className="text-sm text-brand">{msg}</div>}

      <Panel>
        <div className="font-semibold mb-1">Labs</div>
        {!labs.length ? <Empty msg="No lab instances. Start one from Labs." /> : (
          <div>
            {labs.map(l => (
              <div key={l.id} className="py-3 border-b border-line last:border-0">
                <div className="flex items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Link to={`/labs/instance/${l.id}`} className="font-medium text-sm hover:text-brand truncate">{l.lab_id}</Link>
                      <span className={chipClass(l.status)}>{l.status}</span>
                      <span className="text-muted text-[11px]">{l.machines.length} machine{l.machines.length === 1 ? "" : "s"}</span>
                    </div>
                    {l.last_error && <div className="text-bad text-xs mt-0.5">{l.last_error}</div>}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {RUNNING.has(l.status) && <button className="btn text-xs" disabled={busy[l.id]} onClick={() => act(l.id, () => api.post(`/api/lab-instances/${l.id}/stop`))}>Stop</button>}
                    <button className="btn btn-danger text-xs" disabled={busy[l.id]} onClick={() => act(l.id, () => api.del(`/api/lab-instances/${l.id}`))}>Delete</button>
                  </div>
                </div>
                {l.machines.length > 0 && (
                  <div className="mt-1 ml-3 pl-3 border-l border-line">
                    {l.machines.map(m => (
                      <div key={m.id} className="text-muted text-[11px] mono py-0.5 flex items-center gap-2">
                        <span className={chipClass(m.status)} style={{ fontSize: "10px" }}>{m.status}</span>
                        {m.name.includes("-") ? m.name.split("-").slice(1).join("-") : m.name}{m.ip_address ? ` · ${m.ip_address}` : ""}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel>
        <div className="font-semibold mb-1">Standalone machines</div>
        {!standalone.length ? <Empty msg="No standalone machines. Launch one from Machines." /> : standalone.map(vmRow)}
      </Panel>
    </div>
  );
}
