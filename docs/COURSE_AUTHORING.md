# Course Authoring

Courses are authored as structured Python in
`backend/app/catalog/content/courses_*.py` (the source of truth) and imported
into the database. You can add or edit courses without changing application
source — the content modules *are* the content layer, and the importer is
idempotent and preserves learner progress and achievements.

## Anatomy of a course

Use the helpers in `_authoring.py`:

```python
from backend.app.catalog.content._authoring import (
    course, lesson, mcq, short, cmd, exercise, assessment, wstep)

COURSES = [
  course(
    "my-course-id", "My Course", "One-line description.",
    difficulty="intermediate",          # orientation|beginner|easy|intermediate|hard|advanced|expert|mastery
    category="web-security", specialization="web",
    prerequisites=["http-https"],       # course ids
    competency_prereqs=["http-fundamentals"],
    lab_id="web-security-lab",           # optional
    lessons=[
      lesson("Lesson title", "intermediate", 20, "input-validation",
             """Markdown body with **bold**, `code` and fenced blocks.""",
             exercises=[
               mcq("Question?", ["A","B","C"], "B", "input-validation",
                   "Why B is correct.", hints=["a nudge"]),
             ],
             hints=["optional lesson hint"],              # optional scaffolding
             walkthrough=[wstep("Step 1","do this")]),    # optional
    ],
    assessment=assessment("Final check", [
      short("Short answer?", "answer", "input-validation", "explanation"),
    ], difficulty="intermediate", passing_score=70),
  ),
]
```

- **Difficulty** must reflect real knowledge/complexity/independence, not just
  length. A longer lab is not automatically "expert".
- **Competency keys** must exist in `content/competencies.py` (validated by
  `hacklab courses validate`).
- **Optional hints/walkthroughs** are advertised to the UI but their content is
  fetched on demand, so they stay hidden until the learner opts in.
- **Answers** are hashed at import; the plaintext never reaches the DB column
  the client sees.

## Register the course

Add your list to the aggregator in `content/courses.py` (`ALL_COURSES`). If you
created a new module, import it there.

## Validate & import

```bash
hacklab courses validate      # unique ids + competency references, 0 issues expected
hacklab init                  # re-import (idempotent; progress preserved)
```

## Materialising YAML (optional)

The authored content can be exported to versioned YAML/JSON under `catalog/`
for review/bulk workflows; the importer and CLI operate from the Python source
by default. Difficulty must increase gradually within a course, and a learning
path (see [LEARNING_PATHS.md](LEARNING_PATHS.md)) sequences courses from easy to
hard.
