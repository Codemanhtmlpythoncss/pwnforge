"""Assessment methodology, enumeration and privilege concepts (authorised only)."""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, lesson, mcq, short,
)


def _c(id, title, desc, difficulty, prereqs, lessons, qs, spec="pentest",
       cprereqs=None, lab=None, cat="methodology"):
    return course(id, title, desc, difficulty, cat, specialization=spec,
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=["methodology"], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


L = lesson
COURSES = [
    _c("vulnerability-assessment", "Vulnerability Assessment",
       "Systematically find, verify and prioritise weaknesses.",
       "intermediate", ["networking-fundamentals", "linux-fundamentals"],
       [L("Finding vs verifying", "intermediate", 15, "vuln-assessment",
          "Scanners surface *potential* issues; an assessor must *verify* them to remove "
          "false positives and understand real impact. A finding is only actionable once "
          "you can reproduce it and explain the conditions under which it occurs. Always "
          "work within an authorised scope.",
          exercises=[mcq("A scanner result is best treated as:",
                         ["A confirmed breach", "A lead to verify", "Noise to ignore",
                          "A patch"], "A lead to verify", "vuln-assessment",
                         "Verify before reporting.")],
          hints=["Reproduce a finding before you report it."]),
        L("Prioritising by risk", "intermediate", 15, "vuln-assessment",
          "Rank findings by likelihood and impact, considering exposure and existing "
          "controls. A medium bug on an internet-facing service may outrank a high bug "
          "that requires local access. Prioritisation is what makes a report useful to "
          "the people who must fix things.",
          exercises=[short("Rank findings by impact and ___.", "likelihood",
                           "vuln-assessment", "Likelihood and impact drive ranking.")])],
       [mcq("The assessor's job after a scan is to:",
            ["Trust results", "Verify and prioritise", "Delete logs", "Reboot"],
            "Verify and prioritise", "vuln-assessment", "Verify then prioritise."),
        short("Context that can raise a finding's priority: internet-___.", "facing",
              "vuln-assessment", "Exposure matters.")]),

    _c("penetration-testing-methodology", "Penetration-Testing Methodology",
       "The structured, authorised phases of a professional engagement.",
       "intermediate", ["vulnerability-assessment"],
       [L("Scope, rules of engagement, authorisation", "intermediate", 15, "pentest-methodology",
          "Every legitimate test begins with written authorisation and a defined scope: "
          "which systems, which techniques, which time windows, and who to contact. "
          "Working outside scope is both unethical and unlawful. Pwnforge exists to "
          "practise these skills safely inside isolated, owned environments.",
          exercises=[mcq("What must precede any testing?",
                         ["A scanner", "Written authorisation and scope", "A VPN",
                          "A report"], "Written authorisation and scope",
                         "pentest-methodology", "Authorisation and scope come first.")],
          hints=["No authorisation, no testing."]),
        L("The phased approach", "intermediate", 15, "pentest-methodology",
          "A typical methodology: reconnaissance → enumeration → vulnerability analysis → "
          "controlled verification → post-activity analysis → reporting. Each phase feeds "
          "the next and everything is documented for the final report and for "
          "reproducibility.",
          exercises=[short("Final phase of an engagement?", "reporting",
                           "security-reporting", "Reporting concludes the work.")])],
       [mcq("Testing outside the agreed scope is:",
            ["Fine if quick", "Unethical and often unlawful", "Encouraged", "Required"],
            "Unethical and often unlawful", "pentest-methodology", "Stay in scope."),
        short("First technical phase after authorisation?", "reconnaissance",
              "reconnaissance", "Recon starts the technical work.")]),

    _c("reconnaissance", "Reconnaissance in Authorised Environments",
       "Gather information about in-scope systems methodically.",
       "easy", ["networking-fundamentals"],
       [L("Passive vs active", "easy", 15, "reconnaissance",
          "Passive recon uses information already available without touching the target "
          "(public records, documentation). Active recon interacts with in-scope systems "
          "(resolving names, checking which services respond). Record everything you "
          "learn; reconnaissance must stay within the written scope.",
          exercises=[mcq("Interacting directly with an in-scope host is:",
                         ["Passive recon", "Active recon", "Reporting", "Scoping"],
                         "Active recon", "reconnaissance", "Direct interaction is active.")],
          hints=["Passive = no interaction; active = interaction with in-scope assets."]),
        L("Building an asset inventory", "easy", 10, "reconnaissance",
          "Reconnaissance should produce an **asset inventory**: a structured record "
          "of the in-scope systems you discovered and the evidence about each one. "
          "For each asset, record its hostname or IP address, role if known, exposed "
          "ports and services, where and when you observed the information, and your "
          "confidence in it. For example: `web-01 | 10.10.10.20 | HTTPS on 443 | "
          "DNS lookup | observed today | high confidence`. This inventory is the map "
          "for later enumeration and prioritisation; it is not a claim that every "
          "listed system is vulnerable. Do not add systems outside the authorised scope.",
          exercises=[mcq("Which is a useful asset-inventory entry?",
                         ["An in-scope host's IP, observed services and evidence source",
                          "A guessed password for an unknown user",
                          "A system discovered outside the agreed scope",
                          "A vulnerability assumed without checking"],
                         "An in-scope host's IP, observed services and evidence source",
                         "reconnaissance",
                         "Record scoped systems and observed facts, with their evidence.")],
          hints=["Record observed facts about each in-scope system, not guesses."])],
       [mcq("Reading public documentation about a target is:",
            ["Active recon", "Passive recon", "Exploitation", "Reporting"],
            "Passive recon", "reconnaissance", "No interaction = passive."),
        short("The structured list of in-scope systems and their observed services is an asset ___.",
              "inventory", "reconnaissance",
              "Recon records scoped assets and verified details in an asset inventory.",
              hints=["It is the organised record you use as a map for later enumeration."]) ]),

    _c("service-enumeration", "Service Enumeration",
       "Identify and fingerprint the services a host exposes.",
       "easy", ["reconnaissance", "networking-fundamentals"],
       [L("From open port to service", "easy", 15, "service-enumeration",
          "Enumeration turns 'port 8080 is open' into 'an HTTP server of version X with "
          "these endpoints'. Banner text, response headers and default pages all help "
          "fingerprint a service. The more precisely you identify a service, the more "
          "precisely you can assess and remediate it.",
          exercises=[mcq("Enumeration aims to:",
                         ["Crash services", "Precisely identify services and versions",
                          "Encrypt traffic", "Reset passwords"],
                         "Precisely identify services and versions",
                         "service-enumeration", "Identify services precisely.")],
          hints=["Headers and banners reveal software and versions."]),
        L("Mapping the attack surface", "easy", 15, "service-enumeration",
          "Compile services into an attack-surface map: for each, note version, exposure "
          "and known weaknesses to check. This map drives the vulnerability-analysis "
          "phase and, defensively, tells you what to patch or disable.",
          exercises=[short("Disabling an unused service reduces the attack ___.", "surface",
                           "infrastructure-hardening", "Fewer services = smaller surface.")])],
       [mcq("A response header can reveal:", ["Nothing", "Software and version",
            "The CPU temperature", "Disk size"], "Software and version",
            "service-enumeration", "Headers often leak versions."),
        short("Goal: build an attack-___ map.", "surface", "service-enumeration",
              "Attack-surface map.")],
       lab="network-basics-lab"),

    _c("linux-privilege-escalation-concepts", "Linux Privilege-Escalation Concepts",
       "Understand how Linux privilege boundaries are weakened and hardened.",
       "hard", ["linux-administration", "service-enumeration"],
       [L("Where boundaries break", "hard", 20, "linux-privesc",
          "Privilege escalation exploits a misconfiguration that lets a low-privilege "
          "user gain more rights: over-permissive sudo rules, SUID binaries used unsafely, "
          "writable paths used by root services, and exposed credentials. The defensive "
          "goal is to enumerate these conditions and remove them — least privilege, "
          "minimal SUID, careful sudoers.",
          exercises=[mcq("Which is a common Linux privesc condition?",
                         ["Read-only /etc", "Over-permissive sudo rules",
                          "Disabled services", "A firewall"],
                         "Over-permissive sudo rules", "linux-privesc",
                         "Broad sudo rules are a classic path.")],
          hints=["Enumerate sudo, SUID and writable root-run paths."]),
        L("Hardening against it", "hard", 20, "infrastructure-hardening",
          "Remediation: audit `sudo -l` capability, review SUID/SGID binaries, ensure "
          "service files and their directories are not writable by non-root, rotate and "
          "protect credentials, and keep the kernel/packages patched. Verify each fix.",
          exercises=[short("Principle to apply to limit privesc: least ___.", "privilege",
                           "linux-privesc", "Least privilege limits escalation.")])],
       [mcq("SUID binaries are risky when they:", ["Are small",
            "Can be abused to run as owner (often root)", "Use colour", "Log a lot"],
            "Can be abused to run as owner (often root)", "linux-privesc",
            "Unsafe SUID use runs as the file owner."),
        short("Core principle against privesc?", "least privilege", "linux-privesc",
              "Least privilege.")],
       cprereqs=["linux-administration"], lab="linux-admin-lab"),

    _c("windows-privilege-escalation-concepts", "Windows Privilege-Escalation Concepts",
       "Understand Windows privilege weaknesses and their remediation.",
       "hard", ["windows-administration", "service-enumeration"],
       [L("Common Windows weaknesses", "hard", 20, "windows-privesc",
          "Windows privilege issues include unquoted service paths, weak service "
          "permissions, misused privileges (e.g. SeImpersonate), and credentials left in "
          "configuration or memory. Enumerating these and fixing the configuration "
          "(quoting paths, tightening ACLs, removing stored secrets) closes the gaps.",
          exercises=[mcq("Unquoted service path risk lets Windows:",
                         ["Run faster", "Execute an unintended binary",
                          "Save RAM", "Rotate logs"], "Execute an unintended binary",
                         "windows-privesc", "A space in an unquoted path can be hijacked.")],
          hints=["Check service ACLs and path quoting."])],
       [mcq("A fix for unquoted service paths:", ["Delete the service",
            "Quote the binary path", "Disable logging", "Add RAM"], "Quote the binary path",
            "windows-privesc", "Quoting the path removes the ambiguity."),
        short("Tighten service permissions via ___ (3-letter).", "ACL",
              "windows-privesc", "Access control lists.")],
       cprereqs=["windows-administration"]),

    _c("password-security-auditing", "Password Security and Auditing",
       "Hashing, policy and authorised password auditing.",
       "intermediate", ["cybersecurity-fundamentals"],
       [L("How passwords should be stored", "intermediate", 15, "password-security",
          "Systems must store passwords as salted, slow hashes (bcrypt/scrypt/Argon2). "
          "Auditing (in authorised settings) measures resistance to guessing and finds "
          "reused or weak credentials so they can be replaced. Strong policy favours "
          "length and uniqueness over arbitrary complexity rules.",
          exercises=[mcq("Best stored-password property for defence:",
                         ["Fast hashing", "Salted slow hashing", "Plaintext for recovery",
                          "Base64"], "Salted slow hashing", "password-security",
                         "Salt + slow KDF resists cracking.")],
          hints=["Length and uniqueness beat forced symbol rules."])],
       [mcq("Salting primarily defeats:", ["Network sniffing", "Precomputed tables",
            "Phishing", "CSRF"], "Precomputed tables", "password-security",
            "Salts defeat rainbow tables."),
        short("Modern password KDF used by Pwnforge?", "argon2", "password-security",
              "Argon2id.")]),
]
