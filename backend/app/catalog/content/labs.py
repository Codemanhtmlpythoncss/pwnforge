"""Multi-machine lab definitions. Machine profile_ids reference generated profiles."""
from __future__ import annotations


def _lab(id, title, description, difficulty, category, machines, networks,
         startup_order, course=None, minutes=90, objectives=None, tags=None,
         hints=None, guide="", tasks=None):
    return dict(id=id, title=title, description=description, difficulty=difficulty,
                category=category, machines=machines, networks=networks,
                startup_order=startup_order, readiness_checks=[], course_id=course,
                estimated_minutes=minutes, reset_behavior="disposable",
                objectives=objectives or [], tags=tags or [], tasks=tasks or [],
                hints=hints or _DEFAULT_HINTS, guide=guide)


# Generic three-tier hints used where a lab doesn't override them. Tier 1 nudges, tier 2 narrows, tier 3 is concrete —
# none reveal the flag.
_DEFAULT_HINTS = [
    {"title": "Where to start", "text": "You're given the target's IP and nothing else. Begin with host and service "
     "discovery — find which ports are open and what's listening before anything else."},
    {"title": "Enumerate the service", "text": "Identify the software and version behind each open port. Weak or default "
     "configurations, exposed files and known issues are usually found by careful enumeration, not guessing."},
    {"title": "Get in, then look around", "text": "Once you have access, treat the box like any system: check the home "
     "directory, running services and privileges. The flag is a file on the machine — read it and submit its contents."},
]


