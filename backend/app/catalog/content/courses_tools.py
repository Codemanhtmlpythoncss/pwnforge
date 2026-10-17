"""Tool-mastery courses — how to actually use the security tools.

Every course teaches a tool (or small family) the way a professional uses it:
what it does, how to run it, the options that matter, how to read the output,
and the defensive/remediation angle. All usage is framed for **authorised**
testing — your own Pwnforge labs, or systems you own or have written permission
to test. The platform's isolated labs are the intended practice targets.
"""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, cmd, lesson, mcq, short, wstep,
)

AUTH = ("> Only run these tools against systems you own or are explicitly "
        "authorised to test — the Pwnforge labs are built for exactly this. "
        "Unauthorised scanning or access is unethical and usually unlawful.")


def _c(id, title, desc, difficulty, spec, prereqs, lessons, qs, cprereqs=None,
       lab=None, tags=None):
    return course(id, title, desc, difficulty, "tools", specialization=spec,
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=(tags or []) + ["tool", "hands-on"], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


L = lesson
COURSES = [
    # ---------------------------------------------------------------- Recon
    _c("tool-nmap", "Nmap: Network Scanning & Enumeration",
       "Discover hosts, find open ports, fingerprint services and run NSE "
       "scripts — the enumeration workhorse.",
       "easy", "pentest", ["networking-fundamentals", "service-enumeration"],
       [
           L("Host discovery & your first scan", "easy", 20, "tool-scanning",
             "Nmap maps what's reachable and what's listening.\n\n```\n"
             "nmap -sn 10.200.0.0/24        # ping sweep: which hosts are up\n"
             "nmap 10.200.0.10              # default: top 1000 TCP ports\n"
             "nmap -p- 10.200.0.10          # all 65535 TCP ports\n"
             "nmap -p 22,80,443 10.200.0.10 # specific ports\n```\n"
             "Start a Pwnforge lab and scan the target you own. Read every line: "
             "`open`, `closed` and `filtered` each mean something different "
             "(filtered usually implies a firewall).\n\n" + AUTH,
             exercises=[cmd("Scan ALL TCP ports on 10.0.0.5 (nmap -p- ...)",
                            "nmap -p- 10.0.0.5", "tool-scanning",
                            "`-p-` scans all 65535 ports.")],
             hints=["`-sn` = no port scan, just host discovery.",
                    "`filtered` often means a firewall is dropping probes."]),
           L("Service & version detection, OS", "easy", 20, "tool-scanning",
             "Knowing a port is open is step one; knowing *what* answers is the "
             "goal.\n\n```\nnmap -sV 10.200.0.10          # service/version detection\n"
             "nmap -sV -sC 10.200.0.10      # + default safe NSE scripts\n"
             "nmap -O 10.200.0.10           # OS guess (needs privilege)\n"
             "nmap -A 10.200.0.10           # aggressive: -sV -sC -O + traceroute\n```\n"
             "`-sC` runs the *default* category of the Nmap Scripting Engine — "
             "safe, informative scripts. Record versions; they drive the whole "
             "assessment and tell a defender exactly what to patch.",
             exercises=[cmd("Enable service/version detection (flag)?", "-sV",
                            "tool-scanning", "`-sV` probes service versions.")],
             walkthrough=[wstep("Start the Network Basics Lab", "It gives you owned targets."),
                          wstep("Sweep then scan", "`nmap -sn` the subnet, then `-sV -sC` a host."),
                          wstep("Record versions", "Note service + version for each open port."),
                          wstep("Map to risk", "List known-weak versions to investigate/patch.")]),
           L("NSE, timing & output", "easy", 15, "tool-scanning",
             "The NSE has categories (`default`, `safe`, `vuln`, `auth`, ...): "
             "`nmap --script vuln 10.200.0.10`. Timing templates `-T0`..`-T5` trade "
             "speed for stealth/stability (`-T4` is a common lab default). Always "
             "save output: `-oA scan` writes normal/greppable/XML at once, which "
             "feeds reports and other tools.",
             exercises=[cmd("Save all three output formats with base name 'scan'",
                            "nmap -oA scan", "tool-scanning", "`-oA` writes .nmap/.gnmap/.xml.")]),
       ],
       [cmd("All-ports flag?", "-p-", "tool-scanning", "`-p-` = every TCP port."),
        mcq("`-sC` runs:", ["All scripts", "Default/safe NSE scripts", "Exploits",
            "Nothing"], "Default/safe NSE scripts", "tool-scanning", "Default category."),
        short("Port state that usually means a firewall is dropping probes?",
              "filtered", "tool-scanning", "filtered.")],
       lab="network-basics-lab"),

    _c("tool-web-scanners", "Web Scanners: Nikto & Nuclei",
       "Automated first-pass web checks and template-based scanning.",
       "intermediate", "web", ["tool-nmap", "web-application-security"],
       [
           L("Nikto for quick server checks", "intermediate", 15, "tool-web-scanners",
             "Nikto does a fast, noisy sweep for known issues, dangerous files and "
             "server misconfig.\n\n```\nnikto -h http://10.200.0.10\n"
             "nikto -h http://10.200.0.10 -p 8080 -Tuning 123b\n```\n"
             "It's a starting point, not a verdict — every finding must be "
             "confirmed manually. Great for spotting default pages, outdated "
             "servers and exposed admin paths in your lab app.",
             exercises=[cmd("Scan a host with nikto (nikto -h URL)", "nikto -h http://10.0.0.5",
                            "tool-web-scanners", "`-h` sets the target host.")],
             hints=["Nikto is loud; use it in labs, not quietly on real estates."]),
           L("Nuclei & templates", "intermediate", 20, "tool-web-scanners",
             "Nuclei runs community/custom YAML *templates* to check for specific, "
             "known issues with far less noise than a blind scanner.\n\n```\n"
             "nuclei -u http://10.200.0.10\n"
             "nuclei -u http://10.200.0.10 -t http/misconfiguration/\n"
             "nuclei -l targets.txt -severity high,critical\n```\n"
             "Templates make findings reproducible and reviewable — you can read "
             "exactly what was checked, which is ideal for a report.",
             exercises=[short("Nuclei checks are written as ___ (file type).", "templates",
                              "tool-web-scanners", "YAML templates.")]),
       ],
       [mcq("A scanner result should be treated as:", ["Proof", "A lead to verify",
            "A patch", "Noise"], "A lead to verify", "tool-web-scanners",
            "Always confirm manually."),
        short("Nuclei runs checks written as ___.", "templates", "tool-web-scanners",
              "Templates.")],
       lab="web-security-lab"),

    _c("tool-wireshark", "Wireshark & tcpdump: Packet Analysis",
       "Capture and dissect traffic to understand exactly what's on the wire.",
       "intermediate", "defensive", ["tcpip-packet-analysis"],
       [
           L("Capturing with tcpdump", "intermediate", 15, "tool-packet-analysis",
             "`tcpdump` captures from the CLI; save to a pcap for later analysis.\n\n"
             "```\ntcpdump -i eth0 -w capture.pcap\n"
             "tcpdump -i eth0 'tcp port 80'\n"
             "tcpdump -r capture.pcap -n host 10.200.0.10\n```\n"
             "BPF filters (`host`, `port`, `net`, `tcp`/`udp`) limit the capture "
             "to what matters. Capturing needs privilege and a NIC you own.",
             exercises=[cmd("Write a capture to capture.pcap on eth0",
                            "tcpdump -i eth0 -w capture.pcap", "tool-packet-analysis",
                            "`-w` writes a pcap.")],
             hints=["Capture filters (BPF) differ from Wireshark display filters."]),
           L("Wireshark display filters & streams", "intermediate", 20, "tool-packet-analysis",
             "Open the pcap in Wireshark and filter with the display language: "
             "`http`, `tcp.port == 80`, `ip.addr == 10.200.0.10`, "
             "`tcp.flags.syn == 1`. *Follow TCP Stream* reconstructs an exchange so "
             "you can read an application conversation end-to-end. Use Statistics → "
             "Conversations to see who talks to whom.",
             exercises=[short("Wireshark display filter for HTTP only?", "http",
                              "tool-packet-analysis", "`http` filters HTTP.")],
             walkthrough=[wstep("Capture", "`tcpdump -w lab.pcap` while using the lab."),
                          wstep("Open in Wireshark", "Load lab.pcap."),
                          wstep("Filter", "Apply `http` or `tcp.port==80`."),
                          wstep("Follow stream", "Right-click → Follow → TCP Stream.")]),
       ],
       [cmd("tcpdump flag to write a pcap?", "-w", "tool-packet-analysis", "`-w file`."),
        short("Reconstruct a full exchange in Wireshark: Follow TCP ___.", "stream",
              "tool-packet-analysis", "Follow TCP Stream.")],
       lab="defensive-monitoring-lab"),

    # ---------------------------------------------------------------- Web
    _c("tool-burp", "Burp Suite: Web Proxy Testing",
       "Intercept, inspect, replay and tamper HTTP for authorised web testing.",
       "intermediate", "web", ["web-application-security", "http-https"],
       [
           L("Proxy & intercept", "intermediate", 20, "tool-web-proxy",
             "Burp sits between your browser and the app so you can see and modify "
             "every request. Set the browser proxy to `127.0.0.1:8080`, install "
             "Burp's CA cert for HTTPS, then use **Proxy → Intercept** to pause and "
             "edit requests. **HTTP history** records everything for review. Point "
             "it only at your lab app.\n\n" + AUTH,
             exercises=[mcq("Burp's default proxy listener is:",
                            ["0.0.0.0:80", "127.0.0.1:8080", "127.0.0.1:443", "10.0.0.1:8000"],
                            "127.0.0.1:8080", "tool-web-proxy", "Default is 127.0.0.1:8080.")],
             hints=["Install Burp's CA cert so HTTPS traffic is readable."]),
           L("Repeater & Decoder", "intermediate", 20, "tool-web-proxy",
             "**Repeater** lets you resend and tweak a single request repeatedly — "
             "ideal for probing how a parameter changes a response (the manual way "
             "to confirm injection/authz issues). **Decoder** encodes/decodes "
             "URL/base64/hex. **Comparer** diffs two responses. Working manually in "
             "Repeater teaches you *why* a bug exists, not just that a scanner "
             "flagged it.",
             exercises=[short("Burp tab for resending/tweaking one request?", "Repeater",
                              "tool-web-proxy", "Repeater.")],
             walkthrough=[wstep("Start the Web Security Lab", "Owned, intentional target."),
                          wstep("Proxy the browser", "Point it at 127.0.0.1:8080, trust the CA."),
                          wstep("Send to Repeater", "Right-click a request → Send to Repeater."),
                          wstep("Vary one input", "Change a parameter, compare responses.")]),
           L("Intruder & scanner (responsibly)", "intermediate", 15, "tool-web-proxy",
             "**Intruder** automates sending many payloads to a position (e.g. to "
             "test input handling); use small, targeted sets against your lab, not "
             "blind floods. The **Scanner** (Pro) crawls and flags issues — treat "
             "results as leads. Always keep scope tight so you never touch anything "
             "out of bounds.",
             exercises=[mcq("Scanner/Intruder results are:", ["Confirmed vulns",
                            "Leads to verify", "Exploits", "Patches"], "Leads to verify",
                            "tool-web-proxy", "Verify everything manually.")]),
       ],
       [mcq("Burp default listener?", ["127.0.0.1:8080", "0.0.0.0:80", "127.0.0.1:443",
            "8000"], "127.0.0.1:8080", "tool-web-proxy", "127.0.0.1:8080."),
        short("Tab for resending one request?", "Repeater", "tool-web-proxy", "Repeater."),
        mcq("To read HTTPS in Burp you must:", ["Disable TLS", "Install Burp's CA cert",
            "Use HTTP only", "Nothing"], "Install Burp's CA cert", "tool-web-proxy",
            "Trust Burp's CA.")],
       lab="web-security-lab"),

    _c("tool-zap", "OWASP ZAP: Open-Source Web Proxy",
       "The free, open-source alternative to Burp for authorised web testing.",
       "intermediate", "web", ["tool-burp"],
       [
           L("ZAP basics", "intermediate", 15, "tool-web-proxy",
             "ZAP offers an intercepting proxy, an automated and manual scanner, "
             "and a spider/crawler. Use the **HUD** in-browser or the desktop UI. "
             "Set the browser proxy, import ZAP's cert, and define a strict "
             "**context/scope** so automation stays inside your lab app.\n\n" + AUTH,
             exercises=[short("ZAP, like Burp, is an intercepting ___.", "proxy",
                              "tool-web-proxy", "An intercepting proxy.")],
             hints=["Define a scope/context before running the active scanner."]),
           L("Spider, passive & active scan", "intermediate", 15, "tool-web-proxy",
             "The **spider** discovers URLs; the **passive scan** flags issues from "
             "observed traffic (safe); the **active scan** sends test payloads and "
             "must only run inside your defined scope. ZAP scripts and the API let "
             "you automate checks in CI for your own apps.",
             exercises=[mcq("Which ZAP scan sends test payloads?",
                            ["Passive", "Active", "Spider", "None"], "Active",
                            "tool-web-proxy", "Active scanning sends payloads.")]),
       ],
       [short("ZAP is an intercepting ___.", "proxy", "tool-web-proxy", "Proxy."),
        mcq("Safe, observation-only scan?", ["Active", "Passive", "Intruder", "Brute"],
            "Passive", "tool-web-proxy", "Passive scanning only observes.")],
       lab="web-security-lab"),

    _c("tool-content-discovery", "Content Discovery: gobuster, ffuf & feroxbuster",
       "Find hidden paths, files, subdomains and parameters with wordlists.",
       "intermediate", "web", ["web-application-security"],
       [
           L("Directory & file brute-forcing", "intermediate", 20, "tool-content-discovery",
             "Apps often have unlinked paths. Content-discovery tools request many "
             "candidate names from a wordlist and report what exists.\n\n```\n"
             "gobuster dir -u http://10.200.0.10 -w /usr/share/wordlists/dirb/common.txt\n"
             "ffuf -u http://10.200.0.10/FUZZ -w common.txt -mc 200,301,403\n"
             "feroxbuster -u http://10.200.0.10 -w common.txt\n```\n"
             "`FUZZ` is ffuf's placeholder; `-mc` matches status codes. Wordlist "
             "choice matters more than the tool.\n\n" + AUTH,
             exercises=[cmd("ffuf placeholder keyword in a URL?", "FUZZ",
                            "tool-content-discovery", "`FUZZ` marks the inject point.")],
             hints=["SecLists is the go-to wordlist collection.",
                    "Match/limit by status code and size to cut noise."]),
           L("Vhosts, DNS & parameters", "intermediate", 15, "tool-content-discovery",
             "The same idea fuzzes more than paths:\n\n```\n"
             "ffuf -u http://10.200.0.10 -H 'Host: FUZZ.site.lab' -w subs.txt   # vhosts\n"
             "gobuster dns -d site.lab -w subs.txt                               # subdomains\n"
             "ffuf -u 'http://10.200.0.10/page?FUZZ=1' -w params.txt             # parameters\n```\n"
             "Filter results by response size (`-fs`) to drop the uniform 'not "
             "found' noise.",
             exercises=[short("ffuf flag to filter by response size?", "-fs",
                              "tool-content-discovery", "`-fs` filters by size.")]),
       ],
       [cmd("ffuf URL placeholder?", "FUZZ", "tool-content-discovery", "FUZZ."),
        short("Most important factor besides the tool?", "wordlist",
              "tool-content-discovery", "Wordlist quality.")],
       lab="web-security-lab"),

    _c("tool-sqlmap", "sqlmap: Testing & Fixing SQL Injection",
       "Confirm, understand and remediate SQLi on your own vulnerable lab apps.",
       "hard", "web", ["sql-injection-labs", "tool-burp"],
       [
           L("Running sqlmap safely in a lab", "hard", 20, "sql-injection",
             "sqlmap automates detecting and exploiting SQL injection — run it only "
             "against the intentionally-vulnerable Pwnforge web lab you own.\n\n```\n"
             "sqlmap -u 'http://10.200.0.10/item?id=1' --batch\n"
             "sqlmap -r request.txt --batch            # from a saved Burp request\n"
             "sqlmap -u '...' --dbs                     # enumerate databases\n```\n"
             "Save a request from Burp and feed it with `-r` so auth/headers are "
             "preserved. The goal here is to *prove* the bug and then fix it.\n\n" + AUTH,
             exercises=[cmd("Feed sqlmap a saved request file (flag)?", "-r",
                            "sql-injection", "`-r request.txt`.")],
             hints=["`-r` reuses a Burp-saved request (cookies, headers, method)."]),
           L("From finding to fix", "hard", 20, "vuln-remediation",
             "Once confirmed, the professional step is remediation: convert the "
             "offending query to a **parameterised statement**, re-test the same "
             "input, and confirm sqlmap can no longer inject. Record before/after "
             "evidence. Finding the bug is half the job; proving the fix is the "
             "other half.",
             exercises=[mcq("The definitive SQLi fix:", ["Blocklist quotes",
                            "Parameterised queries", "Hide errors", "Rate limit"],
                            "Parameterised queries", "sql-injection", "Parameterisation.")]),
       ],
       [cmd("sqlmap flag to load a saved request?", "-r", "sql-injection", "`-r`."),
        mcq("After confirming SQLi you should:", ["Move on", "Parameterise and re-test",
            "Delete logs", "Ignore"], "Parameterise and re-test", "vuln-remediation",
            "Fix then verify.")],
       cprereqs=["sql-injection"], lab="web-security-lab"),

    # ------------------------------------------------- Exploitation framework
    _c("tool-metasploit", "Metasploit Framework (Lab Use)",
       "Use the framework's modules, sessions and workflow against owned lab "
       "targets — and understand how defenders detect it.",
       "hard", "pentest", ["penetration-testing-methodology", "tool-nmap"],
       [
           L("msfconsole & the module model", "hard", 20, "tool-exploitation-frameworks",
             "Metasploit organises capability into **modules**: `auxiliary` "
             "(scanners/enum), `exploit`, `payload`, `post`, `encoder`.\n\n```\n"
             "msfconsole\nsearch type:auxiliary smb\nuse auxiliary/scanner/smb/smb_version\n"
             "set RHOSTS 10.200.0.10\nrun\n```\n"
             "`show options` lists required settings; `info` explains a module. "
             "Start with auxiliary scanners to enumerate your lab before anything "
             "else.\n\n" + AUTH,
             exercises=[short("Module type for scanners/enumeration?", "auxiliary",
                              "tool-exploitation-frameworks", "auxiliary modules.")],
             hints=["`show options` reveals what a module needs (RHOSTS etc.).",
                    "Prefer auxiliary scanners first to map the lab."]),
           L("Exploits, payloads & sessions", "hard", 20, "tool-exploitation-frameworks",
             "An `exploit` module delivers a `payload`; a staged payload opens a "
             "**session** (e.g. Meterpreter) back to a handler.\n\n```\n"
             "use exploit/...\nset RHOSTS 10.200.0.10\nset PAYLOAD <payload>\n"
             "set LHOST <your-lab-ip>\nexploit\nsessions -l\n```\n"
             "`LHOST` is where the session connects back — your attacker host on "
             "the lab network. Everything stays inside the isolated lab.",
             exercises=[mcq("`LHOST` specifies:", ["The target", "Your listener/host",
                            "A port only", "The payload"], "Your listener/host",
                            "tool-exploitation-frameworks", "Where the session connects back.")],
             walkthrough=[wstep("Start an infra lab", "Owned targets on an isolated net."),
                          wstep("Enumerate", "Use an auxiliary scanner module first."),
                          wstep("Configure", "`set RHOSTS`, `PAYLOAD`, `LHOST`."),
                          wstep("Review sessions", "`sessions -l`; clean up when done.")]),
           L("Post-exploitation & detection", "hard", 15, "detection-engineering",
             "`post` modules gather information after access. Crucially, learn the "
             "defender's view: framework activity leaves artefacts (process "
             "creation, network patterns, auth events) that detections key on. "
             "Knowing how the tool behaves makes you a better blue-teamer.",
             exercises=[short("Module category that runs after access?", "post",
                              "tool-exploitation-frameworks", "post modules.")]),
       ],
       [short("Non-exploit scanner module type?", "auxiliary", "tool-exploitation-frameworks",
              "auxiliary."),
        mcq("LHOST is:", ["The target", "Your connect-back host", "A CVE", "A wordlist"],
            "Your connect-back host", "tool-exploitation-frameworks", "Your host/listener."),
        short("Interactive session type Metasploit often opens?", "meterpreter",
              "tool-exploitation-frameworks", "Meterpreter.")],
       lab="enterprise-identity-lab"),

    _c("tool-netcat", "netcat & socat: The Network Swiss Army Knife",
       "Make and manage raw TCP/UDP connections for testing and transfers.",
       "easy", "pentest", ["networking-fundamentals"],
       [
           L("Listeners, clients & banners", "easy", 15, "tool-netcat",
             "netcat moves bytes over the network.\n\n```\n"
             "nc -lvnp 4444                 # listen on 4444 (verbose, no DNS)\n"
             "nc 10.200.0.10 80             # connect; then type an HTTP request\n"
             "nc -nv 10.200.0.10 22         # grab an SSH banner\n```\n"
             "A listener on one lab host plus a client on another is the simplest "
             "way to test connectivity and read service banners.",
             exercises=[cmd("Listen verbosely on TCP 4444 (nc flags)?", "nc -lvnp 4444",
                            "tool-netcat", "`-l` listen, `-v` verbose, `-n` no DNS, `-p` port.")],
             hints=["`-lvnp` is the classic listener combo."]),
           L("File transfer & socat", "easy", 15, "tool-netcat",
             "Pipe data across a connection:\n\n```\n"
             "# receiver:\nnc -lvnp 4444 > out.bin\n# sender:\nnc 10.200.0.10 4444 < in.bin\n```\n"
             "`socat` is netcat's more capable cousin (TLS, PTYs, bidirectional "
             "relays): `socat - TCP:10.200.0.10:80`. Both are invaluable for "
             "testing and for stabilising shells in your labs.",
             exercises=[short("More capable netcat alternative (TLS/PTY)?", "socat",
                              "tool-netcat", "socat.")]),
       ],
       [cmd("Classic nc listener flags for port 4444?", "nc -lvnp 4444", "tool-netcat",
            "`-lvnp`."),
        short("netcat cousin supporting TLS/PTYs?", "socat", "tool-netcat", "socat.")],
       lab="network-basics-lab"),

    _c("tool-proxychains", "Pivoting: proxychains, Tor & SSH Tunnels",
       "Route tools through tunnels to reach segmented lab networks.",
       "advanced", "pentest", ["tool-netcat", "network-segmentation"],
       [
           L("SSH tunnels", "advanced", 20, "tool-proxying",
             "SSH can forward ports to reach hosts you can only see from a jump "
             "box in your lab.\n\n```\n"
             "ssh -L 8080:10.10.0.5:80 user@jump      # local forward\n"
             "ssh -D 1080 user@jump                   # dynamic SOCKS proxy\n```\n"
             "A dynamic `-D` proxy turns SSH into a SOCKS proxy other tools can use "
             "to reach an internal lab subnet.",
             exercises=[cmd("SSH flag for a dynamic SOCKS proxy?", "-D",
                            "tool-proxying", "`-D` opens a SOCKS proxy.")],
             hints=["`-L` = local forward, `-D` = SOCKS proxy, `-R` = remote forward."]),
           L("proxychains & Tor", "advanced", 15, "tool-proxying",
             "proxychains forces a tool's traffic through a proxy (e.g. your SSH "
             "SOCKS or Tor): `proxychains nmap -sT 10.10.0.0/24`. Set the proxy in "
             "`/etc/proxychains.conf`. Tor provides anonymity for authorised OSINT, "
             "but note many scans don't work well over Tor (no UDP, slow).",
             exercises=[mcq("proxychains is used to:", ["Speed up scans",
                            "Route a tool through a proxy", "Crack hashes", "Fuzz"],
                            "Route a tool through a proxy", "tool-proxying",
                            "It forces traffic via a proxy.")]),
       ],
       [cmd("SSH dynamic SOCKS flag?", "-D", "tool-proxying", "`-D`."),
        mcq("proxychains routes a tool through a:", ["GPU", "Proxy", "Database", "Shell"],
            "Proxy", "tool-proxying", "A proxy.")]),

    _c("tool-http-clients", "curl & HTTPie: Crafting HTTP Requests",
       "Drive and inspect web APIs and apps straight from the terminal.",
       "easy", "web", ["http-https"],
       [
           L("curl essentials", "easy", 15, "tool-http-clients",
             "curl makes any HTTP request, scriptably.\n\n```\n"
             "curl -i http://10.200.0.10/            # show response headers\n"
             "curl -X POST -d 'a=1&b=2' http://.../x # form POST\n"
             "curl -H 'Authorization: Bearer T' .../ # custom header\n"
             "curl -b 'session=...' .../             # send a cookie\n"
             "curl -sk https://.../ | jq .           # TLS, pipe JSON to jq\n```\n"
             "`-i` shows headers, `-s` is quiet, `-k` skips cert checks (labs only).",
             exercises=[cmd("curl flag to include response headers?", "-i",
                            "tool-http-clients", "`-i` includes headers.")],
             hints=["Pipe JSON APIs through `jq` to read them."]),
           L("HTTPie for humans", "easy", 10, "tool-http-clients",
             "HTTPie is a friendlier client: `http POST 10.200.0.10/login "
             "user=admin pass=admin` sends JSON by default with colourised output. "
             "Great for exploring an API quickly before scripting it with curl.",
             exercises=[short("Friendly curl alternative with colour output?", "httpie",
                              "tool-http-clients", "HTTPie.")]),
       ],
       [cmd("curl flag to show headers?", "-i", "tool-http-clients", "`-i`."),
        short("Tool to pretty-print/filter JSON in a pipe?", "jq", "tool-http-clients",
              "jq.")]),

    # ------------------------------------------------- Password auditing
    _c("tool-hydra", "Hydra: Authorised Authentication Testing",
       "Test login resilience against guessing on systems you own.",
       "hard", "pentest", ["authentication-security", "tool-nmap"],
       [
           L("How Hydra works", "hard", 15, "tool-password-auditing",
             "Hydra tries username/password combinations against a service to "
             "measure resilience — run it only against your own lab logins.\n\n```\n"
             "hydra -l admin -P rockyou.txt ssh://10.200.0.10\n"
             "hydra -L users.txt -P pass.txt 10.200.0.10 http-post-form \\\n"
             "  '/login:user=^USER^&pass=^PASS^:Invalid'\n```\n"
             "`^USER^`/`^PASS^` are placeholders; the trailing string is the "
             "failure marker. The defensive lesson: rate-limiting, lockout and MFA "
             "make this ineffective.\n\n" + AUTH,
             exercises=[mcq("What defeats online password guessing?",
                            ["Longer URLs", "Rate-limiting/lockout/MFA", "Faster CPU",
                             "More threads"], "Rate-limiting/lockout/MFA",
                            "tool-password-auditing", "Throttle, lock out, add MFA.")],
             hints=["`-l` single user, `-L` user list; `-p`/`-P` likewise for passwords."]),
       ],
       [mcq("Best defence against Hydra-style guessing:", ["Hide the login",
            "Rate-limit + lockout + MFA", "Bigger wordlist", "UDP"],
            "Rate-limit + lockout + MFA", "tool-password-auditing", "Throttle + MFA."),
        short("Hydra flag for a password list?", "-P", "tool-password-auditing", "`-P`.")]),

    _c("tool-john", "John the Ripper: Password Auditing",
       "Audit password-hash strength offline from data you're authorised to test.",
       "hard", "pentest", ["password-security-auditing"],
       [
           L("Formats, wordlists & rules", "hard", 20, "tool-password-auditing",
             "John cracks captured hashes offline to measure strength.\n\n```\n"
             "john --list=formats | head\n"
             "john --wordlist=rockyou.txt hashes.txt\n"
             "john --wordlist=rockyou.txt --rules hashes.txt\n"
             "john --show hashes.txt\n```\n"
             "`--rules` mutates wordlist entries (capitalise, append digits). Use "
             "only on hashes from your own lab/accounts. The takeaway: long, unique "
             "passphrases and slow KDFs resist this.",
             exercises=[cmd("Show already-cracked results (john flag)?", "--show",
                            "tool-password-auditing", "`--show` lists cracked.")],
             hints=["`--rules` applies mutations; `rockyou.txt` is the classic list."]),
       ],
       [cmd("John flag to apply mutation rules?", "--rules", "tool-password-auditing",
            "`--rules`."),
        short("Property that best resists cracking: length & ___.", "uniqueness",
              "password-security", "Length + uniqueness.")]),

    _c("tool-hashcat", "Hashcat: GPU Password Auditing",
       "Fast, GPU-accelerated hash auditing and the attack modes that matter.",
       "hard", "pentest", ["tool-john"],
       [
           L("Hash modes & attack modes", "hard", 20, "tool-password-auditing",
             "Hashcat needs the **hash mode** (`-m`) and **attack mode** (`-a`).\n\n"
             "```\nhashcat -m 0 -a 0 hashes.txt rockyou.txt     # MD5, straight wordlist\n"
             "hashcat -m 1000 -a 0 ntlm.txt rockyou.txt     # NTLM\n"
             "hashcat -m 0 -a 3 hashes.txt '?l?l?l?l?d?d'    # mask (brute)\n"
             "hashcat --show -m 0 hashes.txt\n```\n"
             "`-a 0` = wordlist, `-a 3` = mask/brute. `hashid`/`hashcat --identify` "
             "helps spot the mode. Audit only hashes you're authorised to test.",
             exercises=[cmd("Hashcat flag that sets the hash type?", "-m",
                            "tool-password-auditing", "`-m` sets hash mode.")],
             hints=["`-a 0` wordlist, `-a 3` mask; `-m` picks the hash type."]),
       ],
       [cmd("Hashcat attack-mode flag?", "-a", "tool-password-auditing", "`-a`."),
        mcq("`-a 3` is:", ["Wordlist", "Mask/brute", "Combinator", "Rule"], "Mask/brute",
            "tool-password-auditing", "Mask attack.")]),

    # ------------------------------------------------- Windows / AD tooling
    _c("tool-smb-enum", "SMB & LDAP Enumeration Toolkit",
       "enum4linux, smbclient, rpcclient and ldapsearch for Windows/AD recon.",
       "hard", "active-directory", ["tool-nmap", "active-directory-fundamentals"],
       [
           L("SMB shares & sessions", "hard", 20, "tool-ad-tooling",
             "Enumerate SMB on owned lab hosts.\n\n```\n"
             "enum4linux -a 10.200.0.10\n"
             "smbclient -L //10.200.0.10 -N          # list shares, null session\n"
             "smbclient //10.200.0.10/share -N       # connect to a share\n```\n"
             "Null/anonymous sessions and over-shared folders are classic "
             "misconfigurations — the fix is tightening share ACLs and disabling "
             "anonymous access.\n\n" + AUTH,
             exercises=[cmd("List SMB shares with a null session (smbclient ...)?",
                            "smbclient -L //10.0.0.5 -N", "tool-ad-tooling",
                            "`-L` lists shares, `-N` no password.")],
             hints=["`-N` attempts a null (anonymous) session."]),
           L("LDAP & RPC", "hard", 15, "tool-ad-tooling",
             "`ldapsearch` queries the directory; `rpcclient` enumerates users and "
             "policy.\n\n```\n"
             "ldapsearch -x -H ldap://10.200.0.10 -b 'dc=lab,dc=local'\n"
             "rpcclient -U '' -N 10.200.0.10 -c enumdomusers\n```\n"
             "This maps users, groups and policy — the same inventory a defender "
             "should review for over-exposure.",
             exercises=[short("Tool to query a directory over LDAP?", "ldapsearch",
                              "tool-ad-tooling", "ldapsearch.")]),
       ],
       [cmd("smbclient flag to list shares?", "-L", "tool-ad-tooling", "`-L`."),
        short("Null/anonymous SMB session flag?", "-N", "tool-ad-tooling", "`-N`.")],
       lab="enterprise-identity-lab"),

    _c("tool-impacket", "Impacket: Windows Protocol Tooling (Lab)",
       "Python tools that speak SMB/MSRPC/Kerberos for authorised AD work.",
       "advanced", "active-directory", ["tool-smb-enum"],
       [
           L("The Impacket example scripts", "advanced", 20, "tool-ad-tooling",
             "Impacket ships example scripts that implement Windows protocols.\n\n```\n"
             "impacket-smbclient lab/user:pass@10.200.0.10\n"
             "impacket-GetUserSPNs lab/user:pass -dc-ip 10.200.0.10\n"
             "impacket-secretsdump lab/user:pass@10.200.0.10\n```\n"
             "They're the backbone of AD testing (and of understanding attacks so "
             "you can detect them). Use only against your owned lab domain.\n\n" + AUTH,
             exercises=[mcq("Impacket scripts primarily implement:",
                            ["Web scanning", "Windows protocols (SMB/RPC/Kerberos)",
                             "Password cracking", "Packet capture"],
                            "Windows protocols (SMB/RPC/Kerberos)", "tool-ad-tooling",
                            "They speak Windows protocols.")],
             hints=["GetUserSPNs relates to Kerberoasting; secretsdump to credential material."]),
       ],
       [mcq("Impacket is a toolkit for:", ["GPU cracking", "Windows protocols",
            "Fuzzing", "Forensics"], "Windows protocols", "tool-ad-tooling",
            "SMB/RPC/Kerberos etc."),
        short("Impacket script to request service tickets (GetUser___)?", "SPNs",
              "tool-ad-tooling", "GetUserSPNs.")],
       lab="enterprise-identity-lab"),

    _c("tool-crackmapexec", "NetExec / CrackMapExec: AD Assessment (Lab)",
       "Sweep and assess Windows/AD estates at scale in your lab.",
       "advanced", "active-directory", ["tool-impacket"],
       [
           L("Sweeping with nxc/cme", "advanced", 20, "tool-ad-tooling",
             "NetExec (the maintained successor to CrackMapExec) checks many hosts "
             "for access, shares and config.\n\n```\n"
             "nxc smb 10.200.0.0/24\n"
             "nxc smb 10.200.0.10 -u user -p pass --shares\n"
             "nxc smb 10.200.0.10 -u user -p pass --users\n```\n"
             "It quickly shows where a credential works — invaluable both for "
             "assessment and for spotting over-broad access to remediate.\n\n" + AUTH,
             exercises=[short("Maintained successor to CrackMapExec (command)?", "nxc",
                              "tool-ad-tooling", "NetExec (`nxc`).")],
             hints=["`--shares` and `--users` are common enumeration flags."]),
       ],
       [short("NetExec command name?", "nxc", "tool-ad-tooling", "nxc."),
        mcq("A credential working on many hosts indicates:", ["Good hygiene",
            "Over-broad access to fix", "A patch", "Nothing"], "Over-broad access to fix",
            "tool-ad-tooling", "Reuse/over-privilege to remediate.")],
       lab="enterprise-identity-lab"),

    _c("tool-bloodhound", "BloodHound: AD Attack-Path Analysis (Lab)",
       "Visualise and reason about Active Directory privilege relationships.",
       "advanced", "active-directory", ["tool-crackmapexec"],
       [
           L("Collect & analyse", "advanced", 20, "tool-ad-tooling",
             "A collector (e.g. SharpHound/bloodhound-python) gathers directory "
             "relationships; BloodHound graphs them so you can see paths from a "
             "low-privilege object to high-value ones.\n\n```\n"
             "bloodhound-python -u user -p pass -d lab.local -ns 10.200.0.10 -c all\n```\n"
             "Then run queries like *Shortest Path to Domain Admins*. For "
             "defenders, this is the single best way to find and cut dangerous "
             "privilege paths before an attacker uses them.\n\n" + AUTH,
             exercises=[mcq("BloodHound helps you see AD:",
                            ["Packet loss", "Privilege/attack paths", "Web bugs",
                             "Hashes"], "Privilege/attack paths", "tool-ad-tooling",
                            "It graphs privilege relationships.")],
             hints=["'Shortest Path to Domain Admins' is the classic query."]),
       ],
       [mcq("BloodHound visualises:", ["Traffic", "AD privilege paths", "Memory",
            "Disks"], "AD privilege paths", "tool-ad-tooling", "Privilege graphs."),
        short("Python collector for BloodHound: bloodhound-___?", "python",
              "tool-ad-tooling", "bloodhound-python.")],
       lab="enterprise-identity-lab"),

    _c("tool-responder", "Responder: LLMNR/NBT-NS Analysis & Defence (Lab)",
       "Understand name-resolution poisoning and, crucially, how to stop it.",
       "advanced", "defensive", ["tool-smb-enum"],
       [
           L("What Responder demonstrates", "advanced", 15, "tool-ad-tooling",
             "On a lab network, Responder answers broadcast name-resolution queries "
             "(LLMNR/NBT-NS/mDNS) to show how misconfigured networks leak "
             "authentication material: `responder -I eth0`. The *point* for most "
             "learners is defensive — disabling LLMNR/NBT-NS and enabling SMB "
             "signing removes the weakness entirely.\n\n" + AUTH,
             exercises=[mcq("The durable fix Responder teaches:",
                            ["Faster NICs", "Disable LLMNR/NBT-NS + SMB signing",
                             "More RAM", "Bigger subnets"],
                            "Disable LLMNR/NBT-NS + SMB signing", "tool-ad-tooling",
                            "Remove the weak broadcast protocols.")],
             hints=["LLMNR/NBT-NS are the broadcast protocols to disable."]),
       ],
       [mcq("Responder abuses which protocols?", ["HTTP/HTTPS", "LLMNR/NBT-NS/mDNS",
            "SSH/SFTP", "DNS over TLS"], "LLMNR/NBT-NS/mDNS", "tool-ad-tooling",
            "Broadcast name resolution."),
        short("Enable SMB ___ to resist relay.", "signing", "tool-ad-tooling", "SMB signing.")],
       lab="enterprise-identity-lab"),

    # ------------------------------------------------- Reverse engineering
    _c("tool-ghidra", "Ghidra: Reverse Engineering",
       "Disassemble and decompile binaries with the NSA's open-source SRE suite.",
       "advanced", "reverse", ["reverse-engineering-fundamentals"],
       [
           L("Projects, disassembly & decompiler", "advanced", 20, "tool-re-tooling",
             "Ghidra imports a binary, auto-analyses it, and shows disassembly "
             "alongside a C-like **decompiler** view. Navigate the Symbol Tree and "
             "function list; rename variables and add comments as you understand "
             "them. The decompiler is the fastest way to grasp logic before diving "
             "into assembly. Analyse only binaries you're permitted to, inside "
             "isolation.",
             exercises=[mcq("Ghidra's standout feature vs a plain disassembler:",
                            ["GPU cracking", "A decompiler (C-like view)", "A web proxy",
                             "Packet capture"], "A decompiler (C-like view)",
                            "tool-re-tooling", "The decompiler.")],
             hints=["Rename symbols as you learn them — future-you will thank you."]),
           L("Strings, xrefs & patching", "advanced", 15, "tool-re-tooling",
             "`Window → Defined Strings` finds literals; cross-references (xrefs) "
             "show who calls/uses a function or string — the fastest path to the "
             "interesting code. Ghidra can also patch instructions and export, "
             "useful for CrackMe-style lab challenges.",
             exercises=[short("Show who references a function/string: x___.", "refs",
                              "tool-re-tooling", "Cross-references (xrefs).")]),
       ],
       [mcq("Ghidra provides a:", ["Decompiler", "GPU cracker", "Proxy", "Fuzzer"],
            "Decompiler", "tool-re-tooling", "C-like decompiler."),
        short("Follow who uses a function via cross-___.", "references", "tool-re-tooling",
              "Cross-references.")],
       lab="reverse-engineering-lab"),

    _c("tool-radare2", "radare2 / rizin: CLI Reverse Engineering",
       "Fast, scriptable command-line binary analysis.",
       "advanced", "reverse", ["tool-ghidra"],
       [
           L("Opening and navigating", "advanced", 20, "tool-re-tooling",
             "radare2 is terminal-driven.\n\n```\nr2 ./binary\naaa        # analyse all\n"
             "afl        # list functions\ns main      # seek to main\n"
             "pdf        # print disassembly of current function\nVV         # visual graph\n```\n"
             "Commands compose: a letter per concept (`a` analyse, `p` print, `s` "
             "seek). It's steep but fast once learned, and fully scriptable.",
             exercises=[cmd("radare2 command to analyse everything?", "aaa",
                            "tool-re-tooling", "`aaa` runs full analysis.")],
             hints=["`afl` lists functions; `pdf` disassembles the current one."]),
       ],
       [cmd("Analyse-all command in r2?", "aaa", "tool-re-tooling", "`aaa`."),
        short("r2 command to list functions (af_)?", "afl", "tool-re-tooling", "afl.")],
       lab="reverse-engineering-lab"),

    _c("tool-gdb", "gdb & pwndbg: Dynamic Analysis",
       "Run, break, step and inspect program state at runtime.",
       "advanced", "reverse", ["tool-ghidra", "memory-safety"],
       [
           L("Breakpoints, stepping & inspection", "advanced", 20, "tool-re-tooling",
             "gdb runs a program under your control; pwndbg/GEF add security-focused "
             "views.\n\n```\ngdb ./binary\nb main          # breakpoint\nrun\n"
             "ni / si         # next / step instruction\ninfo registers\n"
             "x/16xw $sp      # examine 16 words at the stack pointer\n```\n"
             "Watching registers and memory as code executes reveals what static "
             "analysis can't. Do this on binaries you're authorised to analyse, in "
             "isolation.",
             exercises=[cmd("gdb command to set a breakpoint at main?", "b main",
                            "tool-re-tooling", "`b main` breaks at main.")],
             hints=["`x/` examines memory; `info registers` dumps CPU state."]),
       ],
       [cmd("gdb breakpoint command (short form)?", "b", "tool-re-tooling", "`b`."),
        short("pwndbg/GEF are gdb ___ for security analysis.", "plugins", "tool-re-tooling",
              "Extensions/plugins.")],
       lab="reverse-engineering-lab"),

    # ------------------------------------------------- Forensics tooling
    _c("tool-volatility", "Volatility: Memory Forensics",
       "Extract processes, connections and artefacts from memory images.",
       "advanced", "forensics", ["digital-forensics"],
       [
           L("Profiles/symbols & core plugins", "advanced", 20, "tool-forensics-tooling",
             "Volatility analyses RAM captures.\n\n```\n"
             "vol -f mem.raw windows.pslist          # processes\n"
             "vol -f mem.raw windows.netscan         # network connections\n"
             "vol -f mem.raw windows.pstree          # process tree\n"
             "vol -f mem.raw windows.cmdline         # command lines\n```\n"
             "(Volatility 3 auto-detects symbols.) Memory reveals what disk can't — "
             "running processes, injected code, and network state at capture time.",
             exercises=[short("Volatility plugin to list processes (windows.ps___)?",
                              "pslist", "tool-forensics-tooling", "windows.pslist.")],
             hints=["Compare pslist vs pstree to spot odd parent/child relationships."]),
       ],
       [short("Volatility plugin for network connections (windows.net___)?", "scan",
              "tool-forensics-tooling", "windows.netscan."),
        mcq("Memory forensics reveals what disk often can't:",
            ["Nothing", "Running processes & volatile state", "File names only",
             "Partitions"], "Running processes & volatile state", "tool-forensics-tooling",
            "Volatile runtime state.")],
       lab="forensics-workstation-lab"),

    _c("tool-autopsy", "Autopsy & The Sleuth Kit: Disk Forensics",
       "Examine disk images, recover files and build timelines.",
       "hard", "forensics", ["digital-forensics"],
       [
           L("The Sleuth Kit CLI & Autopsy GUI", "hard", 20, "tool-forensics-tooling",
             "The Sleuth Kit (TSK) provides CLI tools; Autopsy is the GUI over them.\n\n"
             "```\nmmls disk.img            # partition layout\nfls -r -o 2048 disk.img  # list files (incl. deleted)\n"
             "icat -o 2048 disk.img 1234 > out   # extract a file by inode\n```\n"
             "Autopsy adds keyword search, timelines and reporting. Always work "
             "from a verified **copy** and hash everything (chain of custody).",
             exercises=[mcq("You should analyse:", ["The original disk",
                            "A verified copy/image", "Live production", "Nothing"],
                            "A verified copy/image", "tool-forensics-tooling",
                            "Never the only copy.")],
             hints=["`mmls` shows partitions; `fls` lists files incl. deleted."]),
       ],
       [mcq("Autopsy is a GUI over:", ["Volatility", "The Sleuth Kit", "Wireshark",
            "Nmap"], "The Sleuth Kit", "tool-forensics-tooling", "TSK."),
        short("Verify evidence integrity with a ___.", "hash", "tool-forensics-tooling",
              "Hashes.")],
       lab="forensics-workstation-lab"),

    _c("tool-cyberchef", "CyberChef & Data Decoding",
       "The 'cyber swiss army knife' for encoding, decoding and data analysis.",
       "easy", "defensive", ["cybersecurity-fundamentals"],
       [
           L("Recipes & common operations", "easy", 15, "tool-data-decoding",
             "CyberChef chains *operations* into a **recipe**: base64 decode, URL "
             "decode, from-hex, gunzip, XOR, magic-detect, and hundreds more. Drop "
             "data in, build a recipe, read the output. `hashid` or "
             "`hashcat --identify` names an unknown hash so you pick the right mode. "
             "Essential for CTFs, log triage and quick artefact analysis.",
             exercises=[mcq("A CyberChef chain of operations is called a:",
                            ["Payload", "Recipe", "Module", "Session"], "Recipe",
                            "tool-data-decoding", "A recipe.")],
             hints=["The 'Magic' operation guesses encodings for you."]),
       ],
       [short("A CyberChef operation chain is a ___.", "recipe", "tool-data-decoding",
              "Recipe."),
        short("Tool/flag to identify an unknown hash type?", "hashid", "tool-data-decoding",
              "hashid / --identify.")]),
]
