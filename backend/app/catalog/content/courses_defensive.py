"""Cryptography, defensive security, forensics and reverse-engineering courses."""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, lesson, mcq, short,
)


def _c(id, title, cat, desc, difficulty, spec, prereqs, lessons, qs,
       cprereqs=None, lab=None):
    return course(id, title, desc, difficulty, cat, specialization=spec,
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=[cat], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


L = lesson
COURSES = [
    _c("cryptography-fundamentals", "Cryptography Fundamentals", "crypto",
       "Symmetric and asymmetric cryptography, hashing and their correct use.",
       "intermediate", "crypto", ["cybersecurity-fundamentals"],
       [L("Symmetric, asymmetric, hashing", "intermediate", 20, "crypto-fundamentals",
          "Symmetric crypto (AES) uses one shared key for speed; asymmetric crypto (RSA, "
          "ECC) uses a key pair to solve key distribution and enable signatures. Hashes "
          "(SHA-256) are one-way integrity checks, not encryption. Using the right "
          "primitive for the job — and never rolling your own — is the core discipline.",
          exercises=[mcq("A hash function provides:",
                         ["Confidentiality", "One-way integrity", "Key exchange",
                          "Compression"], "One-way integrity", "crypto-fundamentals",
                         "Hashes verify integrity, they do not encrypt.")],
          hints=["Hashing is not encryption."])],
       [mcq("Which solves key distribution?", ["Symmetric", "Asymmetric", "Hashing",
            "Base64"], "Asymmetric", "crypto-fundamentals", "Public-key crypto helps distribute keys."),
        short("Never roll your own ___.", "crypto", "crypto-fundamentals",
              "Use vetted libraries.")]),

    _c("tls-and-certificates", "TLS and Certificates", "crypto",
       "Transport security, certificates and public-key infrastructure.",
       "intermediate", "crypto", ["cryptography-fundamentals", "http-https"],
       [L("How TLS protects a connection", "intermediate", 20, "tls-certificates",
          "TLS authenticates the server via a certificate signed by a trusted CA, then "
          "negotiates keys to encrypt and integrity-protect the session. Certificate "
          "validation (chain, hostname, expiry, revocation) is what stops impersonation. "
          "Misconfigurations — expired certs, weak ciphers, missing validation — undermine "
          "the whole guarantee.",
          exercises=[mcq("Certificate validation prevents:",
                         ["Slow pages", "Server impersonation", "Large downloads",
                          "DNS caching"], "Server impersonation", "tls-certificates",
                         "Validation binds the key to the hostname.")],
          hints=["Chain + hostname + expiry + revocation all matter."])],
       [short("Who signs a server certificate (2-letter)?", "CA", "tls-certificates",
              "A Certificate Authority."),
        mcq("A client must validate the cert's:", ["Colour", "Hostname and chain",
            "File size", "Port"], "Hostname and chain", "tls-certificates",
            "Validate hostname and chain.")]),

    _c("log-analysis", "Log Analysis", "defensive",
       "Read, filter and correlate logs to understand what happened.",
       "easy", "defensive", ["linux-administration"],
       [L("Where logs live and what they say", "easy", 15, "log-analysis",
          "Linux logs under `/var/log` (auth.log, syslog, service logs); Windows uses the "
          "Event Log. Effective analysis means filtering to the relevant time window and "
          "events, then correlating across sources. A single log line rarely tells the "
          "story; the sequence does.",
          exercises=[mcq("Correlating multiple logs helps because:",
                         ["Logs are short", "A sequence reveals what one line cannot",
                          "It saves disk", "It is faster"],
                         "A sequence reveals what one line cannot", "log-analysis",
                         "Correlation reconstructs events.")],
          hints=["Pin the time window first."]),
        L("From logs to findings", "easy", 15, "log-analysis",
          "Turn raw logs into findings: identify the actor, the action, the target and "
          "the outcome. Note gaps (missing logs are themselves a finding). Clear, "
          "time-ordered notes become the basis of an incident timeline.",
          exercises=[short("Missing logs are themselves a ___.", "finding",
                           "log-analysis", "Gaps matter.")])],
       [mcq("Linux auth events are typically in:", ["/etc/passwd", "/var/log/auth.log",
            "/proc", "/boot"], "/var/log/auth.log", "log-analysis",
            "auth.log records authentication."),
        short("Correlate logs to build a ___ (time-ordered).", "timeline",
              "timeline-analysis", "Timelines order events.")],
       lab="defensive-monitoring-lab"),

    _c("siem-fundamentals", "SIEM Fundamentals", "defensive",
       "Centralised collection, normalisation and alerting.",
       "intermediate", "defensive", ["log-analysis"],
       [L("Why centralise", "intermediate", 15, "siem-fundamentals",
          "A SIEM collects logs from many sources, normalises them to a common schema, "
          "and lets you search and alert across the estate. Centralisation defeats "
          "attempts to hide by clearing one host's logs and enables correlation rules "
          "that no single host could evaluate.",
          exercises=[mcq("A key SIEM benefit:", ["Faster CPUs",
                         "Cross-source correlation and tamper resistance", "More disk",
                          "Nicer fonts"], "Cross-source correlation and tamper resistance",
                         "siem-fundamentals", "Centralisation enables correlation.")],
          hints=["Normalisation makes cross-source rules possible."])],
       [short("SIEM normalises logs to a common ___.", "schema", "siem-fundamentals",
              "A shared schema."),
        mcq("Forwarding logs off-host helps against:", ["Slow disks",
            "Local log tampering", "DNS", "TLS"], "Local log tampering",
            "siem-fundamentals", "Off-host copies resist tampering.")],
       lab="defensive-monitoring-lab"),

    _c("detection-engineering", "Detection Engineering", "defensive",
       "Write precise detection rules that balance signal and noise.",
       "hard", "defensive", ["siem-fundamentals"],
       [L("Good detections", "hard", 20, "detection-engineering",
          "A good detection targets attacker behaviour (technique) rather than a single "
          "indicator, is specific enough to limit false positives, and documents the "
          "expected response. Map detections to a framework like MITRE ATT&CK so coverage "
          "is measurable and gaps are visible.",
          exercises=[mcq("A durable detection targets:",
                         ["A single IP", "Attacker behaviour/technique", "A filename only",
                          "A port only"], "Attacker behaviour/technique",
                         "detection-engineering", "Behaviour-based rules survive IOC changes.")],
          hints=["Behaviour outlasts indicators."])],
       [mcq("Detections are often mapped to:", ["OSI", "MITRE ATT&CK", "DNS", "TLS"],
            "MITRE ATT&CK", "detection-engineering", "ATT&CK organises techniques."),
        short("Rules balance signal against ___ (false positives).", "noise",
              "detection-engineering", "Signal vs noise.")]),

    _c("threat-hunting", "Threat Hunting", "defensive",
       "Proactively search for intrusions with hypotheses.",
       "advanced", "defensive", ["detection-engineering"],
       [L("Hypothesis-driven hunting", "advanced", 20, "threat-hunting",
          "Hunting assumes something may already be present and tests specific "
          "hypotheses ('if an attacker used technique X, I would see Y'). You gather the "
          "relevant data, look for the expected artefacts, and either confirm, refute or "
          "refine. Findings feed new detections so the hunt improves future coverage.",
          exercises=[mcq("Threat hunting is:", ["Waiting for alerts",
                         "Hypothesis-driven proactive search", "Patching", "Scanning only"],
                         "Hypothesis-driven proactive search", "threat-hunting",
                         "Hunting is proactive and hypothesis-led.")],
          hints=["State the hypothesis before you look."])],
       [short("Hunting is driven by a ___.", "hypothesis", "threat-hunting",
              "Hypotheses guide hunts."),
        mcq("Hunt findings should become:", ["New detections", "Deleted logs",
            "Nothing", "Faster disks"], "New detections", "threat-hunting",
            "Feed results back into detection.")]),

    _c("incident-response", "Incident Response", "defensive",
       "A structured process for handling security incidents.",
       "intermediate", "defensive", ["log-analysis"],
       [L("The IR lifecycle", "intermediate", 20, "incident-response",
          "A common model: Preparation → Identification → Containment → Eradication → "
          "Recovery → Lessons Learned. Containment limits damage; eradication removes the "
          "cause; recovery restores service safely. Preparation (plans, access, logging) "
          "determines how well the rest goes.",
          exercises=[mcq("Which phase limits ongoing damage?",
                         ["Recovery", "Containment", "Lessons learned", "Preparation"],
                         "Containment", "incident-response", "Containment stops the bleeding.")],
          hints=["Prepare before, learn after."])],
       [short("Phase after eradication?", "recovery", "incident-response",
              "Recovery follows eradication."),
        mcq("The final phase is:", ["Identification", "Lessons learned", "Containment",
            "Detection"], "Lessons learned", "incident-response", "Review closes the loop.")],
       lab="defensive-monitoring-lab"),

    _c("digital-forensics", "Digital Forensics", "forensics",
       "Handle evidence and examine artefacts soundly.",
       "intermediate", "forensics", ["linux-administration"],
       [L("Evidence integrity", "intermediate", 20, "evidence-handling",
          "Sound forensics preserves evidence integrity: hash data on acquisition, work "
          "from copies, and maintain a chain of custody. If integrity is not provable, "
          "conclusions are not defensible. Document every action with timestamps.",
          exercises=[mcq("First step to preserve evidence integrity:",
                         ["Edit the file", "Hash and work from a copy", "Delete logs",
                          "Reboot"], "Hash and work from a copy", "evidence-handling",
                         "Hash, then analyse copies.")],
          hints=["Never analyse the only copy."]),
        L("Filesystem artefacts", "intermediate", 15, "filesystems",
          "Filesystems store timestamps (MACB), deleted-file remnants and metadata that "
          "reconstruct activity. Understanding how a filesystem records changes lets you "
          "build an accurate timeline and spot tampering.",
          exercises=[short("Timestamps help build a ___.", "timeline", "timeline-analysis",
                           "Timelines from timestamps.")])],
       [mcq("Chain of custody documents:", ["Disk speed",
            "Who handled evidence and when", "CPU model", "RAM"],
            "Who handled evidence and when", "evidence-handling", "It tracks handling."),
        short("Acquire then verify with a ___.", "hash", "evidence-handling",
              "Hashes prove integrity.")],
       lab="forensics-workstation-lab"),

    _c("reverse-engineering-fundamentals", "Reverse Engineering Fundamentals", "reverse",
       "Static and dynamic analysis of compiled programs.",
       "advanced", "reverse", ["python-for-security"],
       [L("Static vs dynamic", "advanced", 20, "reverse-engineering",
          "Static analysis examines a binary without running it (disassembly, strings, "
          "structure); dynamic analysis observes it executing in a controlled, isolated "
          "environment under a debugger. Each reveals what the other hides. Always analyse "
          "untrusted binaries inside isolation, exactly like Pwnforge's disposable VMs.",
          exercises=[mcq("Dynamic analysis means:",
                         ["Reading source", "Observing execution in isolation",
                          "Compiling", "Signing"], "Observing execution in isolation",
                         "reverse-engineering", "Dynamic = running it safely.")],
          hints=["Combine both; isolate always."]),
        L("Binary formats", "advanced", 15, "binary-formats",
          "ELF (Linux) and PE (Windows) binaries have headers, sections (code, data) and "
          "symbol/import tables. Reading these structures tells you how a program is laid "
          "out before you ever look at instructions.",
          exercises=[short("Linux executable format (acronym)?", "ELF", "binary-formats",
                           "ELF on Linux.")])],
       [mcq("Analyse untrusted binaries:", ["On your host", "In isolation",
            "On production", "In email"], "In isolation", "malware-analysis",
            "Always isolate untrusted code."),
        short("Windows executable format (acronym)?", "PE", "binary-formats",
              "PE on Windows.")],
       lab="reverse-engineering-lab"),

    _c("memory-safety", "Memory Safety", "reverse",
       "Memory-safety vulnerability classes and modern mitigations.",
       "advanced", "reverse", ["reverse-engineering-fundamentals"],
       [L("Classes and mitigations", "advanced", 20, "memory-safety",
          "Memory-safety bugs (buffer overflows, use-after-free) arise in languages "
          "without automatic bounds/lifetime checks. Modern mitigations — ASLR, DEP/NX, "
          "stack canaries, and memory-safe languages — raise the bar. The durable fix is "
          "to prevent the bug class: bounds checking, safe APIs, and memory-safe "
          "languages where possible.",
          exercises=[mcq("A mitigation that randomises memory layout:",
                         ["DEP", "ASLR", "Canary", "NX"], "ASLR", "memory-safety",
                         "ASLR randomises addresses.")],
          hints=["The best fix removes the bug class entirely."])],
       [short("Mitigation that marks memory non-executable (acronym)?", "NX",
              "memory-safety", "NX/DEP."),
        mcq("Durable fix for memory-safety bugs:", ["Bigger RAM",
            "Memory-safe languages / bounds checks", "Faster CPU", "More threads"],
            "Memory-safe languages / bounds checks", "memory-safety",
            "Prevent the class.")]),

    _c("malware-analysis-fundamentals", "Malware Analysis Fundamentals", "forensics",
       "Safely triage and analyse malicious software in isolation.",
       "advanced", "reverse", ["reverse-engineering-fundamentals"],
       [L("Safe triage", "advanced", 20, "malware-analysis",
          "Analysis happens only in isolated, monitored environments with no path to "
          "production or the internet unless deliberately controlled. Triage establishes "
          "basic properties (hashes, type, strings, behaviour indicators) before deeper "
          "static/dynamic analysis. The goal is understanding and detection, never "
          "redistribution.",
          exercises=[mcq("Malware is analysed in:",
                         ["Production", "An isolated, monitored lab", "Your inbox",
                          "A browser tab"], "An isolated, monitored lab",
                         "malware-analysis", "Isolation is mandatory.")],
          hints=["Record hashes first; keep it contained."])],
       [short("Record a sample's ___ during triage (integrity id).", "hash",
              "malware-analysis", "Hashes identify samples."),
        mcq("Analysis output supports:", ["Redistribution", "Detection and understanding",
            "Nothing", "Faster disks"], "Detection and understanding", "malware-analysis",
            "Produce detections and understanding.")],
       lab="malware-analysis-lab"),

    _c("network-monitoring", "Network Monitoring", "defensive",
       "Observe network behaviour to spot anomalies.",
       "easy", "defensive", ["networking-fundamentals"],
       [L("Baselines and anomalies", "easy", 15, "network-monitoring",
          "You cannot spot the abnormal without knowing the normal. Monitoring builds a "
          "baseline of expected flows, volumes and destinations; deviations (new "
          "destinations, odd ports, volume spikes) become leads. Flow records and packet "
          "captures are the raw material.",
          exercises=[mcq("Anomaly detection needs a:", ["Faster NIC", "Baseline of normal",
                         "Bigger disk", "New cable"], "Baseline of normal",
                         "network-monitoring", "Baselines define normal.")],
          hints=["Normal first, then deviations."])],
       [short("Compare traffic against a ___ to find anomalies.", "baseline",
              "network-monitoring", "Baselines reveal anomalies."),
        mcq("A sudden spike to a new destination is:", ["Always fine", "A lead to investigate",
            "A patch", "A backup"], "A lead to investigate", "network-monitoring",
            "Investigate deviations.")],
       lab="defensive-monitoring-lab"),
]
