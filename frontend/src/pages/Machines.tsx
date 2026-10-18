import { useEffect, useState } from "react";
import { api } from "../api";
import { Diff, Spinner, Empty } from "../ui";
import { MachineAvatar } from "../logo";

const DIFFS = ["", "easy", "intermediate", "hard", "advanced", "expert"];
const PAGE = 24;

export default function Machines() {
  const [data, setData] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [q, setQ] = useState(""); const [diff, setDiff] = useState("");
  const [cat, setCat] = useState(""); const [osf, setOsf] = useState("");
  const [page, setPage] = useState(0);
  const [msg, setMsg] = useState("");

  const load = () => {
    const p = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE) });
    if (q) p.set("q", q); if (diff) p.set("difficulty", diff);
    if (cat) p.set("category", cat); if (osf) p.set("os_family", osf);
    api.get(`/api/profiles?${p}`).then(setData);
  };
  useEffect(() => { load(); }, [q, diff, cat, osf, page]);
  useEffect(() => { api.get("/api/profiles/stats").then(setStats); }, []);
  useEffect(() => { setPage(0); }, [q, diff, cat, osf]);

  const launch = async (pid: string) => {
    setMsg("");
    try {
      await api.post("/api/vms", { profile_id: pid });
      setMsg(`Launching ${pid}… see Labs / VMs for progress.`);
    } catch (e: any) { setMsg(e.message); }
  };

  const total = data?.total ?? 0;
  const pages = Math.ceil(total / PAGE);
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Machine Catalogue</h1>
        <div className="text-muted text-sm mt-1">
          {stats ? `${stats.total} distinct VM profiles` : "…"}
          {stats && ` · ${Object.keys(stats.by_category).length} categories`}
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Search by name/id…" value={q} onChange={e => setQ(e.target.value)} />
        <select className="input max-w-[160px]" value={diff} onChange={e => setDiff(e.target.value)}>
          {DIFFS.map(d => <option key={d} value={d}>{d || "All difficulties"}</option>)}
        </select>
        <select className="input max-w-[190px]" value={cat} onChange={e => setCat(e.target.value)}>
          <option value="">All categories</option>
          {stats && Object.keys(stats.by_category).sort().map((c: string) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select className="input max-w-[150px]" value={osf} onChange={e => setOsf(e.target.value)}>
          <option value="">All OS</option>
          {stats && Object.keys(stats.by_os_family).sort().map((c: string) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      {msg && <div className="text-sm text-brand">{msg}</div>}
      {!data ? <Spinner /> : data.items.length === 0 ? <Empty msg="No profiles match." /> : (
        <>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.items.map((p: any) => (
              <div key={p.id} className="card card-hover card-lift p-4 flex flex-col">
                <div className="flex items-start gap-3">
                  <MachineAvatar os={p.os_family} difficulty={p.difficulty} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <Diff d={p.difficulty} />
                      <span className={`tag ${p.readiness === "ready" ? "tag-green" : ""}`}>
                        {p.readiness === "ready" ? "● ready" : p.readiness}
                      </span>
                    </div>
                    <div className="font-semibold text-sm leading-snug mt-1.5">{p.name}</div>
                    <div className="text-muted text-[11px] mt-0.5 mono truncate">{p.id}</div>
                  </div>
                </div>
                <div className="text-muted text-xs mt-3 flex flex-wrap gap-x-3 gap-y-1">
                  <span>{p.os_family}</span><span>{p.vcpu} vCPU</span>
                  <span>{p.memory_mb} MB</span><span>{p.disk_gb} GB</span>
                </div>
                <div className="flex gap-2 mt-3">
                  <button className="btn btn-primary flex-1 text-sm"
                    disabled={p.readiness !== "ready"} onClick={() => launch(p.id)}>
                    ▸ Launch
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button className="btn" disabled={page === 0} onClick={() => setPage(page - 1)}>Prev</button>
            <span className="text-muted text-sm">Page {page + 1} / {pages || 1}</span>
            <button className="btn" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}
