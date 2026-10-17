"""Foundational courses: orientation, Linux, networking, Windows, AD."""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, cmd, exercise, lesson, mcq, short, wstep,
)

COURSES = [
    course(
        "hacklab-orientation", "HackLab Orientation",
        "Learn to use the HackLab platform: starting labs, using terminals, "
        "understanding isolated networks, and working safely.",
        "orientation", "platform", specialization=None,
        objectives=[
            "Navigate the HackLab interface",
            "Start, stop and reset a disposable lab VM",
            "Understand isolated lab networking and safe practice",
        ],
        tags=["orientation", "beginner"],
        competency_prereqs=[],
        lessons=[
            lesson(
                "Welcome to HackLab", "orientation", 10, "platform-orientation",
                """
HackLab is a self-hosted training platform. You progress through **courses**
(instructional content and assessments) and **labs** (disposable virtual
machines you interact with). This orientation explains the moving parts so the
rest of your journey is smooth.

Key ideas:

- **Courses** teach concepts and track your progress and demonstrated
  competencies server-side.
- **Labs** spin up one or more VMs on an isolated virtual network. They are
  *disposable*: resetting a lab returns it to a clean baseline without
  affecting your learning progress.
- **Difficulty levels** run from Orientation (0) to Mastery (7). You are guided
  along a sensible path but may choose to attempt harder material early.

Nothing you do inside a lab touches your host machine or the public internet
unless an administrator has explicitly enabled external connectivity.
""",
                hints=["Your progress is stored on the server, not the browser.",
                       "Labs are isolated by default — experiment freely."],
            ),
            lesson(
                "Starting and resetting a lab", "orientation", 10, "platform-orientation",
                """
From the **Machine Catalogue** or a course's **Lab Workspace**, press *Start*.
HackLab validates the profile, checks host capacity, creates a copy-on-write
disk overlay, defines the VM, attaches it to an isolated network, and starts
it. You will see real progress for each stage. A lab is only marked *ready*
once the hypervisor confirms the VM is actually running.

When you are finished, press *Stop* to free resources, or *Reset* to discard
all changes inside the VM and start again from the clean baseline. Resetting
rebuilds the disposable overlay; your course progress, flags and achievements
are untouched.
""",
                exercises=[
                    exercise("Lifecycle order",
                             "Which happens LAST when starting a lab?",
                             "mcq", "The lab is marked ready after the VM is confirmed running",
                             "platform-orientation",
                             "Readiness is only reported after the hypervisor confirms the running state.",
                             choices=["The overlay disk is created",
                                      "The VM is defined",
                                      "The lab is marked ready after the VM is confirmed running",
                                      "The network is created"]),
                ],
                walkthrough=[
                    wstep("Open the catalogue", "Go to Machine Catalogue and pick a profile marked Ready."),
                    wstep("Press Start", "Watch the staged progress bar."),
                    wstep("Use the terminal", "Open the in-browser terminal once the VM is running."),
                    wstep("Reset when done", "Press Reset to return to a clean baseline."),
                ],
            ),
            lesson(
                "Working safely", "orientation", 10, "security-terminology",
                """
Treat every vulnerable lab VM as potentially hostile: do not paste real
credentials into lab guests, and do not rely on a lab being connected to the
internet. The platform keeps labs isolated for your safety and the host's.

Good habits:

- Take notes as you work — labs are disposable but your notes are not.
- Prefer stopping labs you are not using to conserve CPU and RAM.
- Use the optional hints and walkthroughs when you are stuck; using a hint is
  never penalised, it is simply recorded so recommendations can adapt.
""",
            ),
        ],
        assessment=assessment(
            "Orientation Check", difficulty="orientation", passing_score=60,
            questions=[
                mcq("What does resetting a lab affect?",
                    ["Your course progress", "Only the VM's disk state",
                     "Your achievements", "Other users' labs"],
                    "Only the VM's disk state", "platform-orientation",
                    "Resets rebuild the disposable disk; learner progress is independent."),
                mcq("By default, lab networks are:",
                    ["Bridged to your LAN", "Isolated", "On the public internet", "Shared between users"],
                    "Isolated", "platform-orientation",
                    "Isolated networking is the safe default."),
            ],
        ),
    ),

    course(
        "cybersecurity-fundamentals", "Cybersecurity Fundamentals",
        "Core security concepts: the CIA triad, threats and risk, defence in "
        "depth, and the vocabulary you will use throughout HackLab.",
        "beginner", "fundamentals", specialization=None,
        objectives=["Explain the CIA triad", "Describe threats, vulnerabilities and risk",
                    "Understand defence in depth and least privilege"],
        tags=["fundamentals", "beginner", "theory"],
        prerequisites=["hacklab-orientation"],
        lessons=[
            lesson(
                "The CIA triad", "beginner", 15, "security-terminology",
                """
Security is often framed around three properties:

- **Confidentiality** — information is available only to those authorised to
  see it (e.g. encryption, access control).
- **Integrity** — information is accurate and unaltered except by authorised
  actors (e.g. hashing, digital signatures, change control).
- **Availability** — systems and data are accessible when needed (e.g.
  redundancy, backups, capacity planning).

Most security decisions trade these against each other and against usability.
A good analyst can name which property a control protects and what happens when
it fails.
""",
                exercises=[
                    mcq("A backup primarily protects which property?",
                        ["Confidentiality", "Integrity", "Availability", "Non-repudiation"],
                        "Availability", "security-terminology",
                        "Backups restore access after data loss — an availability control."),
                ],
                hints=["Think about which property fails if the control is absent."],
            ),
            lesson(
                "Threats, vulnerabilities and risk", "beginner", 15, "security-terminology",
                """
Precise language matters:

- A **vulnerability** is a weakness (a missing patch, a weak password policy).
- A **threat** is something that could exploit a vulnerability (a criminal
  group, malware, an insider error).
- **Risk** combines likelihood and impact: *risk = likelihood × impact*.

Security work is risk management, not risk elimination. You cannot fix
everything, so you prioritise: which weaknesses, if exploited, cause the most
harm and are most likely to be targeted?
""",
                exercises=[
                    short("Complete the equation: risk = likelihood × ____",
                          "impact", "security-terminology",
                          "Risk is commonly modelled as likelihood multiplied by impact."),
                ],
            ),
            lesson(
                "Defence in depth and least privilege", "beginner", 15, "security-terminology",
                """
Two foundational principles:

- **Defence in depth**: layer independent controls so that one failure does not
  cause a breach. A firewall, patched software, monitoring and least privilege
  each cover each other's gaps.
- **Least privilege**: give every user, process and service only the access it
  needs, for only as long as it needs it. This limits the blast radius of any
  single compromise or mistake.

You will apply both repeatedly — when hardening a Linux host, segmenting a
network, or designing an application's authorisation model.
""",
            ),
        ],
        assessment=assessment(
            "Fundamentals Assessment", difficulty="beginner",
            questions=[
                mcq("Which principle limits the blast radius of a compromised account?",
                    ["Defence in depth", "Least privilege", "Availability", "Fail-open"],
                    "Least privilege", "security-terminology",
                    "Least privilege restricts what any single account can do."),
                short("What combines likelihood and impact?", "risk",
                      "security-terminology", "Risk = likelihood × impact."),
                mcq("Encryption of data at rest primarily protects:",
                    ["Availability", "Integrity", "Confidentiality", "Redundancy"],
                    "Confidentiality", "security-terminology",
                    "Encryption keeps data readable only to authorised parties."),
            ],
        ),
    ),

    course(
        "linux-fundamentals", "Linux Fundamentals",
        "The Linux shell, filesystem, permissions and processes — the bedrock "
        "skill for almost every security discipline.",
        "beginner", "linux", specialization="linux",
        objectives=["Navigate the filesystem", "Read and reason about permissions",
                    "Inspect processes and services"],
        tags=["linux", "beginner", "cli"],
        prerequisites=["cybersecurity-fundamentals"],
        lab_id="linux-practice-basic",
        lessons=[
            lesson(
                "The shell and filesystem", "beginner", 15, "linux-fundamentals",
                """
The shell is a text interface to the operating system. Core navigation:

```
pwd            # print working directory
ls -la         # list all files, long format
cd /etc        # change directory
cat file       # show a file
less file      # page through a file
find / -name sshd_config 2>/dev/null   # locate a file
```

The Linux filesystem is a single tree rooted at `/`. Important locations
include `/etc` (configuration), `/var/log` (logs), `/home` (user data) and
`/usr/bin` (programs). Knowing where things live is half of enumeration.
""",
                exercises=[
                    cmd("Which command prints the current directory?", "pwd",
                        "linux-fundamentals", "`pwd` prints the working directory."),
                ],
                hints=["`man <command>` shows a command's manual page.",
                       "`2>/dev/null` discards error output from find."],
            ),
            lesson(
                "Permissions", "beginner", 20, "linux-fundamentals",
                """
Every file has an owner, a group, and three permission triads (owner, group,
other), each with read (r=4), write (w=2) and execute (x=1) bits.

```
-rwxr-x--- 1 alice devs 0 Jan 1 file
```

Here the owner `alice` has `rwx` (7), the group `devs` has `r-x` (5), others
have none (0) → mode `750`. `chmod 640 file` sets owner `rw`, group `r`, others
none. Misconfigured permissions (world-writable sensitive files, over-broad
group access) are a classic source of privilege issues, so reading them
accurately is a core skill.
""",
                exercises=[
                    short("What numeric mode is rw-r-----?", "640",
                          "linux-fundamentals", "owner rw=6, group r=4, other 0 → 640.",
                          hints=["r=4, w=2, x=1; sum each triad."]),
                ],
                walkthrough=[
                    wstep("List with permissions", "Run `ls -l` and read the first column."),
                    wstep("Decode the triads", "Split into owner/group/other, convert each to a digit."),
                    wstep("Change a mode", "Use `chmod 640 file` and verify with `ls -l`."),
                ],
            ),
            lesson(
                "Processes and services", "beginner", 15, "linux-fundamentals",
                """
Running programs are processes. Inspect them with:

```
ps aux            # all processes
top               # live view
ss -tlnp          # listening TCP sockets and owning process
systemctl status  # service states (systemd)
```

A listening socket tells you what services are exposed. Correlating a port to a
process to a configuration file under `/etc` is the enumeration loop you will
use constantly.
""",
                exercises=[
                    cmd("Which command lists listening TCP sockets with the owning process?",
                        "ss -tlnp", "linux-enumeration",
                        "`ss -tlnp` shows listening TCP sockets and the owning program."),
                ],
            ),
        ],
        assessment=assessment(
            "Linux Fundamentals Assessment", difficulty="easy",
            questions=[
                short("Numeric mode for rwxr-x--- ?", "750", "linux-fundamentals",
                      "owner rwx=7, group r-x=5, other 0."),
                mcq("Where do most service configuration files live?",
                    ["/home", "/etc", "/var/run", "/proc"], "/etc",
                    "linux-administration", "`/etc` holds system configuration."),
                cmd("Command to page through a file read-only?", "less",
                    "linux-fundamentals", "`less` pages through files."),
            ],
        ),
    ),
]
