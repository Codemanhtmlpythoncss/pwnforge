"""Authoring helpers for courses.

These produce plain dicts that the importer turns into ORM rows. Keeping the
authored content as structured Python means it is deterministic, reviewable and
easy to materialise to YAML.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def mcq(prompt: str, choices: list[str], answer: str, competency: str,
        explanation: str, points: int = 10, hints: list[str] | None = None) -> dict:
    assert answer in choices, f"answer {answer!r} not among choices for {prompt!r}"
    return {"kind": "mcq", "prompt": prompt, "choices": choices, "answer": answer,
            "competency": competency, "explanation": explanation, "points": points,
            "hints": hints or []}


def short(prompt: str, answer: str, competency: str, explanation: str,
          points: int = 10, hints: list[str] | None = None) -> dict:
    return {"kind": "short_answer", "prompt": prompt, "answer": answer,
            "competency": competency, "explanation": explanation, "points": points,
            "hints": hints or []}


def cmd(prompt: str, answer: str, competency: str, explanation: str,
        points: int = 10, hints: list[str] | None = None) -> dict:
    return {"kind": "command", "prompt": prompt, "answer": answer,
            "competency": competency, "explanation": explanation, "points": points,
            "hints": hints or []}


def exercise(title: str, prompt: str, kind: str, answer: str | None,
             competency: str, explanation: str = "", points: int = 10,
             choices: list[str] | None = None, hints: list[str] | None = None,
             walkthrough: list[dict] | None = None) -> dict:
    return {"title": title, "prompt": prompt, "kind": kind, "answer": answer,
            "competency": competency, "explanation": explanation, "points": points,
            "choices": choices or [], "hints": hints or [],
            "walkthrough": walkthrough or []}


def lesson(title: str, difficulty: str, minutes: int, competency: str, body: str,
           *, exercises: list[dict] | None = None, hints: list[str] | None = None,
           walkthrough: list[dict] | None = None) -> dict:
    return {"title": title, "difficulty": difficulty, "minutes": minutes,
            "competency": competency, "body": body.strip(),
            "exercises": exercises or [],
            "hints": [{"text": h} for h in (hints or [])],
            "walkthrough": walkthrough or []}


def wstep(title: str, detail: str) -> dict:
    return {"title": title, "detail": detail}


def course(id: str, title: str, description: str, difficulty: str, category: str,
           lessons: list[dict], *, specialization: str | None = None,
           minutes: int | None = None, objectives: list[str] | None = None,
           prerequisites: list[str] | None = None,
           competency_prereqs: list[str] | None = None, tags: list[str] | None = None,
           references: list[str] | None = None, os_requirements: list[str] | None = None,
           lab_id: str | None = None, assessment: dict | None = None,
           version: str = "1.0.0") -> dict:
    # Derive objectives from lesson titles when the author did not supply them,
    # so every course always has concrete learning objectives.
    if not objectives:
        objectives = [f"Understand {l['title'].lower()}" for l in lessons]
    return {
        "id": id, "title": title, "description": description, "difficulty": difficulty,
        "category": category, "specialization": specialization,
        "estimated_minutes": minutes or sum(l["minutes"] for l in lessons) + 20,
        "objectives": objectives, "prerequisites": prerequisites or [],
        "competency_prereqs": competency_prereqs or [], "tags": tags or [],
        "references": references or [], "os_requirements": os_requirements or [],
        "lab_id": lab_id, "version": version,
        "lessons": lessons, "assessment": assessment,
    }


def assessment(title: str, questions: list[dict], difficulty: str,
               passing_score: int = 70, description: str = "") -> dict:
    return {"title": title, "questions": questions, "difficulty": difficulty,
            "passing_score": passing_score, "description": description}
