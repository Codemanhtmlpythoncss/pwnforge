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
    <div className="h-full grid lg:grid-cols-2">
      {/* Brand / terminal panel */}
      <div className="hidden lg:flex flex-col justify-center px-16 relative overflow-hidden"
        style={{ background: "linear-gradient(160deg, var(--bg2), var(--bg))" }}>
        <div className="absolute inset-0 opacity-[0.06] pointer-events-none"
          style={{ background: "radial-gradient(600px 400px at 70% 20%, var(--brand), transparent)" }} />
        <div className="relative">
          <div className="text-5xl font-extrabold tracking-tight">
            Pwn<span className="text-brand glow-text">forge</span>
          </div>
          <p className="text-muted mt-3 max-w-md">
            Self-hosted cybersecurity training & virtual lab platform. Learn by
            doing — from fundamentals to expert, in isolated labs you control.
          </p>
          <div className="card p-4 mt-8 max-w-md mono text-[13px]">
            <div className="text-muted">$ pwnforge status</div>
            <div className="text-brand mt-1">✓ 89 courses · 1,440 machines · 10 paths</div>
            <div className="text-ink2">✓ KVM / libvirt orchestration ready</div>
            <div className="text-ink2">✓ isolated networks · browser consoles</div>
            <div className="text-muted mt-1">$ <span className="inline-block w-2 h-4 align-middle bg-brand animate-pulse" /></div>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="grid place-items-center p-6">
        <form onSubmit={submit} className="card p-8 w-full max-w-sm fade-in">
          <div className="text-2xl font-extrabold mb-1 lg:hidden">Pwn<span className="text-brand">forge</span></div>
          <div className="text-xl font-bold mb-1">{bootstrapping ? "Create administrator" : "Sign in"}</div>
          <div className="text-muted text-sm mb-6">
            {bootstrapping ? "First-run setup — this binds to localhost by default." : "Welcome back, operator."}
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
          <label className="block mb-5 text-sm">
            <span className="text-muted">Password</span>
            <input className="input mt-1" type="password" value={p} onChange={e => setP(e.target.value)} required />
          </label>
          {err && <div className="text-bad text-sm mb-3">⚠ {err}</div>}
          <button className="btn btn-primary w-full" disabled={busy}>
            {busy ? "Please wait…" : bootstrapping ? "Create administrator" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
