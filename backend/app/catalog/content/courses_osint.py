"""OSINT (open-source intelligence) courses.

Framed for authorised, ethical use: gathering intelligence from genuinely
public sources, with legality, privacy and investigator OPSEC treated as
first-class topics. Exercises use safe, sandboxed scenarios.
"""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, cmd, course, lesson, mcq, short, wstep,
)


def _c(id, title, desc, difficulty, prereqs, lessons, qs, cprereqs=None, lab=None):
    return course(id, title, desc, difficulty, "osint", specialization="osint",
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=["osint", "recon"], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


L = lesson
COURSES = [
    _c("osint-fundamentals", "OSINT Fundamentals",
       "What open-source intelligence is, where it comes from, and the ethics "
       "and legality that must govern every investigation.",
       "easy", ["cybersecurity-fundamentals"],
       [
           L("What OSINT is (and isn't)", "easy", 15, "osint-fundamentals",
             "Open-source intelligence (OSINT) is intelligence produced from "
             "**publicly available** information: websites, public records, maps, "
             "public social posts, press, and technical sources like DNS and "
             "certificate transparency logs. OSINT does **not** mean accessing "
             "private accounts, bypassing authentication, or social-engineering "
             "people — those are out of scope and often unlawful. Good OSINT is "
             "disciplined collection and analysis of information anyone could "
             "lawfully see.",
             exercises=[mcq("Which is within OSINT scope?",
                            ["Logging into someone's private account",
                             "Reading a public certificate-transparency log",
                             "Guessing a password", "Phishing a target"],
                            "Reading a public certificate-transparency log",
                            "osint-fundamentals",
                            "OSINT uses genuinely public sources only.")],
             hints=["If it requires defeating a control or deceiving a person, it isn't OSINT."]),
           L("The intelligence cycle", "easy", 15, "osint-fundamentals",
             "Professional OSINT follows a cycle: **plan** (define the question and "
             "scope) → **collect** (gather from public sources) → **process** "
             "(organise and de-duplicate) → **analyse** (corroborate, assess "
             "reliability) → **report** (communicate clearly, with sources). "
             "Jumping straight to collection without a question produces noise; "
             "skipping corroboration produces false conclusions.",
             exercises=[short("The cycle step that defines the question and scope is ___.",
                              "plan", "osint-fundamentals", "Planning comes first.")]),
           L("Ethics, legality and privacy", "easy", 15, "osint-ethics",
             "OSINT operates under law and ethics. Respect terms of service, data-"
             "protection law (e.g. GDPR), and the difference between *public* and "
             "*private*. Minimise collection to what the authorised question needs, "
             "avoid harassment, and never repurpose personal data. A lawful source "
             "does not make every use lawful — purpose and proportionality matter.",
             exercises=[mcq("A record is public. Collecting everything about a "
                            "private individual 'just in case' is:",
                            ["Fine — it's public", "Disproportionate and likely unlawful",
                             "Required", "Good practice"],
                            "Disproportionate and likely unlawful", "osint-ethics",
                            "Minimise to the authorised question; proportionality matters.")],
             hints=["Public source ≠ unlimited use. Mind purpose and proportionality."]),
       ],
       [mcq("OSINT is intelligence from:", ["Private accounts", "Publicly available sources",
            "Phishing", "Malware"], "Publicly available sources", "osint-fundamentals",
            "Public sources only."),
        short("First step of the intelligence cycle?", "plan", "osint-fundamentals",
              "Plan the question and scope."),
        mcq("Which principle limits what you collect?", ["Maximisation", "Proportionality",
            "Obfuscation", "Persistence"], "Proportionality", "osint-ethics",
            "Collect only what the authorised question needs.")]),

    _c("osint-techniques", "OSINT Investigation Techniques",
       "Practical, source-safe techniques: advanced search, metadata, geolocation "
       "basics, and the discipline of verification.",
       "intermediate", ["osint-fundamentals"],
       [
           L("Advanced search & pivoting", "intermediate", 20, "osint-techniques",
             "Search operators focus results: site/domain filters, exact phrases, "
             "file-type filters and date ranges turn a vague query into a precise "
             "one. *Pivoting* means using one confirmed fact (a domain, a handle, an "
             "organisation) to find related public records — then confirming each "
             "new fact independently rather than assuming the link.",
             exercises=[short("Using one confirmed fact to find related public data is called ___.",
                              "pivoting", "osint-techniques", "Pivoting expands from confirmed facts.")],
             hints=["Narrow first (operators), then pivot from confirmed facts."]),
           L("Metadata and media", "intermediate", 15, "osint-techniques",
             "Public files and images can carry metadata (e.g. EXIF) such as "
             "timestamps or camera details. In the sandbox you examine provided "
             "sample files with tools like `exiftool` to understand what metadata "
             "reveals — and, defensively, why publishers should strip it. Treat any "
             "personal data found under the same ethics and minimisation rules.",
             exercises=[mcq("Image metadata that may include timestamps is called:",
                            ["DNS", "EXIF", "TLS", "CSP"], "EXIF", "osint-techniques",
                            "EXIF metadata can accompany images.")],
             walkthrough=[wstep("Inspect the sample", "Run `exiftool sample.jpg` on the provided file."),
                          wstep("Read the fields", "Note any timestamp/device fields present."),
                          wstep("Draw the defensive lesson", "Note why publishers strip metadata.")]),
           L("Verification & corroboration", "intermediate", 20, "osint-corroboration",
             "A single source is a lead, not a fact. Corroborate with **independent** "
             "sources, assess each source's reliability and recency, and record the "
             "provenance of every claim. State confidence explicitly and distinguish "
             "what you *know* from what you *infer*. Unverified findings must be "
             "labelled as such in the report.",
             exercises=[short("A single unverified source is a ___, not a fact.", "lead",
                              "osint-corroboration", "Corroborate before asserting.")]),
       ],
       [mcq("Pivoting should expand from:", ["Any guess", "Confirmed facts",
            "Private data", "Assumptions"], "Confirmed facts", "osint-techniques",
            "Pivot from confirmed facts, re-verifying each step."),
        short("Image metadata standard mentioned (acronym)?", "EXIF", "osint-techniques",
              "EXIF."),
        mcq("Before asserting a finding you must:", ["Publish it", "Corroborate independently",
            "Delete sources", "Assume it"], "Corroborate independently",
            "osint-corroboration", "Independent corroboration first.")],
       cprereqs=["osint-fundamentals"], lab="osint-investigation-lab"),

    _c("osint-opsec-reporting", "OSINT OPSEC & Reporting",
       "Protect the investigation and the investigator, and communicate findings "
       "responsibly.",
       "intermediate", ["osint-techniques"],
       [
           L("Investigator OPSEC", "intermediate", 15, "osint-ethics",
             "Collection can reveal *you* to the subject. OPSEC for OSINT means not "
             "tipping off a target (e.g. by interacting with their content), keeping "
             "research accounts separate from personal ones, and documenting your "
             "own actions for accountability. Passive observation of public data is "
             "preferred over any interaction.",
             exercises=[mcq("Which best preserves OPSEC?",
                            ["Liking the target's posts", "Passive observation of public data",
                             "Messaging the target", "Logging into their account"],
                            "Passive observation of public data", "osint-ethics",
                            "Avoid interaction that tips off the subject.")],
             hints=["Interacting with a target's content can reveal your interest."]),
           L("Responsible reporting", "intermediate", 15, "security-reporting",
             "An OSINT report states the authorised question, the sources (with "
             "provenance and dates), the analysis, an explicit confidence level, and "
             "the limits of the findings. Separate fact from inference, redact "
             "unnecessary personal data, and note anything that could not be "
             "verified. The reader must be able to retrace your reasoning.",
             exercises=[short("Reports must separate fact from ___.", "inference",
                              "security-reporting", "Distinguish knowledge from inference.")]),
       ],
       [mcq("Best OPSEC choice:", ["Interact with the target", "Observe public data passively",
            "Use your personal account", "Contact the subject"],
            "Observe public data passively", "osint-ethics", "Passive, non-tipping observation."),
        short("Reports state an explicit ___ level.", "confidence", "security-reporting",
              "State confidence explicitly.")],
       cprereqs=["osint-techniques"]),

    _c("osint-tools", "OSINT Tooling",
       "The practical toolkit for authorised, public-source collection: "
       "search operators, theHarvester, Amass, recon-ng, Shodan, dnsrecon and "
       "username/metadata tools.",
       "intermediate", ["osint-techniques"],
       [
           L("Search operators & dorking", "intermediate", 15, "osint-tooling",
             "Advanced search operators are the most powerful OSINT 'tool' of all: "
             "`site:`, `filetype:`, `intitle:`, exact phrases and date ranges turn "
             "a search engine into a precise collector of **public** information. "
             "Used ethically, 'dorking' finds inadvertently-public documents an "
             "organisation should lock down — a defensive win as much as a "
             "collection technique.",
             exercises=[short("Operator restricting results to one domain?", "site:",
                              "osint-tooling", "site: filters by domain.")],
             hints=["Combine operators: site:example.com filetype:pdf"]),
           L("Domain & infrastructure recon", "intermediate", 20, "osint-tooling",
             "Public technical sources map an org's footprint.\n\n```\n"
             "whois example.com\ndnsrecon -d example.com\n"
             "theHarvester -d example.com -b bing      # public emails/subdomains\n"
             "amass enum -passive -d example.com        # passive subdomain enum\n```\n"
             "Prefer **passive** modes (public data only). Certificate-transparency "
             "logs (crt.sh) and public DNS reveal subdomains without touching the "
             "target. This is the recon a defender runs on themselves to find "
             "exposure.",
             exercises=[cmd("Passive subdomain enumeration (amass enum -___ -d ...)?",
                            "-passive", "osint-tooling", "`-passive` uses public sources only.")],
             walkthrough=[wstep("whois", "Start with `whois` for registration data."),
                          wstep("DNS", "Run `dnsrecon`/dig for records."),
                          wstep("Passive subdomains", "Use amass -passive and crt.sh."),
                          wstep("Corroborate", "Cross-check findings before reporting.")]),
           L("People, usernames & metadata", "intermediate", 15, "osint-tooling",
             "recon-ng is a modular framework that organises public lookups into a "
             "workspace with a database. Username tools (e.g. Sherlock) check where "
             "a handle appears across public sites; `exiftool` reads public file "
             "metadata. Apply the same ethics: minimise collection, respect "
             "privacy, and record provenance for every finding.",
             exercises=[short("Modular OSINT framework with a workspace/db?", "recon-ng",
                              "osint-tooling", "recon-ng.")]),
       ],
       [short("Operator to limit results to a domain?", "site:", "osint-tooling", "site:."),
        cmd("Flag for passive amass enumeration?", "-passive", "osint-tooling", "`-passive`."),
        mcq("Preferred collection mode to avoid touching the target:",
            ["Active", "Passive (public sources)", "Intrusive", "Credentialed"],
            "Passive (public sources)", "osint-tooling", "Passive, public-source only.")],
       cprereqs=["osint-techniques"], lab="osint-investigation-lab"),
]
