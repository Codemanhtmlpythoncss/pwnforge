import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Callout, CodeBlock, Panel, Section, Tabs } from "../ui";
import { Icon } from "../icons";
import { loadHostInfo, maskFromCidr, type HostInfo } from "../components/Connect";

/**
 * Player guide. Explains the HackTheBox-style lab model and, in particular, how to
 * reach a lab target from your own machine over either Tailscale or the local network.
 * The host's LAN IP and lab network are filled in from the server when available, falling
 * back to <host-lan-ip> / 10.200.0.0/16 (PwnForge's default lab network range).
 */
export default function Guide() {
  const [net, setNet] = useState("tailscale");
  const [host, setHost] = useState<HostInfo | null>(null);
  useEffect(() => { loadHostInfo().then(setHost); }, []);
  const cidr = host?.lab_network_cidr || "10.200.0.0/16";
  const gw = host?.host_lan_ip || "<host-lan-ip>";
  const mask = maskFromCidr(cidr);
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Icon name="globe" size={22} className="text-brand" />How labs work &amp; connecting to targets</h1>
        <p className="text-muted mt-1">Labs are real virtual machines, not simulations. Each one is a box you break into — like Hack The Box.</p>
      </div>

      <Section title="The idea">
        <Panel>
          <p className="text-sm text-muted leading-relaxed">
            When you start a lab, PwnForge boots one or more real VMs on an isolated network. A <strong className="text-ink">target</strong> box
            gives you <strong className="text-ink">no credentials</strong> — getting in is the challenge. You enumerate it, find a way in, escalate,
            and grab the <strong className="text-ink">flag</strong> (a string like <code>PWN{"{…}"}</code> hidden on the machine). Submit the flag to solve the lab.
          </p>
          <ul className="mt-3 space-y-1 text-sm text-muted">
            <li className="flex gap-2"><span className="text-brand">▸</span>Use the <strong className="text-ink">in-app console</strong> for a quick look — but it's just the VM's serial console.</li>
            <li className="flex gap-2"><span className="text-brand">▸</span>For the real experience, attack the target <strong className="text-ink">from your own machine</strong> with your own tools (<code>nmap</code>, <code>ssh</code>, Burp, Metasploit…). That needs a network route, below.</li>
          </ul>
        </Panel>
      </Section>

      <Section title="1 · Reach the target from your machine">
        <p className="text-sm text-muted mb-3">
          Lab targets sit on an isolated network behind the PwnForge host (<code>{cidr}</code>), so your own
          computer needs a route to them. Set this up <strong className="text-ink">once per device</strong>. Pick the method that matches your setup:
        </p>
        <Tabs label="Connection method" active={net} onChange={setNet}
          tabs={[["tailscale", "Over Tailscale"], ["lan", "Over the local network"]]} />

        {net === "tailscale" && (
          <div className="space-y-3">
            <p className="text-sm text-muted">Best if your devices are on a Tailscale tailnet — works from anywhere.</p>
            <ol className="list-decimal ml-5 space-y-2 text-sm text-muted">
              <li>On the PwnForge host, turn lab access on (nodeyard dashboard → PwnForge, or run the host helper):
                <CodeBlock label="on the host" code={"pwnforge-host.sh tailnet-access on"} />
              </li>
              <li>Approve the advertised subnet route for that machine in the{" "}
                <a className="text-brand" href="https://login.tailscale.com/admin/machines" target="_blank" rel="noreferrer">Tailscale admin console</a>.</li>
              <li>On <em>your</em> device, accept subnet routes (use <code>set</code>, not <code>up</code>):
                <CodeBlock label="on your device" code={"tailscale set --accept-routes"} />
              </li>
            </ol>
          </div>
        )}

        {net === "lan" && (
          <div className="space-y-3">
            <p className="text-sm text-muted">No Tailscale needed — for devices on the same local network as the host.{host?.host_lan_ip ? "" : " Ask the host's admin for its LAN IP."}</p>
            <ol className="list-decimal ml-5 space-y-2 text-sm text-muted">
              <li>Make sure lab access is on (the host helper opens the LAN path too):
                <CodeBlock label="on the host" code={"pwnforge-host.sh tailnet-access on"} />
              </li>
              <li>Add a static route to the lab network via the host's LAN IP:
                <CodeBlock label="macOS / Linux" code={`sudo ip route add ${cidr} via ${gw}`} />
                <CodeBlock label="macOS (alternative)" code={`sudo route -n add -net ${cidr} ${gw}`} />
                <CodeBlock label="Windows (admin)" code={`route add ${cidr.split("/")[0]} mask ${mask} ${gw}`} />
              </li>
            </ol>
          </div>
        )}
      </Section>

      <Section title="2 · Enumerate and break in">
        <p className="text-sm text-muted mb-3">
          Replace <code>&lt;target-ip&gt;</code> with the IP shown on the lab's workspace page. Run these from your own terminal:
        </p>
        <div className="space-y-3">
          <CodeBlock label="scan services" code={"nmap -Pn -sV -sC <target-ip>"} />
          <CodeBlock label="all ports" code={"nmap -Pn -p- <target-ip>"} />
          <CodeBlock label="ssh in (once you have a user)" code={"ssh <user>@<target-ip>"} />
        </div>
        <Callout kind="warn" title="Always use -Pn">
          Lab targets don't reply to ping, so a plain <code>nmap &lt;ip&gt;</code> reports "Host seems down" and gives up.{" "}
          <code>-Pn</code> tells nmap to skip the ping check and scan anyway — use it on every scan.
        </Callout>
        <Callout kind="info" title="Lab IPs are on the workspace">
          Open the lab from <Link className="text-brand" to="/running">Running</Link>; each machine lists its live IP with a copy button,
          and ready-made <code>nmap</code>/<code>ssh</code> commands. A target shows no login — that's the point. A practice box shows credentials you can copy.
        </Callout>
      </Section>

      <Section title="3 · Capture the flag">
        <p className="text-sm text-muted mb-3">
          Flags are planted on the machine (often in a home directory or <code>/root</code>). Once you have access, find and read it:
        </p>
        <CodeBlock label="hunt for the flag" code={"find / -name 'flag*' 2>/dev/null; cat ~/flag.txt"} />
        <p className="text-sm text-muted mt-3">
          Submit it in the lab workspace's <strong className="text-ink">Submit flag</strong> box. Answers are case-insensitive. Correct submissions award XP and
          unlock the walkthrough. Stuck? The workspace has tiered <strong className="text-ink">hints</strong> — reveal them one at a time.
        </p>
      </Section>

      <Callout kind="warn" title="Can't reach the target?">
        <ul className="space-y-1 ml-1">
          <li>• The lab must be <strong className="text-ink">running</strong> and have an IP (it takes a moment to boot and get one).</li>
          <li>• The host admin must have enabled lab access, and for Tailscale the route must be <strong className="text-ink">approved</strong> in the admin console.</li>
          <li>• Targets can't start outbound connections (no internet, no other labs) — only your inbound sessions get through. That's expected.</li>
        </ul>
      </Callout>
    </div>
  );
}