# Each machine role maps to a generated profile id that exists in the catalogue.
LABS = [
    _lab("web-security-lab", "Web Security Lab",
         "A vulnerable web application, a database and a monitoring host on an "
         "isolated network. Assess the app, verify findings and apply fixes.",
         "intermediate", "web-security",
         machines=[
             {"role": "attacker", "profile_id": "web-chain-nginx-php-a", "network": "lab"},
             {"role": "web", "profile_id": "input-validation-nginx-php-i", "network": "lab"},
             {"role": "db", "profile_id": "db-hardening-postgres-i", "network": "lab"},
             {"role": "monitor", "profile_id": "log-investigation-debian-monitor-i", "network": "lab"},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["db", "web", "monitor", "attacker"],
         course="web-application-security",
         objectives=["Enumerate the application", "Verify a vulnerability",
                     "Apply and verify a remediation"],
         tags=["web", "multi-machine"]),

    _lab("enterprise-identity-lab", "Enterprise Identity Lab",
         "A Windows domain controller, a member server and a workstation with a "
         "monitoring host. Review identity and access configuration.",
         "advanced", "active-directory",
         machines=[
             {"role": "dc", "profile_id": "ad-identity-windows-srv-a", "network": "corp"},
             {"role": "member", "profile_id": "windows-harden-windows-srv-h", "network": "corp"},
             {"role": "workstation", "profile_id": "windows-enum-windows-client-e", "network": "corp"},
             {"role": "monitor", "profile_id": "detection-debian-monitor-h", "network": "corp"},
         ],
         networks=[{"name": "corp", "mode": "isolated"}],
         startup_order=["dc", "member", "workstation", "monitor"],
         course="active-directory-fundamentals",
         objectives=["Map the directory", "Identify an identity misconfiguration",
                     "Recommend remediation"],
         tags=["ad", "identity", "multi-machine"]),

    _lab("defensive-monitoring-lab", "Defensive Monitoring Lab",
         "A log collector / SIEM host, an endpoint and an investigation workstation. "
         "Detect and reconstruct activity.",
         "hard", "defensive",
         machines=[
             {"role": "siem", "profile_id": "detection-debian-monitor-h", "network": "soc"},
             {"role": "endpoint", "profile_id": "log-investigation-ssh-linux-i", "network": "soc"},
             {"role": "analyst", "profile_id": "incident-debian-monitor-h", "network": "soc"},
         ],
         networks=[{"name": "soc", "mode": "isolated"}],
         startup_order=["siem", "endpoint", "analyst"],
         course="detection-engineering",
         objectives=["Build a detection", "Investigate an alert", "Reconstruct the timeline"],
         tags=["defensive", "multi-machine"]),

    _lab("forensics-workstation-lab", "Forensics Workstation Lab",
         "An investigation workstation with disk and network evidence to examine.",
         "hard", "forensics",
         machines=[
             {"role": "workstation", "profile_id": "disk-forensics-ssh-linux-h", "network": "lab"},
             {"role": "evidence", "profile_id": "network-forensics-debian-monitor-h", "network": "lab"},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["evidence", "workstation"],
         course="digital-forensics",
         objectives=["Acquire with integrity", "Build a timeline", "Report findings"],
         tags=["forensics", "multi-machine"]),

    _lab("reverse-engineering-lab", "Reverse Engineering Lab",
         "An isolated analysis workstation for static and dynamic analysis of a sample.",
         "advanced", "reverse",
         machines=[
             {"role": "analysis", "profile_id": "re-static-ssh-linux-a", "network": "air-gapped"},
         ],
         networks=[{"name": "air-gapped", "mode": "isolated"}],
         startup_order=["analysis"],
         course="reverse-engineering-fundamentals",
         objectives=["Static triage", "Dynamic analysis in isolation", "Document behaviour"],
         tags=["reverse", "single-host"]),

    _lab("container-security-lab", "Container Security Lab",
         "A container host to assess image hygiene, runtime flags and segmentation.",
         "advanced", "container",
         machines=[
             {"role": "host", "profile_id": "container-sec-ubuntu-srv-a", "network": "lab"},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["host"],
         course="docker-security",
         objectives=["Assess image hygiene", "Review runtime flags", "Apply least privilege"],
         tags=["container", "single-host"]),

    _lab("linux-practice-basic", "Linux Practice (Basic)",
         "A single Debian host for practising core Linux commands safely.",
         "beginner", "linux",
         machines=[{"role": "host", "profile_id": "linux-enum-ssh-linux-e", "network": "lab"}],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["host"], course="linux-fundamentals",
         objectives=["Navigate the filesystem", "Read permissions", "Inspect services"],
         tags=["linux", "beginner"]),

    _lab("linux-admin-lab", "Linux Administration Lab",
         "A Debian server to practise user, service and package administration.",
         "easy", "linux",
         machines=[{"role": "host", "profile_id": "linux-hardening-ssh-linux-e", "network": "lab"}],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["host"], course="linux-administration",
         objectives=["Manage users", "Harden services", "Apply updates"],
         tags=["linux", "admin"]),

    _lab("network-basics-lab", "Network Basics Lab",
         "A small isolated network for enumeration and service identification.",
         "easy", "networking",
         machines=[
             {"role": "target1", "profile_id": "service-config-ssh-linux-e", "network": "lab"},
             {"role": "target2", "profile_id": "net-appliance-alpine-min-e", "network": "lab"},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["target1", "target2"], course="service-enumeration",
         objectives=["Discover hosts", "Enumerate services", "Map the attack surface"],
         tags=["networking", "enum"]),

    _lab("malware-analysis-lab", "Malware Analysis Lab",
         "An isolated, monitored analysis host for safe sample triage.",
         "advanced", "forensics",
         machines=[{"role": "analysis", "profile_id": "malware-triage-ssh-linux-a",
                    "network": "air-gapped"}],
         networks=[{"name": "air-gapped", "mode": "isolated"}],
         startup_order=["analysis"], course="malware-analysis-fundamentals",
         objectives=["Contain the sample", "Record indicators", "Produce detections"],
         tags=["forensics", "malware"]),

    _lab("osint-investigation-lab", "OSINT Investigation Lab",
         "An OSINT workstation plus a sandboxed 'public footprint' host to "
         "collect from and corroborate against — safely and ethically.",
         "intermediate", "osint",
         machines=[
             {"role": "workstation", "profile_id": "osint-recon-osint-station-i", "network": "lab"},
             {"role": "footprint", "profile_id": "osint-investigation-osint-station-i", "network": "lab"},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["footprint", "workstation"], course="osint-techniques",
         objectives=["Plan the question", "Collect from public sources",
                     "Corroborate and report with confidence levels"],
         tags=["osint", "multi-machine"]),

    # ---- Black-box targets: you get an IP, not a login. Break in and capture the flag. -------------------------
    _lab("foothold-weak-ssh", "Foothold: Weak SSH Password",
         "A black-box target. You are given only its IP address — no credentials. The machine runs a remote-access "
         "service that was left with a weak password. Discover the service, gain access, and read the flag from the "
         "account's home directory.",
         "easy", "initial-access",
         machines=[
             {"role": "target", "profile_id": "linux-enum-ssh-linux-e", "network": "lab",
              # The deliberately-weak credential the learner must discover — it is NEVER shown in the UI.
              "target": {"user": "amy", "password": "sunshine"}},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["target"], minutes=45,
         objectives=["Discover the open service on the target",
                     "Gain access by finding the weak credential",
                     "Read and submit the flag"],
         tags=["initial-access", "ssh", "brute-force", "black-box"],
         hints=[
             {"title": "What's exposed?", "text": "You only have an IP. Start with a port scan (e.g. nmap). What service "
              "is listening, and what does it let you do remotely?"},
             {"title": "A way in", "text": "The service accepts password logins and the password left on it is weak. "
              "You'll need a username — common first names are a good guess — and a common-password wordlist."},
             {"title": "Guess the password", "text": "Use a login-guessing tool (such as hydra or ncrack) against the "
              "service with a common-password list and likely usernames. Once you're in, the flag is a file in the "
              "user's home directory (try `ls` and `cat flag.txt`)."},
         ],
         guide=(
             "Walkthrough — Foothold: Weak SSH Password\n\n"
             "1. Enumerate: `nmap -sV <target-ip>` shows TCP 22 (OpenSSH) open.\n"
             "2. The box has a user with a weak password. The account is `amy` (a common first name — you could also "
             "brute a small username list). The password, `sunshine`, is near the top of common wordlists such as "
             "rockyou.txt.\n"
             "3. Guess it: `hydra -l amy -P /usr/share/wordlists/rockyou.txt ssh://<target-ip>` (or simply try common "
             "passwords by hand). It recovers `amy:sunshine` quickly.\n"
             "4. Log in: `ssh amy@<target-ip>`, then `cat ~/flag.txt` and submit the value.\n\n"
             "Why it exists: password authentication plus a weak, guessable password is one of the most common ways "
             "real systems are compromised.\n"
             "How to prevent it: disable SSH password auth in favour of keys, enforce strong passwords, and add "
             "rate-limiting/lockout (e.g. fail2ban) so guessing is impractical.")),

    _lab("foothold-default-creds", "Foothold: Default Credentials",
         "A black-box target that was deployed and never had its default administrator credentials changed. Find the "
         "service, log in with the credentials it shipped with, and read the flag.",
         "beginner", "initial-access",
         machines=[
             {"role": "target", "profile_id": "service-config-ssh-linux-e", "network": "lab",
              "target": {"user": "admin", "password": "admin", "sudo": True}},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["target"], minutes=30,
         objectives=["Find the exposed service", "Log in with default credentials", "Read and submit the flag"],
         tags=["initial-access", "default-credentials", "black-box"],
         hints=[
             {"title": "Find the service", "text": "Scan the target. A remote-login service is exposed."},
             {"title": "Think defaults", "text": "Appliances and quick deployments often keep the credentials they "
              "ship with. The most common administrator username and password pair is worth trying first."},
             {"title": "Log in", "text": "Try admin / admin (and other common default pairs) over SSH. Once in, the "
              "flag is in the home directory — `cat flag.txt`."},
         ],
         guide=(
             "Walkthrough — Foothold: Default Credentials\n\n"
             "1. `nmap -sV <target-ip>` → TCP 22 open (OpenSSH).\n"
             "2. The box was left with its default admin login: `admin:admin`.\n"
             "3. `ssh admin@<target-ip>` with password `admin`, then `cat ~/flag.txt`.\n\n"
             "Why: unchanged default credentials are a leading cause of real breaches.\n"
             "Prevent: force a credential change on first boot, and never ship guessable defaults.")),

    _lab("foothold-enumerate-user", "Foothold: Name the User",
         "A black-box target with a weak password — but you'll have to work out the username first. Enumerate the box, "
         "identify a valid account, then recover its weak password and read the flag.",
         "intermediate", "initial-access",
         machines=[
             {"role": "target", "profile_id": "linux-enum-ssh-linux-e", "network": "lab",
              "target": {"user": "mwilson", "password": "liverpool"}},
         ],
         networks=[{"name": "lab", "mode": "isolated"}],
         startup_order=["target"], minutes=60,
         objectives=["Enumerate the target and identify a valid username",
                     "Recover the weak password", "Read and submit the flag"],
         tags=["initial-access", "enumeration", "brute-force", "black-box"],
         hints=[
             {"title": "Service first", "text": "As always, scan first. SSH is open — but you need a username before a "
              "password guess is any use."},
             {"title": "Usernames", "text": "Real accounts often follow a pattern (first initial + surname is common). "
              "A small username wordlist of likely names, tried against SSH, will reveal which ones exist."},
             {"title": "Then the password", "text": "With a valid username, run a password guess against SSH with a "
              "common wordlist (football clubs and the like are common weak passwords). Then `cat ~/flag.txt`."},
         ],
         guide=(
             "Walkthrough — Foothold: Name the User\n\n"
             "1. `nmap -sV <target-ip>` → SSH on 22.\n"
             "2. Usernames follow first-initial+surname: the valid account is `mwilson`. A username wordlist "
             "(e.g. hydra with `-L names.txt`) confirms which accounts exist.\n"
             "3. Guess the password with a wordlist: it's `liverpool` (a common weak password). "
             "`hydra -l mwilson -P rockyou.txt ssh://<target-ip>`.\n"
             "4. `ssh mwilson@<target-ip>`, `cat ~/flag.txt`.\n\n"
             "Prevent: don't use guessable usernames as a security layer; enforce strong passwords and key auth.")),
]


# Five additional guided labs are placed at the relevant points in each of the
# ten learning paths. Each uses an existing real-VM profile and has a short,
# server-graded worksheet before flag submission.
_PATH_LAB_SPECS = [
    # Complete Beginner
    ("lab-linux-smb-enumeration", "Linux and SMB Service Inventory", "linux-enum-smb-linux-e",
     "linux-fundamentals", "linux", "Inspect a small Linux host, identify its active services, and record the evidence you used."),
    ("lab-alpine-service-hardening", "Alpine Service Hardening", "linux-hardening-alpine-min-e",
     "linux-fundamentals", "linux", "Review a minimal Alpine host and distinguish required services from unnecessary exposure."),
    ("lab-first-firewall-map", "First Firewall and Port Map", "net-appliance-alpine-min-i",
     "networking-fundamentals", "networking", "Map the host's reachable services and explain how a firewall changes the visible attack surface."),
    ("lab-http-input-validation", "HTTP Input Validation Practice", "input-validation-apache-python-e",
     "web-technologies", "web-security", "Trace an HTTP request to the application and identify where untrusted input must be validated."),
    ("lab-nginx-service-inventory", "Nginx Service Inventory", "service-config-nginx-php-e",
     "service-enumeration", "infrastructure", "Inventory the web and application services on a host, then connect each service to its listening socket."),

    # Web Penetration Testing
    ("lab-web-input-validation-review", "Web Input Validation Review", "input-validation-apache-python-i",
     "web-application-security", "web-security", "Follow user-controlled input through a web request and identify the validation boundary."),
    ("lab-web-authentication-audit", "Web Authentication Audit", "auth-weakness-nginx-php-i",
     "authentication-security", "web-security", "Inspect an authentication service and assess password handling and login protections."),
    ("lab-session-token-audit", "Session Token Audit", "session-flaws-node-express-i",
     "session-management-course", "web-security", "Inspect how an application issues and handles session tokens, then record the controls that matter."),
    ("lab-sql-injection-practice", "SQL Injection Verification Practice", "sqli-nginx-php-i",
     "sql-injection-labs", "web-security", "Use controlled inputs to recognise a database-backed endpoint and describe how to verify it safely."),
    ("lab-xss-output-encoding", "Cross-Site Scripting and Output Encoding", "xss-apache-python-i",
     "cross-site-scripting", "web-security", "Trace a value into an HTML response and identify the context-appropriate output encoding control."),

    # Infrastructure Penetration Testing
    ("lab-linux-firewall-enumeration", "Linux Firewall Enumeration", "net-appliance-ssh-linux-i",
     "firewall-configuration", "networking", "Compare the host's listening services with its firewall policy and document allowed paths."),
    ("lab-samba-service-enumeration", "Samba Service Enumeration", "service-config-smb-linux-i",
     "service-enumeration", "infrastructure", "Enumerate a Samba-enabled host and report the service names and exposed network surface."),
    ("lab-alpine-host-enumeration", "Alpine Host Enumeration", "linux-enum-alpine-min-i",
     "service-enumeration", "linux", "Build a concise host inventory from processes, listening sockets, and service status."),
    ("lab-smb-privilege-boundaries", "SMB and Linux Privilege Boundaries", "linux-privesc-smb-linux-h",
     "linux-privilege-escalation-concepts", "linux", "Review file-sharing and local permission boundaries, then explain the least-privilege issue you identify."),
    ("lab-tls-nginx-audit", "TLS Configuration Audit", "tls-config-nginx-php-i",
     "tls-and-certificates", "infrastructure", "Inspect a web service's TLS endpoint and record the certificate and protocol evidence."),

    # Active Directory Security: Linux/Samba labs complement the Windows-domain capstone.
    ("lab-identity-linux-groups", "Identity and Linux Group Review", "linux-hardening-ssh-linux-i",
     "identity-access-management", "identity", "Inventory local users and groups, then identify where group membership grants access."),
    ("lab-samba-share-inventory", "Samba Share Inventory", "service-config-smb-linux-h",
     "active-directory-fundamentals", "identity", "Enumerate SMB services and share exposure as preparation for the path's directory-services capstone."),
    ("lab-samba-account-enumeration", "Samba Account and Service Enumeration", "linux-enum-smb-linux-i",
     "active-directory-fundamentals", "identity", "Identify the file-sharing service and document the account and access questions an AD assessment must answer."),
    ("lab-samba-service-hardening", "Samba Service Hardening", "service-config-smb-linux-h",
     "identity-access-management", "identity", "Review service exposure and access boundaries on a Samba host; recommend a scoped hardening change."),
    ("lab-identity-privilege-boundaries", "Identity Privilege Boundaries", "linux-privesc-ssh-linux-h",
     "windows-privilege-escalation-concepts", "identity", "Trace how local identity and group privileges affect access, then state the least-privilege correction."),

    # Defensive Security
    ("lab-linux-auth-log-review", "Linux Authentication Log Review", "log-investigation-ssh-linux-e",
     "log-analysis", "defensive", "Inspect authentication evidence, separate routine activity from suspicious events, and record a time window."),
    ("lab-detection-rule-practice", "Detection Rule Practice", "detection-debian-monitor-a",
     "detection-engineering", "defensive", "Translate an observed behaviour into a detection idea with evidence, useful context, and a clear limitation."),
    ("lab-incident-timeline-practice", "Incident Timeline Practice", "incident-ssh-linux-i",
     "incident-response", "defensive", "Build a short incident timeline from host evidence and distinguish confirmed facts from hypotheses."),
    ("lab-threat-hunt-practice", "Threat Hunting Practice", "threat-hunt-debian-monitor-a",
     "threat-hunting", "defensive", "Turn a testable hypothesis into a focused hunt and record what would confirm or refute it."),
    ("lab-network-evidence-review", "Network Evidence Review", "network-forensics-debian-monitor-i",
     "network-monitoring", "defensive", "Inspect network-service evidence and explain how time, direction, and endpoints shape an alert."),

    # Reverse Engineering
    ("lab-static-analysis-capstone", "Static Analysis Capstone", "re-static-ssh-linux-x",
     "reverse-engineering-fundamentals", "reverse", "Practise a safe static-analysis sequence and record hashes, file type, strings, and initial hypotheses."),
    ("lab-malware-triage-capstone", "Malware Triage Capstone", "malware-triage-ssh-linux-x",
     "malware-analysis-fundamentals", "reverse", "Triage a contained analysis environment and separate observed indicators from unverified conclusions."),
    ("lab-re-backup-agent", "Reverse Engineering: Backup Agent", "re-static-ssh-linux-backup-agent-1-2",
     "reverse-engineering-fundamentals", "reverse", "Inspect the analysis target's services and binary artefacts before describing its likely role."),
    ("lab-re-job-runner", "Reverse Engineering: Job Runner", "re-static-ssh-linux-job-runner-1-5",
     "reverse-engineering-fundamentals", "reverse", "Use file metadata and strings to build a cautious first-pass description of a job-runner component."),
    ("lab-re-message-queue", "Reverse Engineering: Message Queue", "re-static-ssh-linux-message-queue-1-8",
     "reverse-engineering-fundamentals", "reverse", "Inspect a message-queue component in isolation and record evidence before drawing conclusions."),

    # Container and Infrastructure Security
    ("lab-container-host-audit", "Container Host Audit", "container-sec-ssh-linux-i",
     "docker-security", "container", "Inspect container tooling and host services, then identify configuration evidence relevant to least privilege."),
    ("lab-container-runtime-hardening", "Container Runtime Hardening", "container-sec-ubuntu-srv-h",
     "docker-security", "container", "Review a container host's runtime and network surface, then propose and verify a safer configuration."),
    ("lab-segmentation-verification", "Network Segmentation Verification", "net-segment-ssh-linux-i",
     "network-segmentation", "networking", "Map the host's network interfaces and verify which service paths should be reachable."),
    ("lab-container-image-policy", "Container Image and Workload Policy", "container-sec-ubuntu-srv-i",
     "kubernetes-security", "container", "Review image provenance, workload identity, and runtime permissions in a container host."),
    ("lab-container-iac-review", "Container Infrastructure-as-Code Review", "container-sec-ssh-linux-a",
     "iac-security", "cloud", "Review declarative container configuration and explain how you would verify live-state drift."),

    # Digital Forensics
    ("lab-disk-forensics-import-tool", "Disk Forensics: Import Tool", "disk-forensics-ssh-linux-import-tool-1-4",
     "digital-forensics", "forensics", "Practise evidence inventory, integrity checks, and timeline notes in a controlled analysis host."),
    ("lab-network-forensics-webhook", "Network Forensics: Webhook Traffic", "network-forensics-debian-monitor-webhook-receiver-1-8",
     "digital-forensics", "forensics", "Review network-monitoring evidence and document endpoints, timestamps, and confidence."),
    ("lab-incident-evidence-timeline", "Incident Evidence Timeline", "incident-debian-monitor-i",
     "incident-response", "forensics", "Correlate host and service evidence into a timeline while preserving source and time-zone context."),
    ("lab-malware-triage-search-index", "Malware Triage: Search Index", "malware-triage-ssh-linux-search-index-1-0",
     "malware-analysis-fundamentals", "forensics", "Perform safe first-pass triage and record hashes, file type, indicators, and containment decisions."),
    ("lab-disk-forensics-backup-agent", "Disk Forensics: Backup Agent", "disk-forensics-ssh-linux-i",
     "digital-forensics", "forensics", "Inspect a host's file-system evidence and explain how a hash supports evidence integrity."),

    # The Hacker's Toolkit
    ("lab-tool-range-ssh", "Tool Range: SSH Enumeration", "tool-range-ssh-linux-e",
     "tool-nmap", "tools", "Use a restrained service scan to identify the SSH endpoint and record exact evidence and tool options."),
    ("lab-tool-range-smb", "Tool Range: SMB Enumeration", "tool-range-smb-linux-i",
     "tool-smb-enum", "tools", "Use SMB enumeration techniques against an isolated Samba host and record exposed services."),
    ("lab-tool-web-proxy", "Tool Range: Web Proxy Practice", "tool-web-range-node-express-i",
     "tool-burp", "tools", "Use an intercepting proxy to inspect a request and response, then identify one security-relevant observation."),
    ("lab-toolkit-ctf-web", "Toolkit Challenge: Web Host", "ctf-box-apache-python-i",
     "tool-http-clients", "tools", "Combine discovery and HTTP-client techniques against a disposable target and verify each observation."),
    ("lab-toolkit-service-discovery", "Toolkit Challenge: Service Discovery", "linux-enum-alpine-min-e",
     "tool-nmap", "tools", "Compare local socket inspection with remote service detection and explain any difference."),

    # OSINT and Reconnaissance
    ("lab-osint-source-confidence", "OSINT Source Confidence", "osint-recon-osint-station-e",
     "osint-fundamentals", "osint", "Build a small source log that records provenance, collection time, corroboration, and confidence."),
    ("lab-osint-corroboration", "OSINT Corroboration Practice", "osint-investigation-osint-station-h",
     "osint-techniques", "osint", "Compare independent public-source observations and explain whether they support the same claim."),
    ("lab-osint-recon-tooling", "OSINT Recon Tooling", "osint-recon-kali-attack-i",
     "osint-tools", "osint", "Choose a public-source collection method, record its limits, and avoid treating one result as proof."),
    ("lab-osint-api-gateway-footprint", "OSINT: API Gateway Footprint", "osint-investigation-osint-station-api-gateway-1-8",
     "osint-techniques", "osint", "Analyse a bounded simulated footprint and distinguish attributable evidence from inference."),
    ("lab-osint-opsec-review", "OSINT OPSEC Review", "osint-recon-kali-attack-h",
     "osint-opsec-reporting", "osint", "Plan a minimal, ethical collection workflow and document scope, exposure, and reporting safeguards."),
]

_PATH_LAB_CHECKS = {
    "linux": {
        "prompt": "Which command lists listening sockets together with process names on Linux?",
        "answers": ["ss -lntup", "ss -tulpen", "ss -tunlp"],
        "hint": "Use the modern socket-statistics utility and request listening TCP/UDP sockets plus process details.",
        "explanation": "`ss` reports socket state; `-lntup` selects listening sockets and includes numeric ports and process information.",
    },
    "networking": {
        "prompt": "Which Nmap option requests service and version detection?",
        "answers": ["-sV", "nmap -sV"],
        "hint": "It is the short option with a capital V.",
        "explanation": "Nmap's `-sV` probes discovered ports to identify service names and versions.",
    },
    "web-security": {
        "prompt": "Which response header lets a site restrict script sources as a defence against injection?",
        "answers": ["content-security-policy", "csp", "content security policy"],
        "hint": "It is commonly abbreviated CSP.",
        "explanation": "Content-Security-Policy defines allowed resource sources and can reduce the impact of script injection.",
    },
    "infrastructure": {
        "prompt": "Which Linux command shows the local routing table?",
        "answers": ["ip route", "ip route show"],
        "hint": "It begins with the `ip` networking utility.",
        "explanation": "`ip route` displays routes and the default gateway used by the host.",
    },
    "identity": {
        "prompt": "What security principle says an account should receive only the access it needs?",
        "answers": ["least privilege", "principle of least privilege"],
        "hint": "It limits standing permissions to the minimum required.",
        "explanation": "Least privilege reduces the impact of compromised or misused accounts.",
    },
    "defensive": {
        "prompt": "What time-ordered record helps reconstruct a sequence of security events?",
        "answers": ["timeline", "incident timeline", "event timeline"],
        "hint": "It arranges events chronologically.",
        "explanation": "A timeline aligns events from multiple sources so analysts can reconstruct what happened.",
    },
    "reverse": {
        "prompt": "What is the name for analysing a binary without running it?",
        "answers": ["static analysis", "static"],
        "hint": "It contrasts with dynamic analysis.",
        "explanation": "Static analysis examines file structure, metadata, strings, and code without executing the sample.",
    },
    "container": {
        "prompt": "Which principle should guide container capabilities and privileges?",
        "answers": ["least privilege", "principle of least privilege"],
        "hint": "Grant only the capabilities required by the workload.",
        "explanation": "Least privilege reduces the damage a compromised container can cause to its host.",
    },
    "cloud": {
        "prompt": "Which Terraform command previews infrastructure changes without applying them?",
        "answers": ["terraform plan", "terraform plan -out"],
        "hint": "It is the review step before the command that applies a configuration.",
        "explanation": "`terraform plan` shows the proposed resource changes so they can be reviewed before apply.",
    },
    "database": {
        "prompt": "Which security principle should limit an application's database account?",
        "answers": ["least privilege", "principle of least privilege"],
        "hint": "The application should not use a database administrator account for routine work.",
        "explanation": "Least privilege restricts application accounts to the specific operations they need.",
    },
    "forensics": {
        "prompt": "Which digest is commonly used to verify that an evidence image has not changed?",
        "answers": ["sha-256", "sha256", "sha 256"],
        "hint": "It is a member of the SHA-2 family and produces a 256-bit digest.",
        "explanation": "A SHA-256 digest can be compared before and after acquisition or analysis to detect changes.",
    },
    "tools": {
        "prompt": "Which Nmap option requests service and version detection?",
        "answers": ["-sV", "nmap -sV"],
        "hint": "It is the short option with a capital V.",
        "explanation": "Nmap's `-sV` probes discovered ports to identify service names and versions.",
    },
    "osint": {
        "prompt": "Name the three useful fields that make an OSINT observation auditable.",
        "kind": "list",
        "answers": ["source,timestamp,confidence", "source,time,confidence", "source,date,confidence"],
        "hint": "Record where the claim came from, when you collected it, and how certain you are.",
        "explanation": "Source, collection time, and confidence let another analyst assess and reproduce the observation.",
    },
}


def _path_practice_lab(spec: tuple, profiles_by_id: dict[str, dict]) -> dict:
    lab_id, title, profile_id, course_id, check_group, description = spec
    profile = profiles_by_id[profile_id]
    services = profile["services"]
    check = _PATH_LAB_CHECKS[check_group]
    tasks = [
        {
            "id": "service-inventory",
            "kind": "service_list",
            "prompt": "Identify the service name(s) configured for this target's application/profile and enter them, separated by commas. Use `systemctl` (or `rc-service -l` on Alpine), then cross-check any network listeners with `ss -lntup`. Extra base OS services are okay.",
            "answer": services,
            "hint": "Start with the service manager, then compare service names with the process and port information from `ss -lntup`.",
            "explanation": "A service inventory should name each configured service and be supported by evidence from service status or listening sockets.",
        },
        {
            "id": "course-check",
            "kind": check.get("kind", "short_answer"),
            "prompt": check["prompt"],
            "answers": check["answers"],
            "hint": check["hint"],
            "explanation": check["explanation"],
        },
    ]
    return _lab(
        lab_id, title,
        f"{description} This is a disposable, isolated VM. Complete the service inventory and course check, then capture the instance flag.",
        profile["difficulty"], profile["category"],
        machines=[{"role": "target", "profile_id": profile_id, "network": "lab"}],
        networks=[{"name": "lab", "mode": "isolated"}], startup_order=["target"],
        course=course_id, minutes=profile["estimated_minutes"],
        objectives=[description, "Identify configured services and verify listening sockets with command output.",
                    "Complete the graded worksheet and capture the lab flag."],
        tags=list(dict.fromkeys(profile["tags"] + ["learning-path", "guided", check_group])),
        hints=[
            {"title": "Start with the host", "text": "Use the lab's own terminal and inspect the target assigned to this disposable workspace."},
            {"title": "Inventory services", "text": "On Debian/Ubuntu try `systemctl list-units --type=service --state=running`; on Alpine try `rc-service -l`. Compare with `ss -lntup`."},
            {"title": "Verify before you submit", "text": "Separate service names from port numbers, and use the command output as evidence rather than guessing from the lab title."},
        ],
        tasks=tasks,
    )


from backend.app.catalog.content.profiles import generate_profiles as _generate_profiles

_profiles_by_id = {profile["id"]: profile for profile in _generate_profiles()}
LABS.extend(_path_practice_lab(spec, _profiles_by_id) for spec in _PATH_LAB_SPECS)
assert len(_PATH_LAB_SPECS) == 50
assert len({lab["id"] for lab in LABS}) == len(LABS), "duplicate lab ids"
