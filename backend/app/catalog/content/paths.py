"""Learning paths. Steps reference real course ids and lab ids."""
from __future__ import annotations


def _p(id, title, description, specialization, dmin, dmax, steps, tags=None):
    return dict(id=id, title=title, description=description,
                specialization=specialization, difficulty_min=dmin, difficulty_max=dmax,
                tags=tags or [], steps=steps)


def _s(order, course=None, lab=None, required=True, note=""):
    return dict(order=order, course_id=course, lab_id=lab, required=required, note=note)


LEARNING_PATHS = [
    _p("path-complete-beginner", "Complete Beginner",
       "Build a practical foundation in safe lab use, Linux, networks, HTTP, service discovery, and basic reporting. Finish by demonstrating that you can inventory a host and explain what your evidence shows.",
       None, "orientation", "easy",
       [_s(1, "pwnforge-orientation"), _s(2, "cybersecurity-fundamentals"),
        _s(3, "linux-fundamentals"),
        _s(4, lab="linux-practice-basic", required=False, note="Practise core Linux on a real machine"),
        _s(5, "networking-fundamentals"), _s(6, "bash-for-security"), _s(7, "http-https"),
        _s(8, "service-enumeration"),
        _s(9, lab="network-basics-lab", required=False, note="Scan and enumerate a small network"),
        _s(10, lab="web-security-lab", required=False, note="Your first security lab"),
        _s(11, "vulnerability-assessment"), _s(12, "security-reporting"),
        _s(13, lab="foothold-default-creds", required=False,
            note="Break into your first box: default credentials")],
       tags=["beginner", "foundation"]),

    _p("path-web-pentest", "Web Penetration Testing",
       "Progress from HTTP fundamentals through input handling, authentication, sessions, access control, SQL injection, and XSS. Practise each stage on an isolated application, then verify a fix and write a reproducible finding.",
       "web", "beginner", "expert",
       [_s(1, "http-https"), _s(2, "web-technologies"), _s(3, "linux-fundamentals"),
        _s(4, "sql-fundamentals"), _s(5, "authentication-security"),
        _s(6, "session-management-course"), _s(7, "access-control-course"),
        _s(8, "web-application-security"),
        _s(9, lab="foothold-default-creds", required=False, note="Warm up: get a foothold on a host"),
        _s(10, "sql-injection-labs"),
        _s(11, "cross-site-scripting"), _s(12, "api-security"),
        _s(13, lab="web-security-lab", note="Intermediate web lab"),
        _s(14, "advanced-web-security"),
        _s(15, lab="foothold-weak-ssh", required=False, note="Pivot: gain access to a host behind the app"),
        _s(16, "security-reporting", note="Final web assessment reporting")],
       tags=["web", "offensive"]),

    _p("path-infra-pentest", "Infrastructure Penetration Testing",
       "Learn to scope an infrastructure assessment, map routes and services, inspect Linux and Windows hosts, validate exposure safely, and explain initial access and privilege boundaries with evidence.",
       "pentest", "beginner", "advanced",
       [_s(1, "networking-fundamentals"), _s(2, "linux-fundamentals"),
        _s(3, "windows-fundamentals"), _s(4, "dns-network-services"),
        _s(5, "reconnaissance"), _s(6, "service-enumeration"),
        _s(7, lab="network-basics-lab", required=False, note="Enumerate a small isolated network"),
        _s(8, "vulnerability-assessment"),
        _s(9, lab="foothold-default-creds", required=False, note="Initial access: default credentials"),
        _s(10, "linux-privilege-escalation-concepts"),
        _s(11, "windows-privilege-escalation-concepts"),
        _s(12, lab="foothold-weak-ssh", required=False, note="Initial access: a weak password"),
        _s(13, lab="foothold-enumerate-user", required=False,
            note="Initial access: find the user, then the password"),
        _s(14, lab="enterprise-identity-lab", note="Advanced multi-service lab"),
        _s(15, "security-reporting")],
       tags=["infrastructure", "offensive"]),

    _p("path-active-directory", "Active Directory Security",
       "Build from Windows and authentication fundamentals to directory enumeration, identity permissions, privilege boundaries, and an isolated enterprise directory capstone. You will document effective access and justify least-privilege changes.",
       "active-directory", "beginner", "expert",
       [_s(1, "windows-fundamentals"), _s(2, "windows-administration"),
        _s(3, "authentication-security"),
        _s(4, lab="foothold-default-creds", required=False, note="Get an initial foothold on a host"),
        _s(5, "active-directory-fundamentals"),
        _s(6, "identity-access-management"),
        _s(7, "windows-privilege-escalation-concepts"),
        _s(8, lab="enterprise-identity-lab", note="Enterprise directory lab")],
       tags=["identity", "windows"]),

    _p("path-defensive", "Defensive Security",
       "Move from host and network telemetry to SIEM searches, detection engineering, threat hunting, incident timelines, and forensic reporting. Finish by validating a detection and communicating what the evidence can—and cannot—prove.",
       "defensive", "beginner", "advanced",
       [_s(1, "cybersecurity-fundamentals"), _s(2, "linux-administration"),
        _s(3, lab="linux-admin-lab", required=False, note="Administer and harden a real server"),
        _s(4, "windows-administration"), _s(5, "log-analysis"),
        _s(6, "network-monitoring"), _s(7, "siem-fundamentals"),
        _s(8, "detection-engineering"), _s(9, "threat-hunting"),
        _s(10, "incident-response"), _s(11, "digital-forensics"),
        _s(12, lab="malware-analysis-lab", required=False, note="Triage a sample to build detections"),
        _s(13, lab="defensive-monitoring-lab", note="Advanced investigation lab")],
       tags=["defensive", "blue-team"]),

    _p("path-reverse-engineering", "Reverse Engineering",
       "Build the programming and memory-safety foundation for safe binary triage, static analysis, controlled dynamic analysis, and malware reporting. Practise an evidence-led workflow in isolated analysis environments.",
       "reverse", "easy", "expert",
       [_s(1, "bash-for-security"), _s(2, "python-for-security"),
        _s(3, "reverse-engineering-fundamentals"), _s(4, "memory-safety"),
        _s(5, "malware-analysis-fundamentals"),
        _s(6, lab="malware-analysis-lab", required=False, note="Triage a real sample in isolation"),
        _s(7, lab="reverse-engineering-lab", note="Final RE challenge")],
       tags=["reverse", "re"]),

    _p("path-container-infra", "Container and Infrastructure Security",
       "Progress from Linux and network foundations to container runtime controls, Kubernetes isolation, segmentation, and infrastructure-as-code review. Practise checking image provenance, identity, capabilities, mounts, and network policy.",
       "cloud", "easy", "advanced",
       [_s(1, "linux-fundamentals"),
        _s(2, lab="linux-practice-basic", required=False, note="Practise Linux on a real box"),
        _s(3, "linux-administration"),
        _s(4, lab="linux-admin-lab", required=False, note="Administer and harden a server"),
        _s(5, "networking-fundamentals"), _s(6, "docker-security"),
        _s(7, "kubernetes-security"), _s(8, "network-segmentation"),
        _s(9, "iac-security"),
        _s(10, lab="container-security-lab", note="Advanced container lab")],
       tags=["cloud", "container"]),

    _p("path-digital-forensics", "Digital Forensics",
       "Learn evidence preservation, hashes, file and network artefacts, event timelines, and incident reconstruction. Each practice lab reinforces provenance, time context, and conclusions that stay within the evidence.",
       "forensics", "easy", "advanced",
       [_s(1, "log-analysis"), _s(2, "digital-forensics"),
        _s(3, "network-monitoring"), _s(4, "incident-response"),
        _s(5, "malware-analysis-fundamentals"),
        _s(6, lab="malware-analysis-lab", required=False, note="Safe malware triage"),
        _s(7, lab="forensics-workstation-lab", note="Advanced investigation challenge")],
       tags=["forensics", "dfir"]),

    _p("path-hacker-toolkit", "The Hacker's Toolkit",
       "Learn when and how to use scanners, HTTP clients, proxies, authentication auditors, SMB tooling, packet analysers, and reverse-engineering tools. Every practical step stays in the authorised lab scope and requires you to validate the output.",
       "pentest", "easy", "advanced",
       [_s(1, "tool-nmap"),
        _s(2, lab="network-basics-lab", required=False, note="Use nmap against a real network"),
        _s(3, "tool-content-discovery"), _s(4, "tool-http-clients"),
        _s(5, "tool-burp"), _s(6, "tool-sqlmap"), _s(7, "tool-netcat"),
        _s(8, "tool-hydra"),
        _s(9, lab="foothold-default-creds", required=False, note="Crack a login: default credentials"),
        _s(10, "tool-john"), _s(11, "tool-hashcat"),
        _s(12, lab="foothold-weak-ssh", required=False, note="Crack a login: a weak SSH password"),
        _s(13, "tool-metasploit"), _s(14, "tool-smb-enum"), _s(15, "tool-impacket"),
        _s(16, lab="foothold-enumerate-user", required=False,
            note="Find the user, then crack the password"),
        _s(17, "tool-bloodhound"), _s(18, "tool-wireshark"), _s(19, "tool-ghidra"),
        _s(20, lab="enterprise-identity-lab", note="Put the toolkit to work", required=False)],
       tags=["tools", "hands-on"]),

    _p("path-osint", "OSINT & Reconnaissance",
       "Define a lawful collection question, gather public-source information, corroborate it, assess confidence, protect operational security, and write a careful report. Labs require source and time notes so claims remain auditable.",
       "osint", "easy", "advanced",
       [_s(1, "osint-fundamentals"), _s(2, "reconnaissance"),
        _s(3, lab="network-basics-lab", required=False, note="Hands-on recon: enumerate a target network"),
        _s(4, "osint-techniques"), _s(5, "osint-tools"),
        _s(6, "osint-opsec-reporting"),
        _s(7, lab="osint-investigation-lab", note="OSINT investigation challenge")],
       tags=["osint", "recon"]),
]


