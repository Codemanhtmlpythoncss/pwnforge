"""Applied learning modules shared by courses that appear in learning paths.

The original catalogue gives many courses only one or two short lessons. These
extensions add a taught workflow and an evidence/verification module to each
path course, with examples selected by subject area and that course's authored
objectives.
"""
from __future__ import annotations

from backend.app.catalog.content._authoring import lesson, mcq, short
from backend.app.catalog.content.paths import LEARNING_PATHS


_TRACKS = {
    "platform": (
        "Operate the lab safely",
        "Keep useful notes and finish cleanly",
        "A productive lab session starts with the objective and the assigned target. Confirm the lab is disposable and isolated, keep real credentials out of the guest, and use the workspace terminal or connection details shown for that instance. Change one thing at a time so you can tell which action produced a result. Stop the instance when you are finished; the saved course record and the guest's temporary disk are separate.",
        "Write down the target, commands, observations, and the meaning of each result while you work. Record exact errors instead of paraphrasing them. Before you finish, verify that the task is complete, submit any requested answer or flag, and stop the lab. If a result is surprising, reset the disposable instance and repeat the smallest relevant step. A repeatable process is more useful than a lucky result.",
        "What should you do with a lab instance when you are finished using it?",
        ["Leave every machine running", "Stop it to release resources", "Delete your course progress", "Share its network with other users"],
        "Stop it to release resources",
        "Stopping the lab frees host resources while course progress remains stored separately.",
    ),
    "fundamentals": (
        "Turn security language into a risk statement",
        "Choose a control and verify its effect",
        "Describe a security problem by naming the asset, the threat or failure, the weakness that makes it possible, and the likely impact. Risk is not just a vulnerability name: likelihood and impact depend on exposure, existing controls, and the value of the asset. Keep facts separate from assumptions and state what evidence would change your estimate.",
        "Choose a control that addresses the cause of the risk, not only its visible symptom. Define how you will verify the control before changing anything, then repeat the same check after the change. Record remaining risk and any trade-offs. A control is not proven effective merely because it was configured; demonstrate that the expected unsafe behaviour is prevented and that normal use still works.",
        "Which pair is the basic basis for prioritising a risk?",
        ["Likelihood and impact", "Hostname and port", "Age and file size", "Username and shell"],
        "Likelihood and impact",
        "Risk prioritisation considers how likely an event is and how much harm it could cause.",
    ),
    "linux": (
        "Build a Linux host inventory",
        "Trace permissions and service exposure",
        "Work from identity to processes to network exposure. Use `id` and `groups` to understand the current account, `ps` to inspect running processes, `systemctl --type=service --state=running` (or `rc-service -l` on Alpine) to inspect services, and `ss -lntup` to map listening sockets to processes. Check important files with `stat` or `ls -l`; inspect sudo rules only with authorisation. Save the command and the relevant output as evidence.",
        "For each finding, state the observed owner, group, mode, process, service, or socket before recommending a change. Compare the access that is configured with the access the service needs. Apply one least-privilege correction at a time, then repeat the exact observation that exposed the issue. Check the service still works, read its journal for errors, and note any remaining access that is intentional.",
        "Which command is the modern default for listing listening sockets?",
        ["ss", "chmod", "grep", "whoami"],
        "ss",
        "`ss` reports socket state and can include listening ports and process information.",
    ),
    "networking": (
        "Map interfaces, routes, and services",
        "Diagnose reachability in layers",
        "Start with local facts: `ip addr` shows interfaces and addresses, `ip route` shows where traffic goes, and `ss -lntup` shows local listeners. For an authorised remote target, scan only the agreed range and use service detection to identify what answers. Record address, port, transport, service name, and evidence separately; an open port is evidence of a listener, not proof of a vulnerability.",
        "When a connection fails, check the path in order: address and subnet, local route and gateway, name resolution if a hostname is involved, filtering policy, and finally whether the service is listening. ICMP failure alone does not prove a host is down. Compare a permitted test with a deliberately blocked path so the expected segmentation policy is clear.",
        "Which command shows the host's routing table on Linux?",
        ["ip route", "ip addr", "ss -lntup", "cat /etc/passwd"],
        "ip route",
        "`ip route` displays the local routing table and default gateway.",
    ),
    "scripting": (
        "Make security scripts predictable",
        "Validate input and handle failures",
        "A useful automation script has a narrow input, a clear output, and safe defaults. Quote variable expansions, validate file paths and target ranges, and keep secrets out of command-line arguments and logs. In Bash, use explicit exit checks and distinguish standard output from errors. In Python, parse structured data with a parser rather than regular expressions when a format has a real grammar.",
        "Test a script with a normal input, an empty input, malformed data, and a permission or network failure. Confirm that a failure returns a non-zero status and does not leave partial output that looks successful. Make repeated runs safe: use temporary files, atomic replacement where appropriate, and document destructive options before enabling them.",
        "Why should shell variable expansions generally be quoted?",
        ["To prevent word splitting and glob expansion", "To make scripts run as root", "To disable exit codes", "To encrypt the variable"],
        "To prevent word splitting and glob expansion",
        "Quoting keeps spaces and wildcard characters inside the intended argument.",
    ),
    "windows": (
        "Inventory Windows services and identities",
        "Verify policy and event evidence",
        "Use `Get-Service` to inventory service state, `Get-NetTCPConnection` or `netstat -ano` to map listeners, and `Get-LocalGroupMember` to review local group membership. Record the service, account, startup mode, port, and process identifier together. In a domain environment, distinguish local configuration from centrally applied policy; a local change may be overwritten by Group Policy.",
        "Before changing a service or permission, record its current value and the expected business function. Apply the smallest policy change, then verify both the setting and the service's behaviour. Use the relevant Windows event channel to confirm the change or investigate a failure. Preserve event time, host, account, and event identifier so another analyst can reproduce your conclusion.",
        "Which PowerShell command inventories Windows services?",
        ["Get-Service", "Get-ProcessRoute", "Get-FileHash", "Get-DnsClient"],
        "Get-Service",
        "`Get-Service` reports installed service names and their current states.",
    ),
    "identity": (
        "Trace an identity's effective access",
        "Reduce standing privilege",
        "For an account, trace authentication, group membership, assigned roles, and the resources those roles can reach. Effective access is the combined result of direct grants, inherited group permissions, and policy. Check both the intended path and unintended paths; a user may inherit access from a nested group or stale assignment.",
        "Remove permissions only after identifying the owner and required workflow. Prefer a narrow role over a broad administrator grant, use separate privileged accounts, and define how elevated access is approved and reviewed. Verify the new effective access with a representative allowed action and a representative denied action. Record the account, role, resource, and evidence for each result.",
        "Which principle limits accounts to only the access they need?",
        ["Least privilege", "Open access", "Security by obscurity", "Shared administration"],
        "Least privilege",
        "Least privilege limits standing permissions to the minimum required for the role.",
    ),
    "web-security": (
        "Trace a browser request through the application",
        "Verify fixes at the right context",
        "Follow an input from the request into application logic, storage, and the response. Identify the trust boundary at each step. Authentication answers who the user is; authorization decides what that user may do. For output, note whether data enters HTML text, an attribute, JavaScript, or a URL, because each context needs the correct encoding. For database operations, parameterize values rather than joining user text into query strings.",
        "Use a harmless test value in an authorised environment and record the request, response, and affected account. Change one control, then repeat the same request and confirm the unsafe result is gone. Also verify normal input still succeeds and access checks apply to direct API requests, not only hidden or disabled buttons. Document the exact affected route and the evidence supporting the result.",
        "What should be used for values in a database query?",
        ["Parameterized queries", "String concatenation", "A hidden form field", "Client-side validation alone"],
        "Parameterized queries",
        "Parameterized queries keep user-controlled values separate from SQL syntax.",
    ),
    "methodology": (
        "Follow an evidence-led assessment workflow",
        "Prioritise and communicate findings",
        "Begin with written authorisation, scope, exclusions, timing, and stop conditions. Discover only what the scope permits. For each possible issue, keep the raw observation, the affected asset, the method, and the timestamp. Validate impact with the least intrusive safe check that answers the question; do not turn a scanner warning into a confirmed vulnerability without evidence.",
        "A useful finding names the affected asset and condition, explains realistic impact, and gives reproducible evidence. Rate severity using a stated method and explain assumptions. Recommend a fix that addresses the root cause, then define a retest that would demonstrate success. State limitations and out-of-scope observations separately so readers can distinguish confirmed results from leads.",
        "What must be agreed before active testing begins?",
        ["Written authorisation and scope", "A public IP address", "A scanner version", "A vulnerability score"],
        "Written authorisation and scope",
        "Active tests must stay within explicit authorisation, scope, and stop conditions.",
    ),
    "defensive": (
        "Turn an alert into a testable question",
        "Build a timeline and validate a detection",
        "Start from a specific hypothesis: which account or process did what, on which host, and when? Identify the log sources that can answer it, check time zones and clock offsets, and preserve the original event fields. Search a narrow time window first, then widen it only when evidence suggests a longer sequence. A missing event may reflect a logging gap, not proof that an action did not happen.",
        "Correlate independent sources and mark each statement as confirmed, inferred, or unknown. For a detection rule, write the behaviour it is meant to catch, the required fields, and known benign lookalikes. Test it against representative positive and negative events. Record precision limits and the response an analyst should take when it fires.",
        "What time-ordered record helps reconstruct a sequence of events?",
        ["Timeline", "Asset tag", "Firewall zone", "Package manifest"],
        "Timeline",
        "A timeline aligns related observations chronologically across sources.",
    ),
    "forensics": (
        "Preserve evidence before analysis",
        "Correlate artefacts without overstating them",
        "Record who collected the evidence, when, from which system, with which tool and settings. Preserve the original and work from a verified copy. Calculate a cryptographic hash at acquisition and compare it after transfer or analysis. Keep timestamps with their original time zone and distinguish file-system times from the time an event actually occurred.",
        "Build a timeline from multiple artefacts and explain the source of each timestamp. A browser record, log entry, and packet capture may describe the same event from different clocks. Note gaps, collection limits, and alternative explanations. Your conclusion should be reproducible from the evidence and should not claim more than the artefacts support.",
        "What is a hash used for in evidence handling?",
        ["Checking whether evidence changed", "Encrypting a disk image", "Replacing chain of custody", "Proving who created a file"],
        "Checking whether evidence changed",
        "A cryptographic hash can reveal whether the evidence bytes changed; it does not replace custody records.",
    ),
    "reverse": (
        "Triage a binary without executing it",
        "Analyse behaviour in a contained environment",
        "Before analysis, record the sample's source and calculate a hash. Use `file`, metadata tools, strings, and section/import listings to learn what the file appears to be. Treat embedded text as clues, not proof. Inspect control flow and dangerous API use only after the basic file format and architecture are known.",
        "If dynamic analysis is authorised, use a disposable snapshot with network access disabled or explicitly controlled. Observe process, file, registry, and network behaviour, then revert the snapshot. Compare observed behaviour with the static hypothesis and record differences. Never execute an unknown sample on a workstation that holds personal or production data.",
        "What is analysis of a binary without running it called?",
        ["Static analysis", "Dynamic analysis", "Fuzzing", "Packet capture"],
        "Static analysis",
        "Static analysis examines a file without executing it.",
    ),
    "container": (
        "Inspect the container's full trust boundary",
        "Reduce runtime privilege and verify isolation",
        "Review the image source and digest, user identity, capabilities, mounts, secrets, network attachments, and exposed ports. A container shares the host kernel, so a root process, privileged mode, or writable host mount can expand impact beyond the container. Check what the workload actually needs instead of assuming the image's defaults are safe.",
        "Apply one restriction at a time: run as a non-root user, drop unused capabilities, make the filesystem read-only where possible, limit resources, and use narrow network policy. Verify the workload still functions, then inspect the effective runtime configuration rather than relying only on a deployment file. Record the image digest and policy evidence for repeatability.",
        "Which principle should guide container capabilities and privileges?",
        ["Least privilege", "Privileged by default", "Shared root access", "Disable logging"],
        "Least privilege",
        "Containers should receive only the privileges and capabilities the workload requires.",
    ),
    "cloud": (
        "Review identity and configuration as code",
        "Check plans, secrets, and drift",
        "Trace a cloud resource back to the identity and configuration that created it. Review role assignments, public exposure, encryption, logging, and data retention together; each setting affects the others. In infrastructure as code, inspect both the source and the rendered plan because variables and modules can change the final resource.",
        "Keep secrets out of code and state files, pin trusted module and image versions, and require review for broad permissions or public ingress. Compare declared configuration with the live environment to detect drift. After remediation, render the plan again and verify that it changes only the intended resources.",
        "What should be reviewed before applying an infrastructure plan?",
        ["The rendered changes and affected resources", "Only the file name", "Only the last line", "The terminal colour scheme"],
        "The rendered changes and affected resources",
        "A plan should be reviewed for its full resource and permission impact before it is applied.",
    ),
    "infrastructure": (
        "Map the service and management planes",
        "Verify the smallest safe configuration change",
        "Inventory interfaces, routes, listening sockets, service accounts, and management endpoints. Separate user-facing traffic from administration and monitoring. For every open service, record its owner, purpose, expected clients, and whether it is reachable from each network zone. An exposed port alone is not a finding until you understand what listens there and who should reach it.",
        "Write the intended allowed and denied flows before adjusting a firewall or service binding. Apply the narrowest rule, then test both a permitted connection and a blocked connection from the right network locations. Confirm logs show the expected decision and that management access remains available. Capture the before-and-after evidence with the rule identifier.",
        "What does `ss -lntup` help identify?",
        ["Listening sockets and associated processes", "The default route", "Installed packages", "User group membership"],
        "Listening sockets and associated processes",
        "`ss -lntup` displays listening sockets, numeric ports, and owning processes when permitted.",
    ),
    "osint": (
        "Plan a bounded public-source investigation",
        "Corroborate claims and write with confidence",
        "Define the question, subject, timeframe, lawful basis, and collection limits before searching. Prefer primary sources and retain the exact URL, collection time, and relevant excerpt. Keep personal data to the minimum needed. A search result snippet is a lead; open and assess the source before treating it as evidence.",
        "Corroborate important claims with independent sources and check whether they refer to the same person, organisation, or time period. Record confidence and contradictory evidence. Separate fact from inference in the report, explain source limitations, and remove sensitive details that do not support the stated purpose.",
        "Which fields make a public-source observation auditable?",
        ["Source, collection time, and confidence", "Colour, font, and page size", "Search order only", "The analyst's guess"],
        "Source, collection time, and confidence",
        "Provenance, time, and confidence help another analyst assess an OSINT observation.",
    ),
    "tools": (
        "Choose a tool for a specific question",
        "Validate tool output and preserve context",
        "State the question you need answered before choosing a scanner, proxy, packet analyser, or password auditor. Confirm the target and limits, select the smallest useful option set, and save the complete output with tool version and timestamp. Understand what the tool measures and what it cannot see; a result may be incomplete because of filtering, authentication, or protocol behaviour.",
        "Verify important results with a second method or direct observation. For a finding, include the command or request, relevant output, target, and time. Avoid broad or high-rate options when a narrow check answers the question. Keep credentials and tokens out of saved transcripts, and stop if the tool behaves outside the authorised scope.",
        "What should you do with a security tool's important result?",
        ["Validate it with evidence", "Assume it is always correct", "Ignore its scope", "Publish it without review"],
        "Validate it with evidence",
        "Tools are aids to analysis; validate important output and preserve enough context to reproduce it.",
    ),
    "crypto": (
        "Select cryptographic controls by purpose",
        "Validate certificates and key handling",
        "Separate confidentiality, integrity, authentication, and key exchange. Encryption protects confidentiality; a cryptographic hash detects changes; a digital signature supports integrity and origin authentication. Use established libraries and protocols rather than inventing a scheme. For password storage, use a password-hashing function designed to resist guessing rather than a fast general-purpose hash.",
        "For TLS, validate the certificate chain, hostname, validity period, and trust source. Protect private keys with limited permissions and a rotation plan. When a configuration changes, inspect the negotiated protocol and certificate from a client, not just the server's configuration file. Record the exact endpoint and test result.",
        "Which property does a cryptographic hash primarily provide?",
        ["Integrity checking", "Confidentiality", "Routing", "Compression"],
        "Integrity checking",
        "A cryptographic hash can help detect changes but does not encrypt data.",
    ),
}


