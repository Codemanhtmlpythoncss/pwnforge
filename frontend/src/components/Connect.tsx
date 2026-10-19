import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { CodeBlock } from "../ui";

type Login = { username: string; password: string } | null | undefined;
export type HostInfo = { host_lan_ip: string | null; lab_network_cidr: string };

// Host LAN IP + lab supernet are the same for every machine, so fetch them once and share.
let hostInfoPromise: Promise<HostInfo> | null = null;
export function loadHostInfo(): Promise<HostInfo> {
  if (!hostInfoPromise) {
    hostInfoPromise = api.get("/api/host/capabilities")
      .then((c: any) => ({ host_lan_ip: c.host_lan_ip ?? null, lab_network_cidr: c.lab_network_cidr || "10.200.0.0/16" }))
      .catch(() => { hostInfoPromise = null; return { host_lan_ip: null, lab_network_cidr: "10.200.0.0/16" }; });
  }
  return hostInfoPromise;
}

/** The subnet to route to reach a machine: the lab's network if known, else the machine's own /24. */
function routeCidr(ip: string, cidr?: string): string {
  if (cidr) return cidr;
  const p = ip.split(".");
  return p.length === 4 ? `${p[0]}.${p[1]}.${p[2]}.0/24` : "10.200.0.0/16";
}

/** Dotted-decimal netmask for a CIDR prefix (e.g. "10.200.0.0/16" -> "255.255.0.0"), for Windows `route add`. */
export function maskFromCidr(cidr: string): string {
  const pfx = parseInt(cidr.split("/")[1] || "24", 10);
  return [0, 1, 2, 3].map(i => { const b = Math.min(8, Math.max(0, pfx - i * 8)); return (0xff << (8 - b)) & 0xff; }).join(".");
}

/**
 * Ready-to-run commands for attacking a machine from the learner's own computer, plus a
 * collapsible one-time "set up access" guide (route the lab network over Tailscale or the LAN).
 * Shown wherever a machine has a live IP — the lab workspace and the Running page — so the
 * setup commands appear as soon as a lab or machine starts. The host's LAN IP and the lab
 * supernet are filled in automatically when the server can report them.
 */
export function ConnectCommands({ ip, login, cidr, defaultOpen }:
  { ip: string; login?: Login; target?: boolean; cidr?: string; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(!!defaultOpen);
  const [host, setHost] = useState<HostInfo | null>(null);
  useEffect(() => { if (open && !host) loadHostInfo().then(setHost); }, [open, host]);

  const net = host?.lab_network_cidr || routeCidr(ip, cidr);
  const gw = host?.host_lan_ip || "<host-lan-ip>";
  const mask = maskFromCidr(net);

  return (
    <div className="space-y-2">
      <div className="text-muted text-xs">Run these from a terminal on your own machine (not the in-app console) to attack it like a real box. Targets don't answer ping, so <span className="font-mono text-ink">-Pn</span> is required:</div>
      <CodeBlock label="scan services" code={`nmap -Pn -sV -sC ${ip}`} />
      {login
        ? <CodeBlock label="ssh in" code={`ssh ${login.username}@${ip}`} />
        : <CodeBlock label="all ports" code={`nmap -Pn -p- ${ip}`} />}

      <button className="btn btn-ghost text-xs" onClick={() => setOpen(o => !o)}>
        {open ? "Hide access setup" : "First time? Set up access to reach this IP"}
      </button>

      {open && (
        <div className="pt-1 space-y-4 text-sm">
          <div className="text-muted">
            Targets live on an isolated network (<span className="font-mono text-ink">{net}</span>) behind the PwnForge host,
            so your computer needs a route to them. Do this <strong className="text-ink">once per device</strong> — pick whichever fits.
            A route to the whole range reaches every lab, not just this one.
          </div>
          <div>
            <div className="font-semibold text-ink mb-1">Over Tailscale</div>
            <ol className="list-decimal ml-5 space-y-1.5 text-muted">
              <li>On the host, enable lab access (nodeyard dashboard → PwnForge, or <span className="font-mono text-ink">pwnforge-host.sh tailnet-access on</span>), then approve the advertised route in the <a className="text-brand" href="https://login.tailscale.com/admin/machines" target="_blank" rel="noreferrer">Tailscale admin console</a>.</li>
              <li>On your device, accept subnet routes:
                <CodeBlock label="your device" code={"tailscale set --accept-routes"} />
              </li>
            </ol>
          </div>
          <div>
            <div className="font-semibold text-ink mb-1">Over the local network (no Tailscale)</div>
            <ol className="list-decimal ml-5 space-y-1.5 text-muted">
              <li>Make sure the host admin turned lab access on (it opens the LAN path too).</li>
              <li>Add a route to the lab network via the host{host?.host_lan_ip ? "" : "'s LAN IP (ask the admin for it)"}:
                <CodeBlock label="macOS / Linux" code={`sudo ip route add ${net} via ${gw}`} />
                <CodeBlock label="Windows (admin)" code={`route add ${net.split("/")[0]} mask ${mask} ${gw}`} />
              </li>
            </ol>
          </div>
          <div className="text-muted text-xs">
            Full walkthrough on the <Link className="text-brand" to="/guide">Guide</Link> page. Targets can't start outbound connections — only your inbound sessions get through.
          </div>
        </div>
      )}
    </div>
  );
}