# Measurable outcomes and an integrative practical standard make each path's
# promise concrete: learners demonstrate the listed skills and produce a
# reviewable capstone artifact.
_PATH_MASTERY = {
    "path-complete-beginner": (
        ["Navigate a Linux host and explain file ownership and permissions",
         "Map a subnet, route, open port, and listening service using evidence",
         "Explain how an HTTP request reaches an application and where input is handled",
         "Distinguish an observation from an assumption in a security finding",
         "Write a concise finding with impact, evidence, and a practical fix"],
        {"title": "Host and service inventory",
         "scenario": "Given an isolated host and its network scope, create a reproducible inventory and explain what is exposed.",
         "success_criteria": ["Identify the target and scope before active checks",
                              "Report discovered services with command output or equivalent evidence",
                              "Explain one relevant risk and a proportionate remediation",
                              "Separate verified facts from assumptions"]}),
    "path-web-pentest": (
        ["Trace browser requests, application logic, and database interactions",
         "Test authentication, sessions, access control, and input handling safely",
         "Verify SQL injection and cross-site scripting findings with controlled evidence",
         "Recommend fixes that address the underlying cause and retest them",
         "Write a reproducible web finding with scope, impact, and evidence"],
        {"title": "Web application assessment",
         "scenario": "Assess an isolated application from its exposed endpoints through one verified weakness and its remediation.",
         "success_criteria": ["Record the exact request and response that support each finding",
                              "Demonstrate the issue with a controlled input and no unrelated data access",
                              "Explain impact and the vulnerable trust boundary",
                              "Retest the proposed fix and document residual limitations"]}),
    "path-infra-pentest": (
        ["Scope an infrastructure assessment and map hosts, routes, and services",
         "Identify service software and versions using safe, bounded probes",
         "Assess Linux and Windows configuration and privilege boundaries",
         "Validate a security issue without exceeding the lab's written scope",
         "Deliver an evidence-based report with prioritised remediation"],
        {"title": "Isolated infrastructure assessment",
         "scenario": "Assess a small isolated network from discovery through validation and reporting.",
         "success_criteria": ["List in-scope hosts and discovered services with evidence",
                              "Explain how the observed network path and filtering affect reachability",
                              "Validate one weakness and state what the result does not prove",
                              "Prioritise a fix and include a verification step"]}),
    "path-active-directory": (
        ["Explain domain, user, group, authentication, and policy relationships",
         "Enumerate directory objects and effective permissions with approved methods",
         "Trace inherited access and identify an excessive privilege path",
         "Recommend least-privilege changes without breaking required access",
         "Document a directory finding and the evidence needed to reproduce it"],
        {"title": "Directory access review",
         "scenario": "Review the isolated directory lab and explain how a selected identity reaches a protected resource.",
         "success_criteria": ["Map the relevant users, groups, roles, and resource",
                              "Show the effective permission path with supporting evidence",
                              "Identify one excessive grant and a least-privilege correction",
                              "Verify both an allowed workflow and the intended restriction"]}),
    "path-defensive": (
        ["Collect and interpret host, identity, and network telemetry with time context",
         "Build a detection from an observable behaviour and test it against evidence",
         "Hunt a stated hypothesis and record supporting and contradicting evidence",
         "Reconstruct an incident timeline while preserving source provenance",
         "Communicate confirmed facts, uncertainty, impact, and next actions"],
        {"title": "Detection and incident investigation",
         "scenario": "Investigate a seeded activity sequence, validate one detection, and report the incident evidence.",
         "success_criteria": ["Cite the source, timestamp, and event details for key claims",
                              "Explain why the detection matches and where false positives may occur",
                              "Build an ordered timeline that distinguishes facts from hypotheses",
                              "Recommend containment and follow-up evidence collection"]}),
    "path-reverse-engineering": (
        ["Identify binary format, architecture, hashes, strings, and relevant metadata",
         "Use disassembly and controlled debugging to trace a program's behaviour",
         "Explain memory-safety issues from code paths and observed effects",
         "Contain samples and avoid unsafe execution outside the isolated lab",
         "Produce a cautious analysis report with indicators and limitations"],
        {"title": "Contained binary triage",
         "scenario": "Analyse the supplied isolated sample from static triage to a supported behaviour report.",
         "success_criteria": ["Record hash, file type, architecture, and analysis environment",
                              "Support behaviour claims with static or controlled dynamic evidence",
                              "Separate indicators from hypotheses and identify uncertainty",
                              "Describe containment and a safe next analysis step"]}),
    "path-container-infra": (
        ["Explain container images, registries, runtime isolation, and workload identity",
         "Identify risky capabilities, mounts, privileges, and exposed ports",
         "Review Kubernetes identity and network policy boundaries",
         "Inspect infrastructure-as-code plans for secrets, exposure, and drift",
         "Verify a least-privilege remediation against the resulting workload"],
        {"title": "Container workload hardening review",
         "scenario": "Review a disposable container host and its declared workload configuration, then verify a scoped hardening change.",
         "success_criteria": ["Inventory images, identities, privileges, mounts, and exposed services",
                              "Explain one concrete path from configuration to workload risk",
                              "Propose a minimal change and inspect the rendered result",
                              "Verify required behaviour still works and excess access is removed"]}),
    "path-digital-forensics": (
        ["Acquire and hash evidence while preserving provenance and chain of custody",
         "Extract file-system, event, and network artefacts using repeatable methods",
         "Correlate timestamps across sources and record time-zone assumptions",
         "Identify indicators while distinguishing them from attribution claims",
         "Write a forensic report whose conclusions are bounded by the evidence"],
        {"title": "Evidence-led incident reconstruction",
         "scenario": "Examine the provided host and network evidence, preserve integrity, and reconstruct the supported event sequence.",
         "success_criteria": ["Record evidence identifiers and pre/post analysis hashes",
                              "Cite artefacts and time context for each timeline entry",
                              "Explain alternative interpretations and evidence gaps",
                              "Keep conclusions and recommendations within what the evidence supports"]}),
    "path-hacker-toolkit": (
        ["Choose scanners, HTTP clients, proxies, and packet tools for a stated question",
         "Keep every probe within a written target and rate scope",
         "Interpret output and validate important results with a second observation",
         "Protect credentials and preserve relevant command and response evidence",
         "Explain tool limitations and produce a reproducible result"],
        {"title": "Scoped multi-tool assessment",
         "scenario": "Use a small approved range to answer a service and application question with complementary tools.",
         "success_criteria": ["State target scope and use bounded options",
                              "Identify services using both remote and host-side evidence where available",
                              "Correlate tool output and explain discrepancies",
                              "Save reproducible evidence without exposing secrets"]}),
    "path-osint": (
        ["Define a lawful collection question, subject, timeframe, and data limits",
         "Record source provenance, collection time, and the exact claim supported",
         "Corroborate important claims with independent sources and check contradictions",
         "Assign confidence and distinguish fact from inference",
         "Write a privacy-aware report that explains source and collection limitations"],
        {"title": "Auditable public-source investigation",
         "scenario": "Investigate a bounded fictional subject, corroborate a claim, and produce a source-linked report.",
         "success_criteria": ["Record source URL, collection time, and relevant evidence for each claim",
                              "Use independent corroboration and note contradictory information",
                              "Explain confidence and separate inference from fact",
                              "Minimise personal data and document the lawful scope"]}),
}

