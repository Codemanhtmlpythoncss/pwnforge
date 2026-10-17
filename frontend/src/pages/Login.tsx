import { useState } from "react";
import { useAuth } from "../auth";

export default function Login() {
  const { initialised, login, bootstrap } = useAuth();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const bootstrapping = !initialised;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      if (bootstrapping) await bootstrap(u, p, name);
      else await login(u, p);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <div className="h-full grid place-items-center p-6">
      <form onSubmit={submit} className="card p-8 w-full max-w-sm">
        <div className="text-2xl font-extrabold mb-1">Hack<span className="text-brand">Lab</span></div>
        <div className="text-muted text-sm mb-6">
          {bootstrapping ? "Create the first administrator account." : "Sign in to continue."}
        </div>
        {bootstrapping && (
          <label className="block mb-3 text-sm">
            <span className="text-muted">Display name</span>
            <input className="input mt-1" value={name} onChange={e => setName(e.target.value)} />
          </label>
        )}
        <label className="block mb-3 text-sm">
          <span className="text-muted">Username</span>
          <input className="input mt-1" value={u} onChange={e => setU(e.target.value)} autoFocus required />
        </label>
        <label className="block mb-4 text-sm">
          <span className="text-muted">Password</span>
          <input className="input mt-1" type="password" value={p} onChange={e => setP(e.target.value)} required />
        </label>
        {err && <div className="text-bad text-sm mb-3">{err}</div>}
        <button className="btn btn-primary w-full justify-center" disabled={busy}>
          {busy ? "Please wait…" : bootstrapping ? "Create administrator" : "Sign in"}
        </button>
        {bootstrapping && (
          <p className="text-muted text-xs mt-4">
            This runs once on a fresh install and binds to localhost by default.
          </p>
        )}
      </form>
    </div>
  );
}
