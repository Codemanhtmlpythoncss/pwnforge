"""Multi-machine lab definitions. Machine profile_ids reference generated profiles."""
from __future__ import annotations


def _lab(id, title, description, difficulty, category, machines, networks,
         startup_order, course=None, minutes=90, objectives=None, tags=None,
         hints=None, guide=""):
    return dict(id=id, title=title, description=description, difficulty=difficulty,
                category=category, machines=machines, networks=networks,
                startup_order=startup_order, readiness_checks=[], course_id=course,
                estimated_minutes=minutes, reset_behavior="disposable",
                objectives=objectives or [], tags=tags or [],
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
