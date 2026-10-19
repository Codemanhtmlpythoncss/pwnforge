import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { api, wsUrl } from "../api";
import { Panel, Spinner } from "../ui";
import { ConnectCommands } from "../components/Connect";

export default function LabWorkspace() {
  const { id } = useParams();
  const [li, setLi] = useState<any>(null);
  const [labId, setLabId] = useState("");
  const [active, setActive] = useState<string | null>(null);
  const [flag, setFlag] = useState("");
  const [flagMsg, setFlagMsg] = useState("");
  const [hintsShown, setHintsShown] = useState(0);
  const [copied, setCopied] = useState("");
  const [gone, setGone] = useState(false);

  const copy = (text: string, what: string) => {
    navigator.clipboard?.writeText(text).then(() => { setCopied(what); setTimeout(() => setCopied(""), 1200); }).catch(() => {});
  };

  // Poll just this instance, not every lab the user owns.
  const load = () => api.get(`/api/lab-instances/${id}`).then((found: any) => {
    setLi(found); setLabId(found?.lab_id || "");
    if (found && !active && found.machines[0]) setActive(found.machines[0].id);
  }).catch(() => setGone(true));
  useEffect(() => {
    setGone(false);
    load();
    const t = setInterval(() => { if (!document.hidden) load(); }, 4000);
    const onVis = () => { if (!document.hidden) load(); };
    document.addEventListener("visibilitychange", onVis);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", onVis); };
  }, [id]);

  const submitFlag = async () => {
    setFlagMsg("");
    const r = await api.post("/api/flags/submit", { scope_type: "lab", scope_id: labId, value: flag });
    setFlagMsg(r.correct ? (r.already_solved ? "✓ Correct (already solved)" : `✓ Correct! +${r.points} pts — walkthrough unlocked below`) : "✗ Incorrect flag");
    if (r.correct) load();
  };

  if (gone) return <Panel><div className="text-sm text-muted">This lab instance is no longer running. Start it again from <a className="text-brand" href="/labs">Labs</a>.</div></Panel>;
  if (!li) return <Spinner />;
  const activeM = li.machines.find((m: any) => m.id === active);
  const labCidr = activeM?.network_cidr || li.topology?.networks?.[0]?.cidr || undefined;
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{li.title || li.lab_id}</h1>
          <div className="text-muted text-sm">Status: <span className={li.status === "running" ? "text-ok" : ""}>{li.status}</span>{li.solved && <span className="text-ok"> · solved ✓</span>}</div>
        </div>
      </div>

      {li.description && <div className="text-muted text-sm">{li.description}</div>}
      {li.objectives?.length > 0 && (
        <Panel>
          <div className="font-semibold mb-2 text-sm">Objectives</div>
          <ul className="space-y-1">
            {li.objectives.map((o: string, i: number) => (
              <li key={i} className="text-sm text-muted flex gap-2"><span className="text-brand">▸</span>{o}</li>
            ))}
          </ul>
        </Panel>
      )}

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
                <div className="text-muted text-xs mt-1 font-mono flex items-center gap-1">
                  {m.ip_address || (m.simulated ? "no ip" : "waiting for an address…")}{m.simulated ? " · simulated" : ""}
                  {m.ip_address && <span role="button" title="Copy IP" onClick={e => { e.stopPropagation(); copy(m.ip_address, "ip-" + m.id); }} className="cursor-pointer hover:text-brand">{copied === "ip-" + m.id ? "✓" : "⧉"}</span>}
                </div>
                {m.target && (
                  <div className="text-xs mt-1 text-warn">🎯 Target — no credentials. Enumerate it and find your own way in.</div>
                )}
                {m.login && (
                  <div className="text-muted text-xs mt-1 font-mono flex items-center gap-2 flex-wrap">
                    <span>login: <span className="select-all text-ink">{m.login.username}</span></span>
                    <span role="button" title="Copy username" onClick={e => { e.stopPropagation(); copy(m.login.username, "u-" + m.id); }} className="cursor-pointer hover:text-brand">{copied === "u-" + m.id ? "✓" : "⧉"}</span>
                    <span>/ <span className="select-all text-ink">{m.login.password}</span></span>
                    <span role="button" title="Copy password" onClick={e => { e.stopPropagation(); copy(m.login.password, "p-" + m.id); }} className="cursor-pointer hover:text-brand">{copied === "p-" + m.id ? "✓" : "⧉"}</span>
                  </div>
                )}
              </button>
            ))}
          </div>
          {li.hints?.length > 0 && (
            <div className="mt-4">
              <div className="font-semibold mb-1 text-sm">Hints <span className="text-muted font-normal">(getting the key)</span></div>
              {li.hints.slice(0, hintsShown).map((h: any, i: number) => (
                <div key={i} className="text-xs mb-1.5 p-2 rounded-lg bg-panel2 border border-line">
                  <div className="font-medium text-ink">{i + 1}. {h.title}</div>
                  <div className="text-muted mt-0.5">{h.text}</div>
                </div>
              ))}
              {hintsShown < li.hints.length && (
                <button className="btn text-xs" onClick={() => setHintsShown(hintsShown + 1)}>
                  {hintsShown === 0 ? "Show a hint" : `Show hint ${hintsShown + 1} of ${li.hints.length}`}
                </button>
              )}
            </div>
          )}
          <div className="mt-4">
            <div className="font-semibold mb-1 text-sm">Network topology</div>
            {li.topology.networks.map((n: any) => (
              <div key={n.id} className="text-muted text-xs font-mono">{n.name} {n.cidr} ({n.mode})</div>
            ))}
          </div>
          <div className="mt-4">
            <div className="font-semibold mb-1 text-sm">Submit flag</div>
            <div className="flex gap-2">
              <input className="input text-sm" placeholder="PWN{…}" value={flag} onChange={e => setFlag(e.target.value)} />
              <button className="btn btn-primary text-sm" onClick={submitFlag}>Go</button>
            </div>
            {flagMsg && <div className={`text-sm mt-1 ${flagMsg.startsWith("✓") ? "text-ok" : "text-bad"}`}>{flagMsg}</div>}
          </div>
        </Panel>

        <Panel className="lg:col-span-2">
          <div className="font-semibold mb-2">Terminal</div>
          {active && <Xterm vmId={active} key={active}
            real={!!li.machines.find((m: any) => m.id === active && !m.simulated && m.status === "running")} />}
        </Panel>
      </div>

      {activeM?.ip_address && !activeM.simulated && (
        <Panel>
          <div className="font-semibold text-sm mb-2">Attack it from your own machine
            <span className="text-muted font-normal font-mono"> · {activeM.ip_address}</span></div>
          <ConnectCommands ip={activeM.ip_address} login={activeM.login} target={activeM.target} cidr={labCidr} />
        </Panel>
      )}

      {li.guide && (
        <Panel>
          <div className="font-semibold mb-2">Walkthrough {li.solved ? <span className="text-ok text-sm font-normal">· unlocked</span> : <span className="text-muted text-sm font-normal">· admin view</span>}</div>
          <pre className="text-sm whitespace-pre-wrap font-mono text-muted leading-relaxed">{li.guide}</pre>
        </Panel>
      )}
    </div>
  );
}

