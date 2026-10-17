# Learning Paths & Progression

## Difficulty levels

| Level | Name | Purpose |
|------:|------|---------|
| 0 | Orientation | Using the platform, terminals, isolated labs, safety |
| 1 | Beginner / very easy | Foundations without prior experience |
| 2 | Easy | Apply foundations to simple practical tasks |
| 3 | Intermediate | Combine techniques on realistic problems |
| 4 | Hard | Investigate unfamiliar environments with less guidance |
| 5 | Advanced | Specialist-level technical skills |
| 6 | Expert | Unfamiliar, technically demanding, independent work |
| 7 | Specialisation & Mastery | Discipline expertise + capstones |

Difficulty is assigned from knowledge requirements, complexity, independence,
number of stages and expected effort — not merely duration.

## Progression rules (as implemented)

- Every course, lesson and lab carries a difficulty; VM profiles carry a
  difficulty classification.
- Prerequisites are **soft-locked**: unmet prerequisites produce a warning and
  (in paths) a *locked* marker, but learners may proceed (`progression.allow_bypass`),
  and admins can override (`progression.enforce_prerequisites`).
- **Competencies** (0–4) are demonstrated through completed lessons, passed
  assessments and solved labs; the mastery threshold is configurable.
- Recommendations consider completed courses, assessment results, prerequisites,
  preferred specialisation and the learner's competency frontier. **Hint usage
  alone never counts as poor understanding.**
- Progress is stored server-side. Completed content is distinguished from
  mastered competencies. Revisiting previous levels and repeating labs is
  allowed and never erases achievements. Updating a course does not erase
  progress.

## Built-in paths

1. **Complete Beginner** — orientation → fundamentals → first easy lab → reporting.
2. **Web Penetration Testing** — HTTP → web tech → SQL → auth/session/access →
   SQLi/XSS → API → intermediate lab → advanced web → final assessment.
3. **Infrastructure Penetration Testing** — networking/Linux/Windows → recon →
   enumeration → assessment → Linux/Windows security → multi-service lab.
4. **Active Directory Security** — Windows → AD fundamentals → identity security
   → enterprise directory lab.
5. **Defensive Security** — admin → logging → monitoring → SIEM → detection →
   hunting → IR → forensics → investigation lab.
6. **Reverse Engineering** — programming → Python → RE fundamentals → memory
   safety → malware triage → RE challenge.
7. **Container & Infrastructure Security** — Linux → Docker → Kubernetes →
   segmentation → IaC → container lab.
8. **Digital Forensics** — logs → forensics → network monitoring → IR → malware
   → investigation challenge.

## Authoring paths

Paths live in `backend/app/catalog/content/paths.py`. Each step references a
real `course_id` or `lab_id`, with `required` and a `note`. Administrators can
add paths without editing application source; re-import with `hacklab init`.
`hacklab paths list` shows them.