_CATEGORY_TRACK = {
    "platform": "platform", "fundamentals": "fundamentals", "linux": "linux",
    "networking": "networking", "scripting": "scripting", "windows": "windows",
    "identity": "identity", "web-security": "web-security", "methodology": "methodology",
    "defensive": "defensive", "forensics": "forensics", "reverse": "reverse",
    "container": "container", "cloud": "cloud", "infrastructure": "infrastructure",
    "osint": "osint", "tools": "tools", "crypto": "crypto",
}

_COURSE_TRACK_OVERRIDES = {
    "reconnaissance": "methodology",
    "service-enumeration": "infrastructure",
    "linux-privilege-escalation-concepts": "linux",
    "windows-privilege-escalation-concepts": "windows",
    "security-reporting": "methodology",
    "network-segmentation": "networking",
    "tool-wireshark": "tools",
}


def extend_path_courses(courses: list[dict]) -> None:
    """Add two applied modules to every course used by an authored learning path."""
    path_course_ids = {
        step["course_id"] for path in LEARNING_PATHS for step in path["steps"]
        if step.get("course_id")
    }
    for course in courses:
        if course["id"] not in path_course_ids:
            continue
        track_name = _COURSE_TRACK_OVERRIDES.get(
            course["id"], _CATEGORY_TRACK.get(course["category"], "methodology"))
        track = _TRACKS[track_name]
        competency = (course["lessons"][0].get("competency")
                      or course.get("specialization") or "security-fundamentals")
        objectives = "\n".join(f"- {item}" for item in course["objectives"][:6])
        scenario = (
            f"Use the methods from **{course['title']}** to work this checklist:\n\n"
            f"{objectives}\n\n"
            "For each item, record the target or evidence, the action you took, and the result. "
            "Mark anything not verified as an assumption. Stop if the action would cross the written scope."
        )
        course["lessons"].extend([
            lesson(
                track[0], "intermediate", 20, competency,
                f"{track[2]}\n\n{scenario}",
                exercises=[mcq(track[4], track[5], track[6], competency, track[7])],
                hints=["Use the lesson's commands and record a short evidence note for each observation."]),
            lesson(
                track[1], "intermediate", 20, competency,
                f"{track[3]}\n\n"
                f"## Apply this to {course['title']}\n\n"
                f"{course['description']}\n\n"
                "Before submitting your work, check that your evidence supports each conclusion, that you have "
                "verified the relevant control or behaviour, and that your notes explain limitations. A strong "
                "result is repeatable by another learner using the same target and steps.",
                exercises=[short(
                    "What must be confirmed before performing active work on a target?",
                    "written authorisation and scope", competency,
                    "Confirm written authorisation and scope before active work.",
                    hints=["Check the permission and the exact target range."]),
                ],
                hints=["Repeat the same check after a change so you can compare before and after."]),
        ])
        course["estimated_minutes"] += 40
        course["objectives"] = list(dict.fromkeys(course["objectives"] + [
            "Apply course concepts in a bounded, evidence-led workflow",
            "Verify results and explain limitations clearly",
        ]))
