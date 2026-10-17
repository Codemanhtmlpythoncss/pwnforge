"""Competency catalogue grouped by domain."""
from __future__ import annotations

# (domain, key, name, description)
COMPETENCIES: list[tuple[str, str, str, str]] = [
    # Linux
    ("linux", "linux-fundamentals", "Linux Fundamentals", "Shell, files, permissions, processes."),
    ("linux", "linux-administration", "Linux Administration", "Services, users, packages, systemd."),
    ("linux", "linux-enumeration", "Linux Enumeration", "Discovering users, services and misconfig."),
    ("linux", "linux-privesc", "Linux Privilege Concepts", "Understanding Linux privilege boundaries."),
    ("linux", "bash-scripting", "Bash Scripting", "Automating tasks safely with Bash."),
    # Networking
    ("networking", "networking-fundamentals", "Networking Fundamentals", "IP, ports, protocols, routing."),
    ("networking", "tcpip-analysis", "TCP/IP & Packet Analysis", "Reading and interpreting packet captures."),
    ("networking", "dns-services", "DNS & Network Services", "Name resolution and core services."),
    ("networking", "network-segmentation", "Network Segmentation", "Designing isolated network zones."),
    ("networking", "firewalls", "Firewall Configuration", "Packet filtering and rule design."),
    # Web
    ("web", "http-fundamentals", "HTTP Fundamentals", "Requests, responses, headers, methods."),
    ("web", "web-technologies", "Web Technologies", "HTML, JS, cookies, same-origin model."),
    ("web", "input-validation", "Input Validation", "Trust boundaries and safe parsing."),
    ("web", "authn-security", "Authentication Security", "Credential handling and auth flows."),
    ("web", "session-management", "Session Management", "Session lifecycle and protection."),
    ("web", "access-control", "Access Control", "Authorisation models and enforcement."),
    ("web", "sql-injection", "SQL Injection (Lab)", "Recognising and remediating SQLi."),
    ("web", "xss", "Cross-Site Scripting", "Recognising and remediating XSS."),
    ("web", "api-security", "API Security", "Securing REST/GraphQL interfaces."),
    ("web", "file-upload-security", "File Upload Security", "Safe handling of uploaded content."),
    ("web", "ssrf", "Server-Side Request Forgery", "Recognising and preventing SSRF."),
    ("web", "path-traversal", "Path Traversal", "Preventing directory traversal."),
    ("web", "advanced-web", "Advanced Web Security", "Chained vulnerabilities and assessment."),
    # Windows / AD
    ("windows", "windows-fundamentals", "Windows Fundamentals", "Windows OS and command-line basics."),
    ("windows", "windows-administration", "Windows Administration", "Users, services, policies."),
    ("windows", "windows-privesc", "Windows Privilege Concepts", "Windows privilege boundaries."),
    ("identity", "ldap-directory", "LDAP & Directory Services", "Directory concepts and queries."),
    ("identity", "ad-fundamentals", "Active Directory Fundamentals", "Domains, OUs, trusts."),
    ("identity", "kerberos", "Kerberos Concepts", "Ticketing and authentication flows."),
    ("identity", "group-policy", "Group Policy", "Policy application and hardening."),
    ("identity", "identity-security", "Identity Security", "IAM weaknesses and defence."),
    # Assessment / methodology
    ("methodology", "pentest-methodology", "Pentest Methodology", "Structured, authorised testing."),
    ("methodology", "reconnaissance", "Reconnaissance", "Authorised information gathering."),
    ("methodology", "service-enumeration", "Service Enumeration", "Identifying running services."),
    ("methodology", "vuln-assessment", "Vulnerability Assessment", "Finding and verifying weaknesses."),
    ("methodology", "vuln-remediation", "Vulnerability Remediation", "Fixing and verifying fixes."),
    ("methodology", "security-reporting", "Security Reporting", "Clear professional reporting."),
    # Crypto
    ("crypto", "crypto-fundamentals", "Cryptography Fundamentals", "Symmetric/asymmetric, hashing."),
    ("crypto", "tls-certificates", "TLS & Certificates", "Transport security and PKI."),
    ("crypto", "password-security", "Password Security", "Hashing, policy, auditing."),
    # Defensive
    ("defensive", "log-analysis", "Log Analysis", "Reading and correlating logs."),
    ("defensive", "siem-fundamentals", "SIEM Fundamentals", "Centralised monitoring."),
    ("defensive", "detection-engineering", "Detection Engineering", "Writing detection rules."),
    ("defensive", "threat-hunting", "Threat Hunting", "Hypothesis-driven investigation."),
    ("defensive", "incident-response", "Incident Response", "Structured response process."),
    ("defensive", "network-monitoring", "Network Monitoring", "Observing network behaviour."),
    ("defensive", "infrastructure-hardening", "Infrastructure Hardening", "Reducing attack surface."),
    ("defensive", "threat-intelligence", "Threat Intelligence", "Using intel effectively."),
    # Forensics
    ("forensics", "evidence-handling", "Evidence Handling", "Chain of custody and integrity."),
    ("forensics", "filesystems", "Filesystems", "Filesystem structures and metadata."),
    ("forensics", "disk-forensics", "Disk Forensics", "Recovering and examining disk artefacts."),
    ("forensics", "timeline-analysis", "Timeline Analysis", "Reconstructing event sequences."),
    ("forensics", "memory-forensics", "Memory Forensics", "Analysing volatile memory."),
    ("forensics", "network-evidence", "Network Evidence", "Analysing captured traffic."),
    # Malware / RE
    ("reverse", "programming-fundamentals", "Programming Fundamentals", "Core programming concepts."),
    ("reverse", "python-security", "Python for Security", "Scripting security tooling."),
    ("reverse", "c-fundamentals", "C Fundamentals", "Low-level language basics."),
    ("reverse", "computer-architecture", "Computer Architecture", "CPU, memory, registers."),
    ("reverse", "assembly", "Assembly Fundamentals", "Reading disassembly."),
    ("reverse", "debugging", "Debugging", "Dynamic analysis with debuggers."),
    ("reverse", "binary-formats", "Binary Formats", "ELF/PE structure."),
    ("reverse", "reverse-engineering", "Reverse Engineering", "Static and dynamic RE."),
    ("reverse", "memory-safety", "Memory Safety", "Memory-safety classes and mitigations."),
    ("reverse", "malware-analysis", "Malware Analysis", "Safe analysis of malicious code."),
    # Cloud / container
    ("cloud", "docker-security", "Docker Security", "Container isolation and images."),
    ("cloud", "container-networking", "Container Networking", "Container network models."),
    ("cloud", "kubernetes-security", "Kubernetes Security", "Cluster and RBAC security."),
    ("cloud", "cloud-fundamentals", "Cloud Security Fundamentals", "Shared responsibility, IAM."),
    ("cloud", "iac-security", "Infrastructure-as-Code Security", "Securing declarative infra."),
    ("cloud", "network-policies", "Network Policies", "Policy-based micro-segmentation."),
    # Secure development
    ("secdev", "secure-coding", "Secure Coding", "Writing resilient code."),
    ("secdev", "secure-sdlc", "Secure Development", "Security across the SDLC."),
    ("secdev", "security-automation", "Security Automation", "Automating security checks."),
    ("secdev", "security-architecture", "Security Architecture", "Designing secure systems."),
    # General
    ("general", "security-terminology", "Security Terminology", "Core vocabulary and concepts."),
    ("general", "platform-orientation", "Platform Orientation", "Using the Pwnforge platform."),
    ("general", "wireless-security", "Wireless Security", "Wi-Fi security concepts."),
    # OSINT (open-source intelligence — authorised, public-source, ethics-first)
    ("osint", "osint-fundamentals", "OSINT Fundamentals", "Sources, the intelligence cycle, ethics and legality."),
    ("osint", "osint-techniques", "OSINT Techniques", "Search operators, metadata, geolocation, verification."),
    ("osint", "osint-ethics", "OSINT Ethics & OPSEC", "Legal/ethical boundaries and investigator OPSEC."),
    ("osint", "osint-corroboration", "Source Corroboration", "Cross-checking and assessing source reliability."),
    ("osint", "osint-tooling", "OSINT Tooling", "theHarvester, Amass, Shodan, recon-ng and friends."),
    # Tool proficiency (used in authorised labs you own or are permitted to test)
    ("tools", "tool-scanning", "Scanning Tools", "Nmap, Masscan and host/port/service discovery."),
    ("tools", "tool-web-scanners", "Web Scanners", "Nikto, Nuclei and automated web checks."),
    ("tools", "tool-packet-analysis", "Packet Analysis Tools", "Wireshark and tcpdump."),
    ("tools", "tool-web-proxy", "Web Proxy Tools", "Burp Suite and OWASP ZAP."),
    ("tools", "tool-content-discovery", "Content Discovery Tools", "gobuster, ffuf, dirb, feroxbuster."),
    ("tools", "tool-exploitation-frameworks", "Exploitation Frameworks", "Metasploit Framework in lab use."),
    ("tools", "tool-password-auditing", "Password Auditing Tools", "John, Hashcat, Hydra for authorised audits."),
    ("tools", "tool-netcat", "Network Utilities", "netcat, socat and basic connectivity tooling."),
    ("tools", "tool-proxying", "Pivoting & Proxying", "proxychains, Tor and SSH tunnelling."),
    ("tools", "tool-ad-tooling", "AD/Windows Tooling", "Impacket, CrackMapExec, BloodHound, Responder (lab)."),
    ("tools", "tool-re-tooling", "Reverse-Engineering Tools", "Ghidra, radare2, gdb/pwndbg."),
    ("tools", "tool-forensics-tooling", "Forensics Tools", "Volatility, Autopsy and The Sleuth Kit."),
    ("tools", "tool-data-decoding", "Data & Decoding Tools", "CyberChef, hashid, base/encoding analysis."),
    ("tools", "tool-http-clients", "HTTP Clients", "curl and HTTPie for crafting requests."),
]


def all_competency_keys() -> set[str]:
    return {c[1] for c in COMPETENCIES}
