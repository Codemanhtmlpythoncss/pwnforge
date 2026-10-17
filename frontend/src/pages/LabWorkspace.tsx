import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { api, wsUrl } from "../api";
import { Panel, Spinner } from "../ui";

export default function LabWorkspace() {
  const { id } = useParams();
  const [li, setLi] = useState<any>(null);
  const [labId, setLabId] = useState("");
  const [active, setActive] = useState<string | null>(null);
  const [flag, setFlag] = useState("");
  const [flagMsg, setFlagMsg] = useState("");

  const load = () => api.get("/api/lab-instances").then(r => {
    const found = r.items.find((x: any) => x.id === id);
    setLi(found); setLabId(found?.lab_id || "");
    if (found && !active && found.machines[0]) setActive(found.machines[0].id);
  });
  useEffect(() => { load(); const t = setInterval(load, 4000); return () => clearInterval(t); }, [id]);

  const submitFlag = async () => {
    setFlagMsg("");
    const r = await api.post("/api/flags/submit", { scope_type: "lab", scope_id: labId, value: flag });
    setFlagMsg(r.correct ? `✓ Correct! +${r.points} pts` : "✗ Incorrect flag");
  };

  if (!li) return <Spinner />;
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{li.lab_id}</h1>
          <div className="text-muted text-sm">Status: <span className={li.status === "running" ? "text-ok" : ""}>{li.status}</span></div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-4">
        <Panel className="lg:col-span-1">
          <div className="font-semibold mb-2">Machines</div>
          <div className="space-y-2">
            {li.machines.map((m: any) => (
              <button key={m.id} onClick={() => setActive(m.id)}
                className={`w-full text-left p-3 rounded-lg border ${active === m.id ? "border-brand" : "border-line"} bg-panel2`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{m.name.split("-").slice(1).join("-")}</span>
                  <span className={`tag ${m.status === "running" ? "text-ok" : ""}`}>{m.status}</span>
                </div>
                <div className="text-muted text-xs mt-1 font-mono">{m.ip_address || "no ip"}{m.simulated ? " · simulated" : ""}</div>
              </button>
            ))}
          </div>
          <div className="mt-4">
            <div className="font-semibold mb-1 text-sm">Network topology</div>
            {li.topology.networks.map((n: any) => (
              <div key={n.id} className="text-muted text-xs font-mono">{n.name} {n.cidr} ({n.mode})</div>
            ))}
          </div>
          <div className="mt-4">
            <div className="font-semibold mb-1 text-sm">Submit flag</div>
            <div className="flex gap-2">
              <input className="input text-sm" placeholder="HACKLAB{…}" value={flag} onChange={e => setFlag(e.target.value)} />
              <button className="btn btn-primary text-sm" onClick={submitFlag}>Go</button>
            </div>
            {flagMsg && <div className={`text-sm mt-1 ${flagMsg.startsWith("✓") ? "text-ok" : "text-bad"}`}>{flagMsg}</div>}
          </div>
        </Panel>

        <Panel className="lg:col-span-2">
          <div className="font-semibold mb-2">Terminal</div>
          {active && <Xterm vmId={active} key={active} />}
        </Panel>
      </div>
    </div>
  );
}

function Xterm({ vmId }: { vmId: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState("connecting…");
  useEffect(() => {
    if (!ref.current) return;
    const term = new Terminal({
      fontSize: 13, theme: { background: "#0e141d", foreground: "#e6edf3" }, cursorBlink: true,
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(ref.current);
    try { fit.fit(); } catch {}
    const ws = new WebSocket(wsUrl(`/api/ws/terminal/${vmId}`));
    let line = "";
    ws.onopen = () => setStatus("connected");
    ws.onclose = () => setStatus("disconnected");
    ws.onmessage = (ev) => term.write(ev.data);
    term.onData((d) => {
      if (d === "\r") { ws.send(line + "\r"); term.write("\r\n"); line = ""; }
      else if (d === "\u007f") { if (line) { line = line.slice(0, -1); term.write("\b \b"); } }
      else { line += d; term.write(d); }
    });
    const onResize = () => { try { fit.fit(); } catch {} };
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); ws.close(); term.dispose(); };
  }, [vmId]);
  return (
    <div>
      <div ref={ref} style={{ height: 420 }} className="rounded-lg overflow-hidden" />
      <div className="text-muted text-xs mt-1">WebSocket: {status}</div>
    </div>
  );
}
