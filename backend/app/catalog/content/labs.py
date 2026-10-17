"""Multi-machine lab definitions. Machine profile_ids reference generated profiles."""
from __future__ import annotations


def _lab(id, title, description, difficulty, category, machines, networks,
         startup_order, course=None, minutes=90, objectives=None, tags=None):
    return dict(id=id, title=title, description=description, difficulty=difficulty,
                category=category, machines=machines, networks=networks,
                startup_order=startup_order, readiness_checks=[], course_id=course,
                estimated_minutes=minutes, reset_behavior="disposable",
                objectives=objectives or [], tags=tags or [])


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
]
