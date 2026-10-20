import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Callout, CodeBlock, Panel, Spinner } from "../ui";

type VpnClient = {
  id: string; user_id: number; name: string; created_at: string; expires_at: string;
  downloaded: boolean; revoked: boolean;
};

/** Admin workflow for giving an invited PwnForge learner their own revocable OpenVPN device profile. */
export default function OpenVpnAccess() {
  const [vpn, setVpn] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [host, setHost] = useState("");
  const [userId, setUserId] = useState("");
  const [deviceName, setDeviceName] = useState("friend-device");
  const [commands, setCommands] = useState<any>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [status, accountList] = await Promise.all([api.get("/api/vpn"), api.get("/api/users")]);
      setVpn(status);
      setUsers(accountList.items || []);
      setHost(status.settings?.public_host || "");
      if (!userId && accountList.items?.length) {
        const firstLearner = accountList.items.find((u: any) => u.role === "learner" && u.is_active);
        if (firstLearner) setUserId(String(firstLearner.id));
      }
    } catch (e: any) { setError(e.message || "Could not load VPN settings."); }
  };
  useEffect(() => { load(); }, []);

  const userNames = useMemo(() => Object.fromEntries(users.map(u => [u.id, u.username])), [users]);
  const activeLearners = users.filter(u => u.role === "learner" && u.is_active);
  const settings = vpn?.settings || {};
  const webPort = window.location.port || String(settings.web_port || (window.location.protocol === "https:" ? 443 : 80));
  const firewallCommands = [
    "# If UFW is active, permit the website on the VPN interface and deny it elsewhere:",
    `sudo ufw allow ${settings.port || 1194}/${settings.protocol || "udp"} comment 'PwnForge VPN'`,
    `sudo ufw insert 1 allow in on tun0 from ${settings.subnet || "10.8.0.0/24"} to any port ${webPort} proto tcp comment 'PwnForge over VPN'`,
    `sudo ufw deny in proto tcp to any port ${webPort} comment 'PwnForge web private'`,
    "sudo ufw status",
    "# Add any required LAN/Tailscale permits before the deny rule above.",
  ].join("\n");

  const act = async (key: string, fn: () => Promise<any>, ok: string) => {
    setBusy(key); setMessage(""); setError("");
    try { await fn(); setMessage(ok); await load(); }
    catch (e: any) { setError(e.message || "That action failed."); }
    finally { setBusy(""); }
  };
  const saveHost = () => act("host", () => api.put("/api/settings/vpn.public_host", { value: host.trim() }), "VPN address saved.");
  const initialize = () => act("init", () => api.post("/api/vpn/init"), "VPN certificates created. Keep the PwnForge data directory private and backed up.");
  const showServerConfig = async () => {
    setBusy("config"); setError("");
    try { setCommands(await api.get("/api/vpn/server-config")); }
    catch (e: any) { setError(e.message || "Could not generate the server configuration."); }
    finally { setBusy(""); }
  };
  const toggleEnabled = () => act("enabled", () => api.put("/api/settings/vpn.enabled", { value: !settings.enabled }),
    settings.enabled ? "VPN instructions hidden from learners." : "VPN instructions are now visible in the learner Guide.");
  const issue = () => act("issue", () => api.post("/api/vpn/clients", { user_id: Number(userId), name: deviceName.trim() }),
    "Device profile created. Download it once, then send it to your friend over a private channel.");

  const download = async (client: VpnClient) => {
    setBusy(`download-${client.id}`); setError(""); setMessage("");
    try {
      const response = await fetch(`/api/vpn/clients/${client.id}/profile`, { credentials: "include", cache: "no-store" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `${response.status} ${response.statusText}`);
      }
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `pwnforge-${client.name}.ovpn`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage(`Downloaded ${filename}. The server has deleted its copy of the private key.`);
      await load();
    } catch (e: any) { setError(e.message || "Profile download failed."); }
    finally { setBusy(""); }
  };
  const revoke = (client: VpnClient) => {
    if (!window.confirm(`Revoke ${client.name}'s VPN access? Their profile will stop working after the server receives the updated revocation list.`)) return;
    void act(`revoke-${client.id}`, () => api.post(`/api/vpn/clients/${client.id}/revoke`), `${client.name} was revoked.`);
  };

  if (!vpn) return <Panel><Spinner /></Panel>;

  return (
    <Panel>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-semibold">Let a friend connect without Tailscale</div>
          <p className="text-muted text-sm mt-1 max-w-3xl">
            PwnForge can issue one private OpenVPN profile per device. Your friend installs an OpenVPN client,
            imports their profile, connects, then signs into PwnForge normally. Each profile can be revoked here.
          </p>
        </div>
        <span className={`tag ${vpn.initialised && settings.public_host ? "text-ok" : ""}`}>
          {vpn.initialised ? "VPN certificates ready" : "VPN not initialized"}
        </span>
      </div>

      {message && <div className="text-sm text-ok mt-3" role="status" aria-live="polite">{message}</div>}
      {error && <div className="text-sm text-bad mt-3" role="alert">{error}</div>}

      <div className="grid lg:grid-cols-2 gap-4 mt-4">
        <div className="space-y-3">
          <div className="text-sm font-semibold">1. Set a public VPN address</div>
          <p className="text-muted text-xs">
            Use a DNS name or public IP your friend can reach. A dynamic DNS name is useful if your home IP changes.
          </p>
          <div className="flex flex-wrap gap-2">
            <input className="input flex-1 min-w-48" aria-label="Public VPN host" placeholder="vpn.example.com or public IP"
              value={host} onChange={e => setHost(e.target.value)} />
            <button className="btn text-sm" disabled={!!busy || !host.trim()} onClick={saveHost}>{busy === "host" ? "Saving…" : "Save address"}</button>
          </div>
          <div className="text-muted text-xs">
            Router: forward <span className="font-mono text-ink">{String(settings.protocol || "udp").toUpperCase()} {settings.port || 1194}</span> to this host's fixed LAN IP.
            Do not forward the PwnForge web port. If your ISP uses CGNAT, router port forwarding won't be reachable from outside; use a public IP or a relay.
          </div>

          <div className="text-sm font-semibold pt-2">2. Prepare the server</div>
          {!vpn.initialised ? (
            <div className="space-y-2">
              <p className="text-muted text-xs">Create PwnForge's VPN certificate authority once. It cannot be regenerated over the existing one.</p>
              <button className="btn btn-primary text-sm" disabled={!!busy || !settings.public_host} onClick={initialize}>
                {busy === "init" ? "Creating…" : "Create VPN certificates"}
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <button className="btn text-sm" disabled={!!busy} onClick={showServerConfig}>
                {busy === "config" ? "Preparing…" : "Show server install steps"}
              </button>
              <div className="text-muted text-xs">Install OpenVPN on the PwnForge host, install the generated files, and enable its systemd service.</div>
            </div>
          )}
          {commands && <div className="space-y-3 mt-2">
            <CodeBlock label="PwnForge server configuration" code={commands.config} />
            <CodeBlock label="Run on the PwnForge host" code={(commands.commands.install || []).join("\n")} />
            <CodeBlock label="Keep revocations in sync (run once on the host)" code={commands.commands.crl_sync} />
            <CodeBlock label="Host firewall (only if UFW is active)" code={firewallCommands} />
            <Callout kind="info" title="Router and host setup">
              {commands.commands.router} The OpenVPN service must be running before you enable learner instructions.
            </Callout>
          </div>}
        </div>

        <div className="space-y-3">
          <div className="text-sm font-semibold">3. Make the PwnForge website available inside the VPN</div>
          <p className="text-muted text-xs">
            The site must listen on the host's VPN-facing interface. For a standalone install, set <code>server.lan_access</code> to <code>true</code> in Settings and restart PwnForge.
            For Nodeyard installs, open Nodeyard → PwnForge → Address and choose <strong className="text-ink">LAN and VPN (all host interfaces)</strong>; Nodeyard's setting overrides PwnForge's own bind setting. The firewall commands below allow the website through <code>tun0</code> and deny that port on other interfaces.
            Add any LAN/Tailscale exceptions before the deny rule if needed. Never forward the web port from your router.
          </p>
          {settings.host_vpn_ip && <CodeBlock label="Friend opens this after connecting" code={`http://${settings.host_vpn_ip}:${webPort}`} />}
          {settings.web_lan_access
            ? <div className="text-xs text-ok">PwnForge's standalone listener is set to LAN/VPN. If Nodeyard hosts it, also verify Nodeyard → PwnForge → Address.</div>
            : <div className="text-xs text-warn">PwnForge's standalone listener is off; friends may connect to OpenVPN but the website won't load through it until you enable listening. Nodeyard installs use Nodeyard → PwnForge → Address.</div>}
          <p className="text-muted text-xs">Your friend still signs in with their normal learner account. Create one in <Link className="text-brand" to="/admin">Administration → Users</Link>, then share their temporary login privately.</p>
          <div className="flex items-center gap-2 pt-1">
            <button className="btn text-sm" disabled={!!busy || !vpn.initialised || !settings.public_host} onClick={toggleEnabled}>
              {busy === "enabled" ? "Saving…" : settings.enabled ? "Hide learner VPN guide" : "Show learner VPN guide"}
            </button>
            <span className="text-muted text-xs">Current: {settings.enabled ? "visible" : "hidden"}</span>
          </div>
        </div>
      </div>

      <div className="border-t border-line mt-5 pt-4">
        <div className="font-semibold text-sm mb-1">4. Issue a separate profile for each friend device</div>
        <p className="text-muted text-xs mb-3">Create the learner first in Administration → Users. Profiles are downloadable once; PwnForge deletes its private-key copy after the download.</p>
        <div className="flex flex-wrap gap-2 mb-4">
          <select className="input max-w-xs" aria-label="Learner" value={userId} onChange={e => setUserId(e.target.value)}>
            <option value="">Choose a learner…</option>
            {activeLearners.map(u => <option key={u.id} value={u.id}>{u.username}</option>)}
          </select>
          <input className="input max-w-52" aria-label="Device name" maxLength={32} value={deviceName} onChange={e => setDeviceName(e.target.value)} />
          <button className="btn btn-primary text-sm" disabled={!!busy || !vpn.initialised || !settings.public_host || !userId || !deviceName.trim()}
            onClick={issue}>{busy === "issue" ? "Issuing…" : "Create device profile"}</button>
          {!activeLearners.length && <Link className="btn text-sm" to="/admin">Create learner account</Link>}
        </div>
        <div className="text-xs text-warn mb-3">A downloaded <code>.ovpn</code> file is a private credential. Send it through a private channel, and revoke it immediately if it is lost or shared accidentally.</div>
        {vpn.clients?.length ? (
          <div className="space-y-2">
            {vpn.clients.map((c: VpnClient) => (
              <div key={c.id} className="flex flex-wrap items-center justify-between gap-2 border border-line rounded-lg p-3 text-sm">
                <div>
                  <div className="font-medium">{userNames[c.user_id] || "Unknown learner"} · {c.name}</div>
                  <div className="text-muted text-xs">{c.revoked ? "Revoked" : c.downloaded ? "Downloaded" : "Ready to download"} · expires {new Date(c.expires_at).toLocaleDateString()}</div>
                </div>
                <div className="flex gap-2">
                  {!c.revoked && !c.downloaded && <button className="btn text-xs" disabled={!!busy} onClick={() => download(c)}>{busy === `download-${c.id}` ? "Downloading…" : "Download profile"}</button>}
                  {!c.revoked && <button className="btn btn-danger text-xs" disabled={!!busy} onClick={() => revoke(c)}>Revoke</button>}
                </div>
              </div>
            ))}
          </div>
        ) : <div className="text-muted text-sm">No VPN device profiles have been issued yet.</div>}
      </div>
    </Panel>
  );
}
