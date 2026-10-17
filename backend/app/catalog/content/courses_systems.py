"""Systems & infrastructure foundations: Linux admin, networking, Windows, AD."""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, cmd, lesson, mcq, short,
)


def _c(id, title, desc, difficulty, category, spec, prereqs, lessons, qs,
       cprereqs=None, tags=None, lab=None):
    return course(id, title, desc, difficulty, category, specialization=spec,
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=tags or [category], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


COURSES = [
    _c("linux-administration", "Linux Administration",
       "Manage services, users, packages and systemd on Debian systems.",
       "easy", "linux", "linux", ["linux-fundamentals"],
       [
           lesson("Users and groups", "easy", 15, "linux-administration",
                  "User accounts live in `/etc/passwd`; group membership in "
                  "`/etc/group`. Add users with `useradd`/`adduser`, grant sudo via "
                  "group membership (e.g. `sudo`), and review `/etc/sudoers` carefully: "
                  "an over-broad sudo rule is a frequent privilege-escalation path. "
                  "Audit with `getent passwd` and `id <user>`.",
                  exercises=[cmd("Command to show a user's uid, gid and groups?", "id",
                                 "linux-administration", "`id <user>` shows identity info.")],
                  hints=["`/etc/sudoers` controls elevated access — review it with `visudo`."]),
           lesson("Packages and updates", "easy", 15, "linux-administration",
                  "Debian uses APT. `apt update` refreshes the package index; "
                  "`apt upgrade` applies updates; `apt install <pkg>` adds software. "
                  "Keeping packages patched is one of the highest-value security "
                  "controls. Unattended-upgrades can automate security patches. "
                  "Know which version is installed with `dpkg -l <pkg>`.",
                  exercises=[cmd("APT subcommand to refresh the package index?", "update",
                                 "linux-administration", "`apt update` refreshes the index.")]),
           lesson("systemd services", "easy", 15, "linux-administration",
                  "systemd manages services as *units*. `systemctl start/stop/enable "
                  "<unit>` controls them; `systemctl status <unit>` and `journalctl -u "
                  "<unit>` show state and logs. Disabling unused services reduces attack "
                  "surface — a core hardening step.",
                  exercises=[cmd("Command to view logs for the unit ssh?",
                                 "journalctl -u ssh", "log-analysis",
                                 "`journalctl -u <unit>` shows a unit's logs.")]),
       ],
       [mcq("Which file defines sudo privileges?",
            ["/etc/passwd", "/etc/sudoers", "/etc/group", "/etc/hosts"], "/etc/sudoers",
            "linux-administration", "`/etc/sudoers` governs sudo access."),
        cmd("Enable a service at boot with systemctl ___ <unit>", "enable",
            "linux-administration", "`systemctl enable` sets a unit to start at boot."),
        mcq("Highest-value routine security control here?",
            ["Changing the MOTD", "Applying patches", "Renaming root", "Disabling colour"],
            "Applying patches", "infrastructure-hardening", "Patching closes known holes.")],
       cprereqs=["linux-fundamentals"], lab="linux-admin-lab"),

    _c("networking-fundamentals", "Networking Fundamentals",
       "IP addressing, ports, protocols and routing — how machines talk.",
       "beginner", "networking", "infrastructure", ["cybersecurity-fundamentals"],
       [
           lesson("IP addressing and subnets", "beginner", 15, "networking-fundamentals",
                  "An IPv4 address (e.g. `10.0.5.23`) plus a subnet mask (`/24`) defines a "
                  "host and the network it belongs to. A `/24` has 256 addresses (254 "
                  "usable). Hosts on the same subnet talk directly; otherwise traffic goes "
                  "via a gateway/router. Private ranges (`10/8`, `172.16/12`, `192.168/16`) "
                  "are used inside networks like Pwnforge's isolated labs.",
                  exercises=[short("How many usable hosts in a /24?", "254",
                                   "networking-fundamentals", "256 total minus network and broadcast.")],
                  hints=["Usable = 2^(32-prefix) - 2."]),
           lesson("Ports and protocols", "beginner", 15, "networking-fundamentals",
                  "TCP and UDP multiplex services using port numbers. Well-known ports: "
                  "22 SSH, 53 DNS, 80 HTTP, 443 HTTPS, 445 SMB, 3389 RDP. TCP is "
                  "connection-oriented (handshake, ordered, reliable); UDP is "
                  "connectionless. Identifying which ports are open and what speaks on "
                  "them is the start of any enumeration.",
                  exercises=[short("Default port for HTTPS?", "443", "networking-fundamentals",
                                   "HTTPS listens on TCP 443.")]),
           lesson("Routing and the gateway", "beginner", 10, "networking-fundamentals",
                  "A host's routing table decides where packets go. The *default gateway* "
                  "handles anything not on the local subnet. `ip route` shows the table; "
                  "`ip addr` shows interfaces/addresses. In segmented networks, routing and "
                  "firewall rules together decide which zones can reach each other.",
                  exercises=[cmd("Command to show the routing table (iproute2)?", "ip route",
                                 "networking-fundamentals", "`ip route` prints routes.")]),
       ],
       [short("Default SSH port?", "22", "networking-fundamentals", "SSH uses TCP 22."),
        mcq("Which is connectionless?", ["TCP", "UDP", "ICMP handshake", "TLS"], "UDP",
            "networking-fundamentals", "UDP is connectionless."),
        short("Usable hosts in a /28?", "14", "networking-fundamentals",
              "2^4 - 2 = 14.")],
       lab="network-basics-lab"),

    _c("tcpip-packet-analysis", "TCP/IP and Packet Analysis",
       "Read packet captures and understand the protocol stack.",
       "intermediate", "networking", "infrastructure", ["networking-fundamentals"],
       [
           lesson("The TCP handshake", "intermediate", 15, "tcpip-analysis",
                  "TCP establishes a connection with SYN → SYN/ACK → ACK. Teardown uses "
                  "FIN/ACK exchanges. In a capture, an unusual number of SYNs without "
                  "completed handshakes can indicate scanning or packet loss. Recognising "
                  "normal vs abnormal flow is the heart of traffic analysis.",
                  exercises=[mcq("Correct handshake order?",
                                 ["ACK, SYN, SYN/ACK", "SYN, SYN/ACK, ACK", "SYN, ACK, FIN",
                                  "SYN/ACK, SYN, ACK"], "SYN, SYN/ACK, ACK", "tcpip-analysis",
                                 "Three-way handshake is SYN, SYN/ACK, ACK.")],
                  hints=["Think client-initiates, server-responds, client-confirms."]),
           lesson("Reading a capture", "intermediate", 20, "tcpip-analysis",
                  "Tools like Wireshark/tshark decode frames layer by layer: Ethernet → IP "
                  "→ TCP/UDP → application. Filters (e.g. `tcp.port == 80`) isolate flows. "
                  "Follow a stream to reconstruct an application exchange. Captures are "
                  "primary evidence in both defensive investigation and troubleshooting.",
                  exercises=[short("Wireshark display filter for HTTP port only (tcp.port == __)",
                                   "80", "tcpip-analysis", "`tcp.port == 80` filters HTTP.")]),
       ],
       [mcq("A flood of SYNs with no completed handshakes suggests:",
            ["Normal browsing", "Possible scanning", "A DNS lookup", "A successful login"],
            "Possible scanning", "tcpip-analysis", "Half-open connections often indicate scanning."),
        short("Three-way handshake final packet flag?", "ACK", "tcpip-analysis",
              "The client's ACK completes the handshake.")]),

    _c("dns-network-services", "DNS and Network Services",
       "Name resolution and the core services that keep networks working.",
       "easy", "networking", "infrastructure", ["networking-fundamentals"],
       [
           lesson("How DNS resolves names", "easy", 15, "dns-services",
                  "DNS maps names to addresses through recursive and authoritative "
                  "servers. Record types matter: A (IPv4), AAAA (IPv6), CNAME (alias), MX "
                  "(mail), TXT (metadata), NS (delegation). `dig example.com A` queries a "
                  "record. Misconfigured DNS (open resolvers, stale records) causes both "
                  "outages and security issues.",
                  exercises=[mcq("Which record maps a name to an IPv4 address?",
                                 ["MX", "A", "TXT", "NS"], "A", "dns-services",
                                 "An A record holds an IPv4 address.")],
                  hints=["`dig` is the query tool of choice."]),
           lesson("DHCP and core services", "easy", 10, "dns-services",
                  "DHCP leases addresses to hosts automatically. In Pwnforge labs, an "
                  "isolated network can run its own DHCP so guests get predictable "
                  "addresses. Other core services — NTP (time), SMTP (mail) — each have "
                  "security-relevant configuration worth understanding.",
                  exercises=[short("Which service hands out IP addresses automatically?",
                                   "DHCP", "dns-services", "DHCP leases IP configuration.")]),
       ],
       [mcq("CNAME records provide:", ["Mail routing", "An alias to another name",
            "A text note", "Reverse lookup"], "An alias to another name", "dns-services",
            "CNAME aliases one name to another."),
        short("Tool to query DNS records from the CLI?", "dig", "dns-services",
              "`dig` queries DNS.")]),

    _c("bash-for-security", "Bash for Security",
       "Automate repetitive tasks and parse data safely with Bash.",
       "easy", "scripting", "linux", ["linux-fundamentals"],
       [
           lesson("Variables, loops and pipes", "easy", 15, "bash-scripting",
                  "Bash glues tools together. Pipes (`|`) pass output between commands; "
                  "loops iterate; variables store values. Example: `for p in 80 443; do "
                  "echo \"checking $p\"; done`. Combining `grep`, `awk`, `cut` and `sort` "
                  "lets you extract exactly the data you need from logs and command output.",
                  exercises=[cmd("Filter lines containing 'error' from a file with g___",
                                 "grep", "bash-scripting", "`grep error file` filters matching lines.")],
                  hints=["Pipes connect stdout of one command to stdin of the next."]),
           lesson("Writing safe scripts", "easy", 15, "bash-scripting",
                  "Robust scripts start with `set -euo pipefail` so errors stop execution "
                  "and undefined variables are caught. Always quote variables (`\"$var\"`) "
                  "to avoid word-splitting and injection. Never build commands from "
                  "untrusted input without validation — the same discipline that prevents "
                  "command injection in applications.",
                  exercises=[mcq("What does `set -e` do?",
                                 ["Echo commands", "Exit on error", "Enable globbing",
                                  "Disable history"], "Exit on error", "secure-coding",
                                 "`set -e` aborts on the first failing command.")]),
       ],
       [cmd("Command to count lines in output (pipe to)?", "wc -l", "bash-scripting",
            "`| wc -l` counts lines."),
        mcq("Why quote \"$var\"?", ["Faster", "Prevents word-splitting/injection",
            "Required syntax", "Changes colour"], "Prevents word-splitting/injection",
            "secure-coding", "Quoting avoids splitting and injection issues.")]),

    _c("python-for-security", "Python for Security",
       "Use Python to build small security tools and automate analysis.",
       "intermediate", "scripting", "reverse", ["bash-for-security"],
       [
           lesson("Python essentials for tooling", "intermediate", 20, "python-security",
                  "Python's standard library covers most security tasks: `socket` for "
                  "network I/O, `hashlib` for hashing, `re` for parsing, `argparse` for "
                  "CLIs, `requests` for HTTP. Write small, testable functions. Prefer "
                  "`subprocess.run([...])` with a list (never `shell=True` on untrusted "
                  "input) to avoid command injection.",
                  exercises=[mcq("Safest way to call an external command on untrusted input?",
                                 ["os.system(s)", "subprocess.run([...]) with a list and no shell",
                                  "eval(s)", "shell=True"],
                                 "subprocess.run([...]) with a list and no shell",
                                 "secure-coding", "A list argv avoids shell interpretation.")],
                  hints=["Avoid shell=True with external input."]),
           lesson("Parsing and reporting", "intermediate", 15, "python-security",
                  "Security data is often semi-structured. Use `csv`, `json` and `re` to "
                  "parse logs and emit clean reports. Hashing with `hashlib.sha256` lets "
                  "you verify file integrity. Keep secrets out of code and logs.",
                  exercises=[short("stdlib module for SHA-256 hashing?", "hashlib",
                                   "python-security", "`hashlib` provides SHA-256.")]),
       ],
       [mcq("Which avoids command injection?",
            ["shell=True", "argv list without a shell", "eval", "os.system"],
            "argv list without a shell", "secure-coding",
            "Passing an argv list avoids shell parsing."),
        short("Module for regular expressions?", "re", "python-security",
              "`re` handles regular expressions.")]),

    _c("windows-fundamentals", "Windows Fundamentals",
       "Windows OS concepts, the command line and PowerShell basics.",
       "beginner", "windows", "infrastructure", ["cybersecurity-fundamentals"],
       [
           lesson("Windows structure", "beginner", 15, "windows-fundamentals",
                  "Windows organises configuration in the Registry (HKLM, HKCU hives) and "
                  "stores users as SIDs. The command line (`cmd`) and PowerShell both "
                  "administer the system; PowerShell is object-oriented (`Get-Service`, "
                  "`Get-Process`). Understanding users, groups and the Registry is the "
                  "basis for Windows security work.",
                  exercises=[short("PowerShell cmdlet to list running services (Get-____)",
                                   "Service", "windows-fundamentals", "`Get-Service` lists services.")],
                  hints=["PowerShell cmdlets follow Verb-Noun naming."]),
           lesson("Users, groups and privileges", "beginner", 15, "windows-fundamentals",
                  "Local accounts and groups (Administrators, Users) govern access. "
                  "Privileges (like SeDebugPrivilege) grant specific capabilities. "
                  "Just as on Linux, least privilege is key: day-to-day accounts should "
                  "not be local administrators.",
                  exercises=[mcq("Which group grants full local control?",
                                 ["Users", "Guests", "Administrators", "Everyone"],
                                 "Administrators", "windows-fundamentals",
                                 "Administrators have full local control.")]),
       ],
       [short("Where does Windows store much of its configuration?", "Registry",
              "windows-fundamentals", "The Registry holds configuration."),
        mcq("PowerShell cmdlets are named:", ["Noun-Verb", "Verb-Noun", "all lowercase",
            "random"], "Verb-Noun", "windows-fundamentals", "Cmdlets use Verb-Noun.")]),

    _c("windows-administration", "Windows Administration",
       "Manage Windows services, policies and the event log.",
       "easy", "windows", "infrastructure", ["windows-fundamentals"],
       [
           lesson("Services and scheduled tasks", "easy", 15, "windows-administration",
                  "Services run background functionality; scheduled tasks run on triggers. "
                  "Both are common persistence and misconfiguration points. Review service "
                  "accounts and binary paths (unquoted service paths are a classic issue). "
                  "Use `services.msc`, `sc query`, and `Get-ScheduledTask`.",
                  exercises=[mcq("An unquoted service path is a risk because:",
                                 ["It is slower", "Windows may execute an unintended binary",
                                  "It uses more RAM", "It breaks logging"],
                                 "Windows may execute an unintended binary",
                                 "windows-privesc", "Spaces in unquoted paths can redirect execution.")],
                  hints=["Look for service binaries in paths with spaces and no quotes."]),
           lesson("Event logs and auditing", "easy", 15, "windows-administration",
                  "Windows Event Log records security-relevant events (logons 4624/4625, "
                  "privilege use, process creation 4688). Enabling and forwarding these "
                  "logs underpins detection. `Get-WinEvent` queries them. Auditing is only "
                  "useful if logs are collected centrally and reviewed.",
                  exercises=[short("Event ID for a successful logon?", "4624",
                                   "log-analysis", "4624 is a successful logon.")]),
       ],
       [short("Event ID for a failed logon?", "4625", "log-analysis",
              "4625 indicates a failed logon."),
        mcq("Scheduled tasks are often abused for:", ["Faster boot", "Persistence",
            "Disk cleanup", "Theming"], "Persistence", "detection-engineering",
            "Attackers use scheduled tasks to persist.")]),

    _c("active-directory-fundamentals", "Active Directory Fundamentals",
       "Domains, organisational units, trusts and authentication in AD.",
       "intermediate", "identity", "active-directory", ["windows-administration"],
       [
           lesson("Directory structure", "intermediate", 20, "ad-fundamentals",
                  "Active Directory is a hierarchical directory of objects (users, "
                  "computers, groups) organised into domains and Organisational Units "
                  "(OUs). Domain Controllers (DCs) hold the directory and authenticate "
                  "users. Group Policy applies settings across OUs. Understanding this "
                  "structure is prerequisite to any identity-security work.",
                  exercises=[mcq("Which server authenticates domain users?",
                                 ["File server", "Domain Controller", "Print server",
                                  "DHCP server"], "Domain Controller", "ad-fundamentals",
                                 "DCs hold the directory and authenticate users.")],
                  hints=["OUs are containers for delegation and policy."]),
           lesson("Authentication: Kerberos basics", "intermediate", 20, "kerberos",
                  "AD uses Kerberos: a client gets a Ticket Granting Ticket (TGT) from the "
                  "DC, then requests service tickets. Tickets, service principal names "
                  "(SPNs) and delegation settings are central to both AD operation and its "
                  "security. Misconfigured delegation and weak service-account passwords "
                  "are common enterprise weaknesses to recognise and remediate.",
                  exercises=[short("What ticket does a client first obtain from the DC? (___)",
                                   "TGT", "kerberos", "The Ticket Granting Ticket comes first.")]),
       ],
       [mcq("OUs are used to:", ["Store files", "Organise objects and apply policy",
            "Route email", "Assign IPs"], "Organise objects and apply policy",
            "ad-fundamentals", "OUs organise objects and scope Group Policy."),
        short("Protocol AD uses for authentication?", "Kerberos", "kerberos",
              "AD primarily uses Kerberos.")],
       lab="enterprise-identity-lab"),
]
