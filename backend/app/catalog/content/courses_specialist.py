"""Cloud/container, secure development, defence operations and specialisations."""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, lesson, mcq, short,
)


def _c(id, title, cat, subcat, spec, desc, prereqs, lessons, qs,
       cprereqs=None, lab=None):
    # The first lesson's difficulty sets the course difficulty.
    difficulty = lessons[0]["difficulty"]
    return course(id, title, desc, difficulty, cat, specialization=spec,
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=[cat, subcat], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


L = lesson
COURSES = [
    _c("docker-security", "Docker Security", "container", "container", "cloud",
       "Container isolation, image hygiene and runtime safety.",
       ["linux-administration"],
       [L("How containers isolate", "intermediate", 20, "docker-security",
          "Containers share the host kernel and isolate processes with namespaces and "
          "cgroups. They are not VMs: a container escape reaches the host. Security basics: "
          "run as non-root, drop capabilities, use read-only filesystems where possible, "
          "and never mount the Docker socket into untrusted containers.",
          exercises=[mcq("Containers isolate using:",
                         ["A separate kernel", "Namespaces and cgroups", "A hypervisor",
                          "TLS"], "Namespaces and cgroups", "docker-security",
                         "Namespaces + cgroups, shared kernel.")],
          hints=["Container != VM; kernel is shared."]),
        L("Image hygiene", "intermediate", 15, "docker-security",
          "Minimal base images reduce attack surface; pin versions; scan for known "
          "vulnerable packages; never bake secrets into layers (they persist in history). "
          "A clean, minimal, scanned image is the baseline of container security.",
          exercises=[short("Secrets baked into image layers persist in the ___.", "history",
                           "docker-security", "Layer history keeps them.")])],
       [mcq("Mounting the Docker socket into an untrusted container is:",
            ["Safe", "Effectively host-level access", "Required", "Faster"],
            "Effectively host-level access", "docker-security",
            "The socket grants host control."),
        short("Run containers as ___ (not root).", "non-root", "docker-security",
              "Least privilege.")],
       lab="container-security-lab"),

    _c("kubernetes-security", "Kubernetes Security", "container", "cloud", "cloud",
       "Cluster architecture, RBAC and network policies.",
       ["docker-security"],
       [L("Cluster and RBAC", "hard", 20, "kubernetes-security",
          "Kubernetes schedules containers across nodes. The API server is the control "
          "plane's gateway; RBAC governs who can do what. Over-broad roles (cluster-admin "
          "everywhere) are a top risk. Grant least-privilege roles scoped to namespaces.",
          exercises=[mcq("K8s authorisation is governed by:",
                         ["DNS", "RBAC", "TLS only", "cgroups"], "RBAC",
                         "kubernetes-security", "RBAC controls actions.")],
          hints=["Scope roles to namespaces; avoid cluster-admin."]),
        L("Network policies", "hard", 15, "network-policies",
          "By default pods can talk freely. NetworkPolicies implement micro-segmentation, "
          "allowing only required flows between workloads — the Kubernetes expression of "
          "least privilege and network segmentation.",
          exercises=[short("K8s object for pod-to-pod micro-segmentation: Network___.",
                           "Policy", "network-policies", "NetworkPolicy.")])],
       [mcq("Over-broad K8s roles are a risk because:", ["They slow pods",
            "They grant excessive control", "They use RAM", "They break DNS"],
            "They grant excessive control", "kubernetes-security", "Least privilege applies."),
        short("Default pod networking is ___ (open/closed)?", "open",
              "network-policies", "Open until policies restrict it.")],
       lab="container-security-lab"),

    _c("cloud-security-fundamentals", "Cloud Security Fundamentals", "cloud", "cloud",
       "cloud", "Shared responsibility, identity and common misconfigurations.",
       ["cybersecurity-fundamentals"],
       [L("Shared responsibility & IAM", "intermediate", 20, "cloud-fundamentals",
          "In the cloud, the provider secures the infrastructure and you secure your "
          "configuration, identities and data. Most cloud incidents stem from "
          "misconfiguration — public storage, over-privileged roles, exposed keys. IAM "
          "least privilege and secure defaults prevent the majority.",
          exercises=[mcq("Most cloud incidents stem from:",
                         ["Provider outages", "Customer misconfiguration",
                          "Slow networks", "Old CPUs"], "Customer misconfiguration",
                         "cloud-fundamentals", "Config errors dominate.")],
          hints=["You own identity, config and data."])],
       [short("Cloud security splits duties under the ___ responsibility model.", "shared",
              "cloud-fundamentals", "Shared responsibility."),
        mcq("A frequent cloud mistake:", ["Public storage buckets", "Too much logging",
            "Strong IAM", "Encryption"], "Public storage buckets", "cloud-fundamentals",
            "Public data stores leak often.")]),

    _c("iac-security", "Infrastructure-as-Code Security", "cloud", "cloud", "cloud",
       "Securing declarative infrastructure and pipelines.",
       ["cloud-security-fundamentals"],
       [L("Shift security left", "hard", 20, "iac-security",
          "IaC (Terraform, manifests) makes infrastructure reviewable and testable. "
          "Scan templates for insecure defaults before deployment, keep secrets out of "
          "code, and require review for changes. Catching misconfig in code is cheaper "
          "and safer than in production.",
          exercises=[mcq("IaC security scanning happens best:",
                         ["After an incident", "Before deployment (in the pipeline)",
                          "Never", "Only yearly"], "Before deployment (in the pipeline)",
                         "iac-security", "Shift left into the pipeline.")],
          hints=["Review and scan templates pre-deploy."])],
       [short("Keep secrets ___ of IaC code.", "out", "iac-security",
              "Never commit secrets."),
        mcq("IaC makes infrastructure:", ["Opaque", "Reviewable and testable",
            "Slower", "Random"], "Reviewable and testable", "iac-security",
            "Declarative infra is reviewable.")]),

    _c("secure-coding", "Secure Coding", "secure-dev", "secure-dev", "secdev",
       "Write code resilient to the common vulnerability classes.",
       ["python-for-security"],
       [L("Validate, encode, parameterise", "intermediate", 20, "secure-coding",
          "Three habits prevent most injection and memory issues: validate input against "
          "an allowlist, encode output for its exact context, and use parameterised APIs "
          "instead of string-built commands/queries. Fail closed, handle errors without "
          "leaking internals, and keep secrets out of code and logs.",
          exercises=[mcq("Preferred way to build a DB query with user data:",
                         ["Concatenate strings", "Parameterised query", "eval", "format()"],
                         "Parameterised query", "secure-coding",
                         "Parameterisation separates data from code.")],
          hints=["Allowlist input, encode output, parameterise calls."])],
       [short("Handle errors without leaking ___.", "internals", "secure-coding",
              "Avoid leaking stack traces/internals."),
        mcq("Fail ___ (open/closed) is safer.", ["open", "closed", "silent", "fast"],
            "closed", "secure-coding", "Fail closed denies by default.")]),

    _c("secure-development-lifecycle", "Secure Development", "secure-dev", "secure-dev",
       "secdev", "Build security into every phase of the SDLC.",
       ["secure-coding"],
       [L("Security across the SDLC", "hard", 20, "secure-sdlc",
          "Security is cheapest early: threat model during design, use safe defaults in "
          "implementation, add security tests, scan dependencies, and review before "
          "release. A vulnerability caught in design costs a fraction of one found in "
          "production.",
          exercises=[mcq("Threat modelling belongs in:",
                         ["Design", "Only after release", "Never", "Marketing"], "Design",
                         "secure-sdlc", "Model threats during design.")],
          hints=["Earlier is cheaper and safer."])],
       [short("Scan third-party ___ for known vulns.", "dependencies", "secure-sdlc",
              "Dependency scanning."),
        mcq("Cheapest phase to fix security:", ["Production", "Design", "Hotfix",
            "Never"], "Design", "secure-sdlc", "Design-time fixes are cheapest.")]),

    _c("firewall-configuration", "Firewall Configuration", "infrastructure",
       "infrastructure", "defensive", "Design and apply packet-filtering rules.",
       ["networking-fundamentals"],
       [L("Default deny", "easy", 15, "firewalls",
          "A sound firewall policy denies everything by default and explicitly allows "
          "only required flows. Rules are ordered and specific; log denied traffic for "
          "visibility. This is least privilege applied to the network edge and between "
          "zones.",
          exercises=[mcq("Best default firewall stance:", ["Allow all", "Default deny",
                         "Random", "Log only"], "Default deny", "firewalls",
                         "Deny by default, allow by exception.")],
          hints=["Allow by exception only."])],
       [short("Firewalls should default to ___.", "deny", "firewalls",
              "Default deny."),
        mcq("Logging denied traffic provides:", ["Nothing", "Visibility", "Speed",
            "Storage"], "Visibility", "firewalls", "Denied-traffic logs aid detection.")]),

    _c("network-segmentation", "Network Segmentation", "infrastructure",
       "infrastructure", "defensive", "Divide networks into isolated zones.",
       ["firewall-configuration"],
       [L("Zones and blast radius", "intermediate", 15, "network-segmentation",
          "Segmentation splits a network into zones (e.g. user, server, management) with "
          "controlled flows between them, so a compromise in one zone does not reach all "
          "others. HackLab's isolated lab networks are a microcosm of this principle.",
          exercises=[mcq("Segmentation primarily limits:",
                         ["Bandwidth", "Blast radius of a compromise", "Latency",
                          "Cost"], "Blast radius of a compromise", "network-segmentation",
                         "Zones contain compromise.")],
          hints=["Contain, don't flatten."])],
       [short("Segmentation reduces the ___ radius.", "blast", "network-segmentation",
              "Blast radius."),
        mcq("Management interfaces should be:", ["On the user VLAN", "In an isolated zone",
            "Public", "Unprotected"], "In an isolated zone", "network-segmentation",
            "Isolate management.")]),

    _c("vulnerability-remediation", "Vulnerability Remediation", "methodology",
       "pentest", "methodology", "Fix verified weaknesses and prove the fix.",
       ["vulnerability-assessment"],
       [L("Remediate and verify", "intermediate", 15, "vuln-remediation",
          "Remediation is not complete until verified. For each finding: apply the fix, "
          "re-test the exact condition, and record before/after evidence. Track residual "
          "risk where a full fix is not yet possible, with compensating controls.",
          exercises=[mcq("A remediation is complete when:",
                         ["Code is changed", "The fix is re-tested and verified",
                          "A ticket is closed", "Time passes"],
                         "The fix is re-tested and verified", "vuln-remediation",
                         "Verify the fix.")],
          hints=["Re-test the exact condition."])],
       [short("Where a full fix isn't possible, apply ___ controls.", "compensating",
              "vuln-remediation", "Compensating controls."),
        mcq("Proof a fix works:", ["A promise", "Before/after re-test evidence",
            "A reboot", "A meeting"], "Before/after re-test evidence", "vuln-remediation",
            "Evidence, not assertion.")]),

    _c("security-reporting", "Security Reporting and Professional Practice",
       "methodology", "pentest", "methodology",
       "Communicate findings clearly, ethically and actionably.",
       ["vulnerability-assessment"],
       [L("Writing a useful report", "intermediate", 20, "security-reporting",
          "A report serves the reader who must act. Each finding needs: a clear title, "
          "risk rating (impact × likelihood), affected assets, reproduction steps, "
          "evidence, and specific remediation. Lead with an executive summary; keep "
          "technical detail precise and reproducible. Ethics and scope discipline underpin "
          "the profession.",
          exercises=[mcq("A finding's rating combines impact and:",
                         ["Length", "Likelihood", "Font", "Author"], "Likelihood",
                         "security-reporting", "Impact × likelihood.")],
          hints=["Write for the person who must fix it."])],
       [short("Reports open with an executive ___.", "summary", "security-reporting",
              "Executive summary."),
        mcq("Each finding must include:", ["Only a title", "Reproduction + remediation",
            "A screenshot only", "Nothing"], "Reproduction + remediation",
            "security-reporting", "Reproducible and actionable.")]),

    _c("identity-access-management", "Identity and Access Management", "identity",
       "active-directory", "identity", "Managing identities, roles and entitlements.",
       ["access-control-course"],
       [L("Lifecycle and least privilege", "intermediate", 20, "identity-security",
          "IAM governs the identity lifecycle: provisioning, authentication, "
          "authorisation, and deprovisioning. Stale accounts and privilege creep are "
          "major risks. Regular access reviews and role-based entitlements keep access "
          "aligned with need.",
          exercises=[mcq("Privilege creep is countered by:",
                         ["Ignoring it", "Regular access reviews", "More admins",
                          "Longer passwords"], "Regular access reviews", "identity-security",
                         "Review access periodically.")],
          hints=["Deprovision promptly; review regularly."])],
       [short("Remove access promptly on ___ (leaving).", "deprovisioning",
              "identity-security", "Deprovision leavers."),
        mcq("Entitlements should map to:", ["Seniority", "Role/need", "Tenure",
            "Location"], "Role/need", "identity-security", "Role-based, need-based access.")]),

    _c("infrastructure-hardening", "Infrastructure Hardening", "defensive",
       "defensive", "defensive", "Systematically reduce attack surface.",
       ["linux-administration", "windows-administration"],
       [L("Minimise, patch, configure", "hard", 20, "infrastructure-hardening",
          "Hardening removes what is not needed (services, accounts, software), keeps the "
          "rest patched, and configures secure defaults (authentication, logging, "
          "permissions). Benchmarks (e.g. CIS) provide checklists. Verify with "
          "configuration review and re-scanning.",
          exercises=[mcq("First hardening move:", ["Add software",
                         "Remove unneeded services/accounts", "Open ports", "Disable logs"],
                         "Remove unneeded services/accounts", "infrastructure-hardening",
                         "Reduce surface first.")],
          hints=["Less software, fewer accounts, patched, logged."])],
       [short("Hardening checklists are often based on ___ benchmarks (acronym).", "CIS",
              "infrastructure-hardening", "CIS Benchmarks."),
        mcq("Hardening reduces the attack ___.", ["surface", "speed", "cost", "colour"],
            "surface", "infrastructure-hardening", "Smaller surface, less risk.")]),

    _c("threat-intelligence", "Threat Intelligence", "defensive", "defensive",
       "defensive", "Use intelligence to prioritise defence.",
       ["detection-engineering"],
       [L("From data to decisions", "hard", 15, "threat-intelligence",
          "Threat intelligence turns raw indicators and reports into decisions: which "
          "threats are relevant to you, what behaviours to detect, and where to invest. "
          "Prioritise by relevance to your environment; map adversary techniques to your "
          "detections and gaps.",
          exercises=[mcq("Good intel is prioritised by:",
                         ["Volume", "Relevance to your environment", "Age", "Source count"],
                         "Relevance to your environment", "threat-intelligence",
                         "Relevance drives value.")],
          hints=["Relevance over volume."])],
       [short("Map intel techniques to your detection ___.", "gaps",
              "threat-intelligence", "Find coverage gaps."),
        mcq("Intelligence should drive:", ["Random changes", "Prioritised defence",
            "Nothing", "More noise"], "Prioritised defence", "threat-intelligence",
            "Intel informs priorities.")]),

    _c("wireless-security", "Wireless Security", "networking", "infrastructure",
       "networking", "Wi-Fi security concepts and defences.",
       ["networking-fundamentals"],
       [L("Wi-Fi protection", "intermediate", 15, "wireless-security",
          "Wireless security depends on strong protocols (WPA3/WPA2-Enterprise), strong "
          "keys, and segmentation of guest/IoT networks. Weak or legacy encryption and "
          "default credentials are the recurring issues. Treat wireless as an untrusted "
          "edge and segment accordingly.",
          exercises=[mcq("Strongest current Wi-Fi protocol here:",
                         ["WEP", "WPA", "WPA2", "WPA3"], "WPA3", "wireless-security",
                         "WPA3 is the current standard.")],
          hints=["Segment guest/IoT; avoid legacy encryption."])],
       [short("Legacy Wi-Fi encryption to avoid (3 letters)?", "WEP", "wireless-security",
              "WEP is broken."),
        mcq("Guest Wi-Fi should be:", ["Flat with corp", "Segmented", "Open",
            "Unlogged"], "Segmented", "network-segmentation", "Segment guest networks.")]),

    _c("security-architecture", "Security Architecture", "secure-dev", "secure-dev",
       "secdev", "Design systems that are secure by construction.",
       ["secure-development-lifecycle", "network-segmentation"],
       [L("Principles of secure design", "advanced", 20, "security-architecture",
          "Secure architecture applies least privilege, defence in depth, secure defaults, "
          "fail-closed behaviour, and clear trust boundaries. Design decisions — where to "
          "place controls, how to segment, how components authenticate — determine how "
          "resilient a system is before a single line of code is reviewed.",
          exercises=[mcq("Secure-by-default means:", ["Features off safely by default",
                         "Everything open", "No logging", "No auth"],
                         "Features off safely by default", "security-architecture",
                         "Safe defaults out of the box.")],
          hints=["Draw the trust boundaries explicitly."])],
       [short("Architecture should define clear trust ___.", "boundaries",
              "security-architecture", "Trust boundaries."),
        mcq("Resilience is decided largely at:", ["Runtime only", "Design time",
            "Marketing", "Never"], "Design time", "security-architecture",
            "Architecture decides resilience early.")]),
]
