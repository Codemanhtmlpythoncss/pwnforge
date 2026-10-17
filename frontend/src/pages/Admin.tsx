import { useEffect, useState } from "react";
import { api } from "../api";
import { Panel, Spinner } from "../ui";

export default function Admin() {
  const [tab, setTab] = useState("overview");
  const tabs = ["overview", "images", "storage", "users", "audit"];
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Administration</h1>
      <div className="flex gap-2">
        {tabs.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`btn ${tab === t ? "btn-primary" : "btn-ghost"} capitalize text-sm`}>{t}</button>
        ))}
      </div>
      {tab === "overview" && <Overview />}
      {tab === "images" && <Images />}
      {tab === "storage" && <Storage />}
      {tab === "users" && <Users />}
      {tab === "audit" && <Audit />}
    </div>
  );
}

function Overview() {
  const [d, setD] = useState<any>(null);
  const [caps, setCaps] = useState<any>(null);
  const [recon, setRecon] = useState("");
  useEffect(() => {
    api.get("/api/admin/diagnostics").then(setD);
    api.get("/api/host/capabilities").then(setCaps);
  }, []);
  if (!d || !caps) return <Spinner />;
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <Panel>
        <div className="font-semibold mb-2">Virtualisation backend</div>
        <div className="text-sm space-y-1">
          <Row k="Driver" v={caps.driver} />
          <Row k="Platform / arch" v={`${caps.platform} / ${caps.arch}`} />
          <Row k="Real virtualization" v={caps.real_virtualization ? "yes" : "no (simulated)"} />
          <Row k="HW acceleration" v={caps.hardware_acceleration ? "yes" : "no"} />
          <Row k="CPUs / RAM" v={`${caps.cpu_count} / ${Math.round(caps.total_memory_mb/1024)}GB`} />
        </div>
        {caps.notes.map((n: string, i: number) => <div key={i} className="text-muted text-xs mt-2">• {n}</div>)}
        <button className="btn mt-3 text-sm" onClick={async () => setRecon(JSON.stringify(await api.post("/api/admin/reconcile")))}>
          Reconcile VM state
        </button>
        {recon && <div className="text-muted text-xs mt-2">{recon}</div>}
      </Panel>
      <Panel>
        <div className="font-semibold mb-2">Counts</div>
        <div className="text-sm space-y-1">
          {Object.entries(d.counts).map(([k, v]) => <Row key={k} k={k} v={String(v)} />)}
        </div>
        <div className="font-semibold mt-3 mb-1 text-sm">Image chain</div>
        <div className="text-xs text-muted">{d.image_chain_problems.length ? d.image_chain_problems.join("; ") : "no problems"}</div>
      </Panel>
    </div>
  );
}

