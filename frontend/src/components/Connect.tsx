import { useState } from "react";
import { Link } from "react-router-dom";
import { CodeBlock } from "../ui";

type Login = { username: string; password: string } | null | undefined;

/** The subnet to route to reach a machine: the lab's network if known, else the machine's own /24. */
function routeCidr(ip: string, cidr?: string): string {
  if (cidr) return cidr;
  const p = ip.split(".");
  return p.length === 4 ? `${p[0]}.${p[1]}.${p[2]}.0/24` : "the lab network";
}

/**
 * Ready-to-run commands for attacking a machine from the learner's own computer, plus a
 * collapsible one-time "set up access" guide (route the lab network over Tailscale or the LAN).
 * Shown wherever a machine has a live IP — the lab workspace and the Running page — so the
 * setup commands appear as soon as a lab or machine starts.
 */
export function ConnectCommands({ ip, login, target, cidr, defaultOpen }:
  { ip: string; login?: Login; target?: boolean; cidr?: string; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(!!defaultOpen);
  const net = routeCidr(ip, cidr);
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
              <li>Add a route to the lab network via the host's LAN IP (ask the admin for it):
                <CodeBlock label="macOS / Linux" code={`sudo ip route add ${net} via <host-lan-ip>`} />
                <CodeBlock label="Windows (admin)" code={`route add ${net.split("/")[0]} mask 255.255.0.0 <host-lan-ip>`} />
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
