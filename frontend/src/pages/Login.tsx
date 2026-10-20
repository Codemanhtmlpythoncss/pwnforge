import { useState } from "react";
import { useAuth } from "../auth";
import { Logo, LogoMark } from "../logo";

export default function Login() {
  const { initialised, registrationOpen, login, bootstrap, register } = useAuth();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [creatingAccount, setCreatingAccount] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const bootstrapping = !initialised;
  const registering = !bootstrapping && creatingAccount;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      if (bootstrapping) await bootstrap(u, p, name);
      else if (registering) {
        if (!registrationOpen) throw new Error("Account creation is disabled. Ask the PwnForge administrator to enable sign-up or add your account.");
        if (p !== confirmPassword) throw new Error("The passwords don't match.");
        await register(u, p, name, email);
      }
      else await login(u, p);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };

  const toggleAccountForm = () => {
    setErr("");
    if (creatingAccount) {
      setCreatingAccount(false);
      setP("");
      setConfirmPassword("");
      return;
    }
    if (!registrationOpen) {
      setErr("Account creation is disabled. Ask the PwnForge administrator to enable sign-up in Settings or add your account.");
      return;
    }
    setCreatingAccount(true);
    setP("");
    setConfirmPassword("");
  };

  return (
    <div className="h-full grid lg:grid-cols-2">
      {/* Brand / terminal panel */}
      <div className="hidden lg:flex flex-col justify-center px-16 relative overflow-hidden"
        style={{ background: "linear-gradient(160deg, var(--bg2), var(--bg))" }}>
        <div className="absolute inset-0 bg-grid pointer-events-none" />
        <div className="absolute inset-0 opacity-[0.06] pointer-events-none"
          style={{ background: "radial-gradient(600px 400px at 70% 20%, var(--brand), transparent)" }} />
        <div className="relative">
          <div className="flex items-center gap-4">
            <LogoMark size={62} />
            <div className="text-5xl font-extrabold tracking-tight">
              Pwn<span className="text-brand glow-text">forge</span>
            </div>
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
          <Logo size={26} className="mb-4 lg:hidden" />
          <div className="text-xl font-bold mb-1">{bootstrapping ? "Create administrator" : registering ? "Create learner account" : "Sign in"}</div>
          <div className="text-muted text-sm mb-6">
            {bootstrapping ? "First-run setup — this binds to localhost by default." : registering ? "Create an account to start learning on this PwnForge server." : "Welcome back, operator."}
          </div>
          {(bootstrapping || registering) && (
            <label className="block mb-3 text-sm">
              <span className="text-muted">Display name{registering ? " (optional)" : ""}</span>
              <input className="input mt-1" value={name} onChange={e => setName(e.target.value)} autoComplete="name" />
            </label>
          )}
          {registering && (
            <label className="block mb-3 text-sm">
              <span className="text-muted">Email (optional)</span>
              <input className="input mt-1" type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" />
            </label>
          )}
          <label className="block mb-3 text-sm">
            <span className="text-muted">Username</span>
            <input className="input mt-1" value={u} onChange={e => setU(e.target.value)} autoFocus required minLength={registering ? 3 : undefined} maxLength={registering ? 64 : undefined} autoComplete="username" />
          </label>
          <label className="block mb-5 text-sm">
            <span className="text-muted">Password</span>
            <input className="input mt-1" type="password" value={p} onChange={e => setP(e.target.value)} required autoComplete={registering || bootstrapping ? "new-password" : "current-password"} />
          </label>
          {registering && (
            <label className="block mb-5 text-sm">
              <span className="text-muted">Confirm password</span>
              <input className="input mt-1" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required autoComplete="new-password" />
            </label>
          )}
          {err && <div className="text-bad text-sm mb-3">⚠ {err}</div>}
          <button className="btn btn-primary w-full" disabled={busy}>
            {busy ? "Please wait…" : bootstrapping ? "Create administrator" : registering ? "Create account" : "Sign in"}
          </button>
          {!bootstrapping && (
            <button type="button" className="btn w-full mt-3" disabled={busy} onClick={toggleAccountForm}>
              {registering ? "Already have an account? Sign in" : "Create account"}
            </button>
          )}
          {!bootstrapping && !registrationOpen && !registering && (
            <p className="text-muted text-xs mt-3 text-center">Self sign-up is off. Ask the administrator to add your learner account.</p>
          )}
        </form>
      </div>
    </div>
  );
}
