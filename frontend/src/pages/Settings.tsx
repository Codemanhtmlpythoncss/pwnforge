import { useEffect, useState } from "react";
import { api } from "../api";
import { Panel, Spinner } from "../ui";

function Updates() {
  const [v, setV] = useState<any>(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState("");
  const [command, setCommand] = useState("");
  const [outcome, setOutcome] = useState<"" | "success" | "failed" | "restarted" | "timeout">("");
  const load = () => api.get("/api/admin/version").then(setV).catch(() => {});
  useEffect(() => { load(); }, []);

  const update = async () => {
    setMsg(""); setOut(""); setCommand(""); setOutcome(""); setBusy(true);
    try {
      const { job_id } = await api.post("/api/admin/update");
      setMsg("Updating… (the service restarts when it's done)");
      let finished = false;
      for (let i = 0; i < 400; i++) {
        await new Promise(r => setTimeout(r, 2000));
        let j;
        try { j = await api.get(`/api/jobs/${job_id}`); }
        catch {
          setOutcome("restarted");
          setMsg("The connection closed while checking the update. Reload and check the version above to confirm the server restarted.");
          finished = true;
          break;
        }
        if (j.status === "succeeded") {
          setOut(typeof j.result?.output === "string" ? j.result.output.trim() : "");
          setCommand(typeof j.result?.command === "string" ? j.result.command : "");
          setOutcome("success");
          setMsg("Update command completed. Reload the page to load the updated app.");
          finished = true;
          break;
        }
        if (j.status === "failed") {
          setOut(j.error || "");
          setOutcome("failed");
          setMsg("Update failed.");
          finished = true;
          break;
        }
        setMsg(`Updating PwnForge${j.stage ? ` — ${j.stage}` : ""}…`);
      }
      if (!finished) {
        setOutcome("timeout");
        setMsg("The update is still running. Check its status in Jobs, then reload when it finishes.");
      }
    } catch (e: any) { setOutcome("failed"); setMsg(e.message); }
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
      {msg && <div className={`text-sm mt-2 ${outcome === "failed" ? "text-bad" : outcome === "success" ? "text-ok" : "text-brand"}`} role={outcome === "failed" ? "alert" : "status"} aria-live="polite">{msg}</div>}
      {outcome === "success" && command && <div className="text-muted text-xs mt-1">Command: <span className="font-mono">{command}</span></div>}
      {outcome === "success" && !out && <div className="text-muted text-xs mt-1">The command exited successfully but produced no console output.</div>}
      {out && <pre className="mt-2 text-xs font-mono bg-panel2 rounded-lg p-3 overflow-auto max-h-56 whitespace-pre-wrap">{out}</pre>}
    </Panel>
  );
}

function ChangePassword() {
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [ok, setOk] = useState(false);
  const save = async () => {
    setBusy(true); setMsg(""); setOk(false);
    try {
      await api.post("/api/auth/change-password", { current_password: cur, new_password: next });
      setOk(true); setMsg("Password changed."); setCur(""); setNext("");
    } catch (e: any) { setMsg(e.message || "Couldn't change the password"); }
    finally { setBusy(false); }
  };
  return (
    <Panel>
      <div className="font-semibold mb-1">Password</div>
      <div className="text-muted text-sm mb-3">
        Change your sign-in password. Passwords are stored hashed, so the current one can't be shown —
        use the eye toggle to see what you type.
      </div>
      <div className="space-y-2 max-w-sm">
        <div className="relative">
          <input className="input pr-16" type={show ? "text" : "password"} placeholder="Current password"
            autoComplete="current-password" value={cur} onChange={e => setCur(e.target.value)} />
        </div>
        <div className="relative">
          <input className="input pr-16" type={show ? "text" : "password"} placeholder="New password"
            autoComplete="new-password" value={next} onChange={e => setNext(e.target.value)} />
          <button type="button" tabIndex={-1} onClick={() => setShow(s => !s)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted hover:text-ink">
            {show ? "Hide" : "Show"}
          </button>
        </div>
        <button className="btn btn-primary text-sm" disabled={busy || !cur || !next} onClick={save}>
          {busy ? "Saving…" : "Change password"}
        </button>
        {msg && <div className={`text-sm ${ok ? "text-ok" : "text-bad"}`}>{msg}</div>}
      </div>
    </Panel>
  );
}

function AccountReset() {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const reset = async () => {
    setBusy(true); setMsg("");
    try {
      await api.post("/api/auth/account/reset");
      setMsg("Your progress has been reset — reloading…");
      setTimeout(() => window.location.reload(), 900);
    } catch (e: any) { setMsg(e.message); setBusy(false); setConfirming(false); }
  };
  return (
    <Panel>
      <div className="font-semibold mb-1">Account</div>
      <div className="text-muted text-sm mb-3">
        Reset your learning progress for a fresh start — clears XP, rank, streak, course and lesson progress,
        assessment attempts, skill evidence, captured flags, achievements and certificates. Your account, password,
        saved items and any running machines are kept.
      </div>
      {!confirming ? (
        <button className="btn btn-danger text-sm" onClick={() => setConfirming(true)}>Reset my progress…</button>
      ) : (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-warn">This can't be undone.</span>
          <button className="btn btn-danger text-sm" disabled={busy} onClick={reset}>
            {busy ? "Resetting…" : "Yes, reset everything"}
          </button>
          <button className="btn text-sm" disabled={busy} onClick={() => setConfirming(false)}>Cancel</button>
        </div>
      )}
      {msg && <div className="text-sm mt-2 text-brand">{msg}</div>}
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
      <ChangePassword />
      <AccountReset />
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