function Xterm({ vmId, real }: { vmId: string; real: boolean }) {
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
    // A real machine: its serial console, keystrokes sent as typed. A simulated one: a line-based practice shell.
    const ws = new WebSocket(wsUrl(real ? `/api/ws/console/${vmId}` : `/api/ws/terminal/${vmId}`));
    ws.binaryType = "arraybuffer";
    let line = "";
    ws.onopen = () => { setStatus(real ? "connected to the machine's console" : "connected"); if (real) ws.send("\r"); };
    ws.onclose = () => setStatus("disconnected");
    ws.onmessage = (ev) => term.write(typeof ev.data === "string" ? ev.data : new Uint8Array(ev.data));
    term.onData((d) => {
      if (real) { if (ws.readyState === WebSocket.OPEN) ws.send(d); return; }
      if (d === "\r") { ws.send(line + "\r"); term.write("\r\n"); line = ""; }
      else if (d === "\u007f") { if (line) { line = line.slice(0, -1); term.write("\b \b"); } }
      else { line += d; term.write(d); }
    });
    const onResize = () => { try { fit.fit(); } catch {} };
    window.addEventListener("resize", onResize);
    return () => { window.removeEventListener("resize", onResize); ws.close(); term.dispose(); };
  }, [vmId, real]);
  return (
    <div>
      <div ref={ref} style={{ height: 420 }} className="rounded-lg overflow-hidden" />
      <div className="text-muted text-xs mt-1">WebSocket: {status}</div>
    </div>
  );
}
