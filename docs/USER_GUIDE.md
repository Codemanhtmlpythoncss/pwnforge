# User Guide

## Signing in

On a fresh install the login screen asks you to **create the administrator**.
After that, everyone signs in with a username and password. The site binds to
localhost by default; your administrator can enable LAN access.

## Dashboard

Shows your current level, course progress, running VMs and active labs, recent
achievements and activity, and **real** host CPU/RAM/disk usage (virtual disk
capacity is reported separately from actual physical consumption).

## Courses

Browse the catalogue with search and filters (difficulty, category). Open a
course to see its objectives, lessons and assessment. Each lesson has:

- **Content** — readable, with code examples.
- **Exercises** — multiple-choice / short-answer / command; graded
  server-side.
- **Optional hints** — click *Hint* to reveal them one at a time. Using a hint
  is never penalised; it is only recorded so recommendations can adapt.
- **Optional walkthroughs** — click *Show walkthrough* for step-by-step
  guidance when you want it.
- **Mark complete** — records your progress.

An **assessment** at the end is graded server-side; passing (plus completing
the lessons) completes the course. The correct answers never reach your
browser.

If a course lists prerequisites you haven't met, you'll see a *Prerequisites
recommended* notice — you can still proceed.

## Learning paths

Structured progressions (e.g. *Web Penetration Testing*, *Defensive Security*)
that order courses and labs from easy to hard. Steps gated by an incomplete
required step show as *locked*, but nothing stops you exploring.

## Skills

Your competency map: each skill has a 0–4 level driven by demonstrated
evidence (completed lessons, passed assessments, solved labs). Domains show how
many competencies you've mastered.

## Machine catalogue & labs

- **Machine Catalogue** lists 1,000+ VM profiles. Filter by difficulty,
  category, OS. A profile marked **ready** can be launched; others show why
  (e.g. *requires base image*). *Launch* starts a single VM.
- **Labs** are multi-machine environments on an isolated network. *Start lab*
  brings up all machines in dependency order; *Open workspace* gives you the
  terminal, machine list, network topology and flag submission.

### Lab workspace

- Pick a machine to open its **terminal** (xterm.js over an authorised
  WebSocket). On a KVM host this is the guest's serial console; on a host
  without a hypervisor it is a clearly-labelled **simulated** terminal (no host
  shell is ever exposed).
- **Submit flag** validates server-side; a correct flag awards points and
  competency evidence.
- **Reset** returns a disposable VM to its clean baseline — your learning
  progress is untouched.

## Achievements & XP

Earn XP and achievements for real milestones (first course, mastering a domain,
completing labs, streaks). An administrator can disable gamification entirely.

## Theme

Toggle dark/light from the sidebar. Dark is the default.
