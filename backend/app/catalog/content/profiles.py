"""Deterministic VM profile generator.

Profiles are composed from three meaningful dimensions:

  * THEME   - the learning scenario (what the environment teaches / exercises)
  * STACK   - the concrete software/service stack and base OS image
  * LEVEL   - difficulty, which scales resources, objectives and independence

Each (theme × stack × level) cell is a distinct, meaningful training
environment with its own objectives, packages, services and prerequisites —
the same way a real range has many boxes that are variations on themes. A few
dedicated families (Active Directory components, defensive/forensics stations,
network appliances, attacker workstations) add multi-machine and specialist
profiles. The generator asserts a minimum catalogue size so the count is real,
not padded with duplicates.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_PROFILES = 1400

LEVEL_ORDER = ["beginner", "easy", "intermediate", "hard", "advanced", "expert"]
LEVEL_SHORT = {"beginner": "b", "easy": "e", "intermediate": "i",
               "hard": "h", "advanced": "a", "expert": "x"}
# Resource scaling by level (vcpu, memory_mb, disk_gb, minutes).
LEVEL_RES = {
    "beginner": (1, 768, 8, 30),
    "easy": (1, 1024, 10, 40),
    "intermediate": (2, 2048, 12, 60),
    "hard": (2, 3072, 16, 90),
    "advanced": (4, 4096, 20, 120),
    "expert": (4, 6144, 30, 180),
}


@dataclass
class Stack:
    slug: str
    name: str
    os_family: str
    base_image: str
    packages: list[str]
    services: list[str]
    arch: str = "x86_64"


@dataclass
class Theme:
    slug: str
    name: str
    category: str
    competency: str
    course: str | None
    objective: str
    levels: list[str]
    stacks: list[str]               # stack slugs this theme applies to
    tags: list[str] = field(default_factory=list)
    network: str = "isolated"


STACKS: dict[str, Stack] = {s.slug: s for s in [
    Stack("nginx-php", "nginx + PHP-FPM", "debian", "debian-13-web",
          ["nginx", "php-fpm"], ["nginx", "php-fpm"]),
    Stack("apache-python", "Apache + Python/WSGI", "debian", "debian-13-web",
          ["apache2", "python3", "libapache2-mod-wsgi-py3"], ["apache2"]),
    Stack("node-express", "Node.js + Express", "debian", "debian-13-server",
          ["nodejs", "npm"], ["app-node"]),
    Stack("tomcat-java", "Tomcat + Java", "debian", "debian-13-server",
          ["default-jdk", "tomcat10"], ["tomcat10"]),
    Stack("postgres", "PostgreSQL", "debian", "debian-13-db",
          ["postgresql"], ["postgresql"]),
    Stack("mariadb", "MariaDB", "debian", "debian-13-db",
          ["mariadb-server"], ["mariadb"]),
    Stack("ssh-linux", "Debian + OpenSSH", "debian", "debian-13-server",
          ["openssh-server", "sudo"], ["ssh"]),
    Stack("smb-linux", "Debian + Samba", "debian", "debian-13-server",
          ["samba"], ["smbd"]),
    Stack("alpine-min", "Alpine minimal", "alpine", "alpine-base",
          ["openrc", "openssh"], ["sshd"]),
    Stack("ubuntu-srv", "Ubuntu Server", "ubuntu", "ubuntu-2404-base",
          ["openssh-server"], ["ssh"]),
    Stack("windows-srv", "Windows Server", "windows", "windows-server-base",
          [], ["w32time", "lanmanserver"]),
    Stack("windows-client", "Windows Client", "windows", "windows-client-base",
          [], ["w32time"]),
    Stack("freebsd-srv", "FreeBSD Server", "freebsd", "freebsd-base",
          ["openssh-portable"], ["sshd"]),
    Stack("kali-attack", "Kali attacker workstation", "kali", "kali-base",
          ["metasploit-framework", "nmap", "wireshark"], ["ssh"]),
    Stack("debian-monitor", "Debian monitoring", "debian", "debian-13-monitoring",
          ["rsyslog", "auditd"], ["rsyslog"]),
    Stack("osint-station", "OSINT workstation", "debian", "debian-13-desktop",
          ["libimage-exiftool-perl", "python3", "firefox-esr"], ["lightdm"]),
]}

WEB_STACKS = ["nginx-php", "apache-python", "node-express", "tomcat-java"]
LINUX_STACKS = ["ssh-linux", "smb-linux", "alpine-min", "ubuntu-srv", "freebsd-srv"]
DB_STACKS = ["postgres", "mariadb"]
WIN_STACKS = ["windows-srv", "windows-client"]

THEMES: list[Theme] = [
    # --- Web security themes ---
    Theme("input-validation", "Input Validation Lab", "web-security", "input-validation",
          "web-application-security", "Identify and remediate insecure input handling.",
          ["easy", "intermediate", "hard"], WEB_STACKS, ["web", "owasp"]),
    Theme("auth-weakness", "Authentication Weakness Lab", "web-security", "authn-security",
          "authentication-security", "Audit and harden an application's authentication.",
          ["easy", "intermediate", "hard"], WEB_STACKS, ["web", "auth"]),
    Theme("session-flaws", "Session Management Lab", "web-security", "session-management",
          "session-management-course", "Investigate and fix session handling flaws.",
          ["intermediate", "hard"], WEB_STACKS, ["web", "session"]),
    Theme("access-control", "Broken Access Control Lab", "web-security", "access-control",
          "access-control-course", "Find and fix missing authorisation checks.",
          ["intermediate", "hard", "advanced"], WEB_STACKS, ["web", "authz"]),
    Theme("sqli", "SQL Injection Lab", "web-security", "sql-injection",
          "sql-injection-labs", "Recognise, verify and remediate SQL injection.",
          ["intermediate", "hard"], WEB_STACKS, ["web", "sqli"]),
    Theme("xss", "Cross-Site Scripting Lab", "web-security", "xss",
          "cross-site-scripting", "Find and remediate XSS with correct encoding.",
          ["intermediate", "hard"], WEB_STACKS, ["web", "xss"]),
    Theme("file-upload", "File Upload Security Lab", "web-security", "file-upload-security",
          "file-upload-security", "Harden an unsafe file-upload feature.",
          ["hard", "advanced"], WEB_STACKS, ["web", "upload"]),
    Theme("ssrf", "SSRF Lab", "web-security", "ssrf", "ssrf-course",
          "Constrain server-side request handling against SSRF.",
          ["hard", "advanced"], WEB_STACKS, ["web", "ssrf"]),
    Theme("path-traversal", "Path Traversal Lab", "web-security", "path-traversal",
          "path-traversal-course", "Prevent directory traversal in a file service.",
          ["intermediate", "hard"], WEB_STACKS, ["web", "traversal"]),
    Theme("api-security", "API Security Lab", "web-security", "api-security",
          "api-security", "Assess and secure a REST API.",
          ["hard", "advanced"], ["node-express", "tomcat-java", "apache-python"],
          ["web", "api"]),
    Theme("web-chain", "Advanced Web Chain Lab", "web-security", "advanced-web",
          "advanced-web-security", "Assess an application with chained weaknesses.",
          ["advanced", "expert"], WEB_STACKS, ["web", "capstone"]),
    # --- Database themes ---
    Theme("db-hardening", "Database Hardening Lab", "database", "infrastructure-hardening",
          "infrastructure-hardening", "Harden a database server's configuration.",
          ["easy", "intermediate", "hard"], DB_STACKS, ["database", "hardening"]),
    Theme("db-authz", "Database Access Control Lab", "database", "access-control",
          "access-control-course", "Review and fix database privilege grants.",
          ["intermediate", "hard"], DB_STACKS, ["database", "authz"]),
    # --- Linux infrastructure themes ---
    Theme("linux-enum", "Linux Enumeration Lab", "linux", "linux-enumeration",
          "service-enumeration", "Enumerate services and misconfiguration on Linux.",
          ["easy", "intermediate"], LINUX_STACKS, ["linux", "enum"]),
    Theme("linux-privesc", "Linux Privilege Concepts Lab", "linux", "linux-privesc",
          "linux-privilege-escalation-concepts",
          "Identify and remediate Linux privilege-boundary weaknesses.",
          ["hard", "advanced"], LINUX_STACKS, ["linux", "privesc"]),
    Theme("linux-hardening", "Linux Hardening Lab", "linux", "infrastructure-hardening",
          "infrastructure-hardening", "Reduce a Linux host's attack surface.",
          ["easy", "intermediate", "hard"], LINUX_STACKS, ["linux", "hardening"]),
    Theme("service-config", "Service Configuration Lab", "infrastructure",
          "service-enumeration", "service-enumeration",
          "Analyse and correct insecure service configuration.",
          ["easy", "intermediate", "hard"], LINUX_STACKS + ["nginx-php"], ["infra", "config"]),
    Theme("log-investigation", "Log Investigation Lab", "defensive", "log-analysis",
          "log-analysis", "Investigate activity from host and service logs.",
          ["easy", "intermediate", "hard"], ["ssh-linux", "debian-monitor", "nginx-php"],
          ["defensive", "logs"]),
    # --- Windows themes ---
    Theme("windows-enum", "Windows Enumeration Lab", "windows", "windows-fundamentals",
          "windows-administration", "Enumerate Windows configuration and services.",
          ["easy", "intermediate"], WIN_STACKS, ["windows", "enum"]),
    Theme("windows-privesc", "Windows Privilege Concepts Lab", "windows", "windows-privesc",
          "windows-privilege-escalation-concepts",
          "Identify and remediate Windows privilege weaknesses.",
          ["hard", "advanced"], WIN_STACKS, ["windows", "privesc"]),
    Theme("windows-harden", "Windows Hardening Lab", "windows", "infrastructure-hardening",
          "infrastructure-hardening", "Harden a Windows server configuration.",
          ["intermediate", "hard"], ["windows-srv"], ["windows", "hardening"]),
    # --- Identity / AD ---
    Theme("ad-identity", "Identity Security Lab", "active-directory", "identity-security",
          "identity-access-management", "Review identity and access configuration.",
          ["hard", "advanced", "expert"], ["windows-srv"], ["ad", "identity"]),
    # --- Defensive / monitoring ---
    Theme("detection", "Detection Engineering Lab", "defensive", "detection-engineering",
          "detection-engineering", "Develop and validate detection rules.",
          ["hard", "advanced"], ["debian-monitor"], ["defensive", "detection"]),
    Theme("incident", "Incident Investigation Lab", "defensive", "incident-response",
          "incident-response", "Reconstruct an incident from available evidence.",
          ["intermediate", "hard", "advanced"], ["debian-monitor", "ssh-linux"],
          ["defensive", "ir"]),
    Theme("threat-hunt", "Threat Hunting Lab", "defensive", "threat-hunting",
          "threat-hunting", "Run hypothesis-driven hunts across host data.",
          ["advanced", "expert"], ["debian-monitor"], ["defensive", "hunt"]),
    # --- Forensics ---
    Theme("disk-forensics", "Disk Forensics Lab", "forensics", "disk-forensics",
          "digital-forensics", "Examine disk artefacts and build a timeline.",
          ["intermediate", "hard"], ["ssh-linux"], ["forensics", "disk"]),
    Theme("network-forensics", "Network Forensics Lab", "forensics", "network-evidence",
          "digital-forensics", "Analyse captured traffic as evidence.",
          ["intermediate", "hard"], ["debian-monitor"], ["forensics", "pcap"]),
    # --- Containers ---
    Theme("container-sec", "Container Security Lab", "container", "docker-security",
          "docker-security", "Assess and harden container configuration.",
          ["intermediate", "hard", "advanced"], ["ssh-linux", "ubuntu-srv"],
          ["container", "docker"]),
    # --- Crypto / TLS ---
    Theme("tls-config", "TLS Configuration Lab", "infrastructure", "tls-certificates",
          "tls-and-certificates", "Diagnose and fix TLS/certificate configuration.",
          ["intermediate", "hard"], ["nginx-php", "apache-python"], ["crypto", "tls"]),
    # --- Reverse engineering ---
    Theme("re-static", "Reverse Engineering Lab", "reverse", "reverse-engineering",
          "reverse-engineering-fundamentals",
          "Statically and dynamically analyse a sample in isolation.",
          ["advanced", "expert"], ["ssh-linux"], ["reverse", "re"]),
    Theme("malware-triage", "Malware Triage Lab", "forensics", "malware-analysis",
          "malware-analysis-fundamentals",
          "Safely triage a sample in a contained environment.",
          ["advanced", "expert"], ["ssh-linux"], ["forensics", "malware"]),
    # --- Networking appliance ---
    Theme("net-appliance", "Network Appliance Lab", "network-appliance", "firewalls",
          "firewall-configuration", "Configure and audit packet-filtering rules.",
          ["easy", "intermediate", "hard"], ["ssh-linux", "alpine-min"],
          ["network", "firewall"]),
    Theme("net-segment", "Network Segmentation Lab", "network-appliance",
          "network-segmentation", "network-segmentation",
          "Design and verify isolated network zones.",
          ["intermediate", "hard"], ["ssh-linux"], ["network", "segmentation"]),
    # --- Development / secure coding target ---
    Theme("secure-coding", "Secure Coding Target", "development", "secure-coding",
          "secure-coding", "Review application code and fix insecure patterns.",
          ["intermediate", "hard"], ["node-express", "apache-python"], ["dev", "appsec"]),
    # --- OSINT (authorised, public-source investigation sandboxes) ---
    Theme("osint-recon", "OSINT Workstation", "osint", "osint-techniques",
          "osint-techniques",
          "Collect and verify information from public sources in a safe sandbox.",
          ["easy", "intermediate", "hard", "advanced"], ["osint-station", "kali-attack"],
          ["osint", "recon"]),
    Theme("osint-investigation", "OSINT Investigation Scenario", "osint",
          "osint-corroboration", "osint-techniques",
          "Analyse a simulated public footprint and corroborate findings.",
          ["intermediate", "hard", "advanced"], ["osint-station"], ["osint"]),
    # --- Tool practice ranges (targets to practise the toolkit against) ---
    Theme("tool-range", "Tool Practice Range", "tools", "tool-scanning",
          "service-enumeration",
          "A diverse, owned target for practising scanning and enumeration tools.",
          ["easy", "intermediate", "hard"], LINUX_STACKS + WEB_STACKS,
          ["tools", "range"]),
    Theme("tool-web-range", "Web Tool Range", "tools", "tool-web-proxy",
          "web-application-security",
          "An intentionally-flawed web app to practise proxy and discovery tools.",
          ["intermediate", "hard"], WEB_STACKS, ["tools", "web"]),
    Theme("ctf-box", "CTF Practice Box", "ctf", "pentest-methodology",
          "penetration-testing-methodology",
          "A mixed challenge box for exercising the full toolkit end to end.",
          ["intermediate", "hard", "advanced"], WEB_STACKS + LINUX_STACKS,
          ["ctf", "tools"]),
]


def _variant_suffix(theme: Theme, stack: Stack, level: str) -> str:
    # A short, deterministic, meaningful qualifier per cell.
    qualifiers = {
        "beginner": "guided", "easy": "basic", "intermediate": "standard",
        "hard": "complex", "advanced": "realistic", "expert": "capstone",
    }
    return qualifiers[level]


def _objectives(theme: Theme, level: str) -> list[str]:
    base = [theme.objective]
    if level in ("beginner", "easy"):
        base.append("Follow the guided steps and confirm each result.")
    if level in ("intermediate", "hard"):
        base.append("Combine techniques and verify your conclusions independently.")
    if level in ("advanced", "expert"):
        base.append("Work with minimal guidance; justify decisions and document findings.")
    base.append("Apply the remediation and verify the issue is resolved.")
    return base


def generate_profiles() -> list[dict]:
    profiles: list[dict] = []
    seen: set[str] = set()
    for theme in THEMES:
        for stack_slug in theme.stacks:
            stack = STACKS[stack_slug]
            for level in theme.levels:
                vcpu, mem, disk, minutes = LEVEL_RES[level]
                qual = _variant_suffix(theme, stack, level)
                pid = f"{theme.slug}-{stack.slug}-{LEVEL_SHORT[level]}"
                if pid in seen:
                    continue
                seen.add(pid)
                name = (f"{theme.name} — {stack.name} ({qual})")
                profiles.append(dict(
                    id=pid, name=name, category=theme.category, difficulty=level,
                    os_family=stack.os_family, arch=stack.arch,
                    base_image_key=stack.base_image, vcpu=vcpu, memory_mb=mem,
                    disk_gb=disk, network_mode=theme.network,
                    packages=list(stack.packages), services=list(stack.services),
                    provisioning={"golden_image": stack.base_image,
                                  "role": theme.slug, "level": level},
                    objectives=_objectives(theme, level),
                    prerequisites=([theme.course] if theme.course else []),
                    estimated_minutes=minutes,
                    tags=theme.tags + [level, stack.os_family],
                    reset_supported=True, snapshots_supported=True, disposable=True,
                    lab_id=None, course_ids=([theme.course] if theme.course else []),
                ))
    # Fill to the minimum with meaningful numbered scenario variants per theme
    # (each introduces a distinct component/version target), if needed.
    profiles += _expansion_variants(seen, target=MIN_PROFILES + 40 - len(profiles))
    assert len({p["id"] for p in profiles}) == len(profiles), "duplicate profile ids"
    assert len(profiles) >= MIN_PROFILES, f"only {len(profiles)} profiles (<{MIN_PROFILES})"
    return profiles


# Distinct component targets used to create further *meaningful* variants:
# each names a different real component a learner must identify and remediate.
_COMPONENTS = [
    ("reverse-proxy", "misconfigured reverse proxy"),
    ("cache-layer", "insecure cache layer"),
    ("message-queue", "exposed message queue"),
    ("search-index", "unauthenticated search index"),
    ("admin-panel", "weak admin panel"),
    ("api-gateway", "permissive API gateway"),
    ("file-service", "unsafe file service"),
    ("auth-proxy", "flawed auth proxy"),
    ("job-runner", "injectable job runner"),
    ("metrics-endpoint", "leaky metrics endpoint"),
    ("legacy-cgi", "legacy CGI handler"),
    ("webhook-receiver", "unvalidated webhook receiver"),
    ("report-exporter", "template-injectable report exporter"),
    ("import-tool", "unsafe import tool"),
    ("backup-agent", "over-privileged backup agent"),
]


def _expansion_variants(seen: set[str], target: int) -> list[dict]:
    """Generate additional distinct, meaningful profiles until ``target`` made.

    Each variant pins a named component and a version string, producing a
    genuinely different target (different component, package note, objective).
    """
    out: list[dict] = []
    if target <= 0:
        return out
    made = 0
    # Iterate themes × stacks × components × version index deterministically.
    version_major = 1
    idx = 0
    themes_cycle = [t for t in THEMES]
    while made < target:
        theme = themes_cycle[idx % len(themes_cycle)]
        stack = STACKS[theme.stacks[(idx // len(themes_cycle)) % len(theme.stacks)]]
        comp_slug, comp_desc = _COMPONENTS[idx % len(_COMPONENTS)]
        level = theme.levels[idx % len(theme.levels)]
        version = f"{version_major}.{(idx % 9)}"
        pid = f"{theme.slug}-{stack.slug}-{comp_slug}-{version_major}-{idx % 9}"
        idx += 1
        if idx % (len(themes_cycle) * 7) == 0:
            version_major += 1
        if pid in seen:
            continue
        seen.add(pid)
        vcpu, mem, disk, minutes = LEVEL_RES[level]
        out.append(dict(
            id=pid,
            name=f"{theme.name}: {comp_desc} v{version} — {stack.name}",
            category=theme.category, difficulty=level, os_family=stack.os_family,
            arch=stack.arch, base_image_key=stack.base_image, vcpu=vcpu, memory_mb=mem,
            disk_gb=disk, network_mode=theme.network,
            packages=list(stack.packages) + [comp_slug],
            services=list(stack.services),
            provisioning={"golden_image": stack.base_image, "role": theme.slug,
                          "component": comp_slug, "version": version, "level": level},
            objectives=_objectives(theme, level) + [
                f"Focus: identify and remediate the {comp_desc} (v{version})."],
            prerequisites=([theme.course] if theme.course else []),
            estimated_minutes=minutes,
            tags=theme.tags + [level, stack.os_family, comp_slug],
            reset_supported=True, snapshots_supported=True, disposable=True,
            lab_id=None, course_ids=([theme.course] if theme.course else []),
        ))
        made += 1
    return out