for _path in LEARNING_PATHS:
    _path["outcomes"], _path["capstone"] = _PATH_MASTERY[_path["id"]]


# Insert the new hands-on steps immediately after the course that teaches the
# skill. Every learning path now has an explicit, ordered course/lab sequence.
_PATH_LAB_INSERTIONS = {
    "path-complete-beginner": [
        ("lab", "linux-practice-basic", "lab-linux-smb-enumeration", "Inventory Linux and SMB services"),
        ("lab", "linux-practice-basic", "lab-alpine-service-hardening", "Review service state and exposure"),
        ("course", "networking-fundamentals", "lab-first-firewall-map", "Map ports and firewall exposure"),
        ("course", "http-https", "lab-http-input-validation", "Trace input through an HTTP request"),
        ("course", "service-enumeration", "lab-nginx-service-inventory", "Connect service names to listening sockets"),
    ],
    "path-web-pentest": [
        ("course", "web-technologies", "lab-web-input-validation-review", "Trace input to a validation boundary"),
        ("course", "authentication-security", "lab-web-authentication-audit", "Review a login service"),
        ("course", "session-management-course", "lab-session-token-audit", "Inspect session handling"),
        ("course", "sql-injection-labs", "lab-sql-injection-practice", "Verify a database-backed endpoint safely"),
        ("course", "cross-site-scripting", "lab-xss-output-encoding", "Check output encoding"),
    ],
    "path-infra-pentest": [
        ("course", "networking-fundamentals", "lab-linux-firewall-enumeration", "Compare listeners and firewall policy"),
        ("course", "dns-network-services", "lab-samba-service-enumeration", "Enumerate a file-sharing service"),
        ("course", "reconnaissance", "lab-alpine-host-enumeration", "Build an evidence-backed host inventory"),
        ("course", "service-enumeration", "lab-tls-nginx-audit", "Inspect service and certificate evidence"),
        ("course", "linux-privilege-escalation-concepts", "lab-smb-privilege-boundaries", "Review local and share permissions"),
    ],
    "path-active-directory": [
        ("course", "windows-fundamentals", "lab-identity-linux-groups", "Review users and effective group access"),
        ("course", "active-directory-fundamentals", "lab-samba-share-inventory", "Inventory SMB shares before the domain lab"),
        ("course", "active-directory-fundamentals", "lab-samba-account-enumeration", "Record account and service questions"),
        ("course", "identity-access-management", "lab-samba-service-hardening", "Recommend a least-privilege change"),
        ("course", "windows-privilege-escalation-concepts", "lab-identity-privilege-boundaries", "Trace an identity privilege boundary"),
    ],
    "path-defensive": [
        ("course", "log-analysis", "lab-linux-auth-log-review", "Review authentication evidence"),
        ("course", "network-monitoring", "lab-network-evidence-review", "Interpret endpoint and time context"),
        ("course", "detection-engineering", "lab-detection-rule-practice", "Create and validate a detection idea"),
        ("course", "threat-hunting", "lab-threat-hunt-practice", "Test a hunt hypothesis"),
        ("course", "incident-response", "lab-incident-timeline-practice", "Build an incident timeline"),
    ],
    "path-reverse-engineering": [
        ("course", "python-for-security", "lab-static-analysis-capstone", "Start a static triage workflow"),
        ("course", "reverse-engineering-fundamentals", "lab-re-backup-agent", "Inspect component metadata and strings"),
        ("course", "memory-safety", "lab-re-job-runner", "Relate code behaviour to memory-safety risks"),
        ("course", "malware-analysis-fundamentals", "lab-malware-triage-capstone", "Triage within an isolated environment"),
        ("lab", "reverse-engineering-lab", "lab-re-message-queue", "Complete a final isolated component analysis"),
    ],
    "path-container-infra": [
        ("course", "linux-administration", "lab-container-host-audit", "Inventory container host services"),
        ("course", "networking-fundamentals", "lab-segmentation-verification", "Verify allowed and blocked paths"),
        ("course", "docker-security", "lab-container-runtime-hardening", "Review runtime privileges and mounts"),
        ("course", "kubernetes-security", "lab-container-image-policy", "Review image and workload identity"),
        ("course", "iac-security", "lab-container-iac-review", "Review rendered configuration and drift"),
    ],
    "path-digital-forensics": [
        ("course", "log-analysis", "lab-disk-forensics-import-tool", "Preserve and inventory evidence"),
        ("course", "digital-forensics", "lab-disk-forensics-backup-agent", "Verify integrity and file-system artefacts"),
        ("course", "network-monitoring", "lab-network-forensics-webhook", "Review network artefacts"),
        ("course", "incident-response", "lab-incident-evidence-timeline", "Correlate events in time"),
        ("course", "malware-analysis-fundamentals", "lab-malware-triage-search-index", "Perform safe first-pass triage"),
    ],
    "path-hacker-toolkit": [
        ("course", "tool-nmap", "lab-tool-range-ssh", "Use service detection against an isolated host"),
        ("course", "tool-content-discovery", "lab-tool-web-proxy", "Inspect application requests through a proxy"),
        ("course", "tool-smb-enum", "lab-tool-range-smb", "Enumerate SMB in the lab scope"),
        ("course", "tool-http-clients", "lab-toolkit-ctf-web", "Verify a response with an HTTP client"),
        ("course", "tool-wireshark", "lab-toolkit-service-discovery", "Compare packet and socket evidence"),
    ],
    "path-osint": [
        ("course", "osint-fundamentals", "lab-osint-source-confidence", "Record provenance and confidence"),
        ("course", "reconnaissance", "lab-osint-recon-tooling", "Choose a bounded collection method"),
        ("course", "osint-techniques", "lab-osint-corroboration", "Corroborate independent observations"),
        ("course", "osint-tools", "lab-osint-api-gateway-footprint", "Analyse a bounded simulated footprint"),
        ("course", "osint-opsec-reporting", "lab-osint-opsec-review", "Plan ethical collection and reporting"),
    ],
}


for _path in LEARNING_PATHS:
    _insertions = _PATH_LAB_INSERTIONS[_path["id"]]
    _after = {}
    for _kind, _item, _lab_id, _note in _insertions:
        _after.setdefault((_kind, _item), []).append((_lab_id, _note))
    _expanded = []
    for _step in sorted(_path["steps"], key=lambda step: step["order"]):
        _expanded.append(_step)
        _kind = "course" if _step.get("course_id") else "lab"
        _key = _step.get("course_id") or _step.get("lab_id")
        if (_kind, _key) in _after:
            for _lab_id, _note in _after.pop((_kind, _key)):
                _expanded.append(_s(0, lab=_lab_id, note=_note))
    if _after:
        raise ValueError(f"Unknown course/lab placement in {_path['id']}: {sorted(_after)}")
    for _order, _step in enumerate(_expanded, start=1):
        _step["order"] = _order
    _path["steps"] = _expanded

assert sum(len(items) for items in _PATH_LAB_INSERTIONS.values()) == 50