function Images() {
  const [d, setD] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const load = () => api.get("/api/images").then(setD);
  useEffect(() => { load(); }, []);
  if (!d) return <Spinner />;
  const act = async (fn: Promise<any>, ok: string) => {
    setMsg(""); try { await fn; setMsg(ok); load(); } catch (e: any) { setMsg(e.message); }
  };
  return (
    <Panel>
      <div className="flex justify-between mb-2">
        <div className="font-semibold">Base images</div>
        <div className="text-muted text-sm">{d.summary.present}/{d.summary.total_images} present</div>
      </div>
      {msg && <div className="text-sm text-brand mb-2">{msg}</div>}
      <table className="w-full text-sm">
        <thead><tr className="text-muted text-left text-xs">
          <th className="py-1">Key</th><th>OS</th><th>Status</th><th>Virt/Actual</th><th></th></tr></thead>
        <tbody>
          {d.items.map((i: any) => (
            <tr key={i.key} className="border-t border-line">
              <td className="py-2 font-mono text-xs">{i.key}</td>
              <td>{i.os_family} {i.os_version}</td>
              <td><span className={`tag ${i.status === "present" ? "text-ok" : ""}`}>{i.status}</span></td>
              <td className="text-muted text-xs">{i.virtual_gb}G / {i.actual_gb}G</td>
              <td className="text-right">
                <button className="btn btn-ghost text-xs" onClick={() => act(api.post(`/api/images/${i.key}/fetch`), "Fetch queued (runs on host only)")}>Fetch</button>
                <button className="btn btn-ghost text-xs" onClick={() => act(api.post(`/api/images/${i.key}/verify`), "Verified")}>Verify</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-muted text-xs mt-3">
        Fetching downloads large images on the host only when invoked. Nothing is downloaded automatically.
      </div>
    </Panel>
  );
}

function Storage() {
  const [d, setD] = useState<any>(null);
  const [clean, setClean] = useState<any>(null);
  useEffect(() => { api.get("/api/storage/report").then(setD); }, []);
  if (!d) return <Spinner />;
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <Panel>
        <div className="font-semibold mb-2">Physical storage</div>
        <div className="text-sm space-y-1">
          <Row k="Data dir" v={d.physical.data_dir} />
          <Row k="Free / total" v={`${d.physical.free_gb}G / ${d.physical.total_gb}G`} />
          <Row k="Low space" v={d.physical.low_space_warning ? "⚠ yes" : "no"} />
        </div>
      </Panel>
      <Panel>
        <div className="font-semibold mb-2">Images & overlays</div>
        <div className="text-sm space-y-1">
          <Row k="Images actual" v={`${d.images.actual_gb}G`} />
          <Row k="Images virtual" v={`${d.images.virtual_gb}G`} />
          <Row k="Overlays" v={`${d.overlays.actual_gb}G`} />
        </div>
        <div className="text-muted text-xs mt-2">{d.savings_note}</div>
        <button className="btn mt-3 text-sm" onClick={async () => setClean(await api.post("/api/storage/cleanup?dry_run=true"))}>
          Cleanup (dry run)
        </button>
        {clean && <div className="text-muted text-xs mt-2">{clean.candidates.length} orphan overlays found.</div>}
      </Panel>
    </div>
  );
}

function Users() {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState({ username: "", password: "", role: "learner" });
  const [msg, setMsg] = useState("");
  const load = () => api.get("/api/users").then(r => setItems(r.items));
  useEffect(() => { load(); }, []);
  const create = async () => {
    setMsg("");
    try { await api.post("/api/users", form); setForm({ username: "", password: "", role: "learner" }); load(); setMsg("Created"); }
    catch (e: any) { setMsg(e.message); }
  };
  return (
    <Panel>
      <div className="font-semibold mb-3">Users</div>
      <div className="flex flex-wrap gap-2 mb-3">
        <input className="input max-w-[160px]" placeholder="username" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} />
        <input className="input max-w-[160px]" type="password" placeholder="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
        <select className="input max-w-[150px]" value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
          {["learner", "instructor", "viewer", "administrator"].map(r => <option key={r}>{r}</option>)}
        </select>
        <button className="btn btn-primary" onClick={create}>Add user</button>
      </div>
      {msg && <div className="text-sm text-brand mb-2">{msg}</div>}
      <table className="w-full text-sm">
        <thead><tr className="text-muted text-left text-xs"><th className="py-1">User</th><th>Role</th><th>XP</th><th>Active</th></tr></thead>
        <tbody>
          {items.map(u => (
            <tr key={u.id} className="border-t border-line">
              <td className="py-2">{u.username}</td><td><span className="tag">{u.role}</span></td>
              <td>{u.xp}</td><td>{u.is_active ? "✓" : "✗"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

function Audit() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { api.get("/api/audit?limit=80").then(r => setItems(r.items)); }, []);
  return (
    <Panel>
      <div className="font-semibold mb-3">Audit log</div>
      <div className="space-y-1 text-sm max-h-[500px] overflow-y-auto">
        {items.map(e => (
          <div key={e.id} className="flex justify-between border-b border-line py-1">
            <span><span className="font-mono text-xs text-brand">{e.action}</span> {e.target_id || ""}</span>
            <span className="text-muted text-xs">{new Date(e.at).toLocaleString()} · {e.ip || "-"}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return <div className="flex justify-between"><span className="text-muted">{k}</span><span className="font-mono text-xs">{v}</span></div>;
}
