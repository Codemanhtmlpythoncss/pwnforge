"""Pwnforge command-line interface.

Shares the same core services as the website — it never re-implements logic.
Run as ``python -m backend.app.cli <command>`` or via the ``pwnforge`` wrapper.
"""
from __future__ import annotations

import getpass
import json
import sys

import typer
from rich.console import Console
from rich.table import Table

from backend.app.core.config import get_settings

app = typer.Typer(add_completion=False, help="Pwnforge administration CLI",
                  pretty_exceptions_enable=False)
console = Console()


# --------------------------------------------------------------------------
@app.command()
def status() -> None:
    """Show platform status: driver, DB, catalogue counts."""
    from sqlalchemy import func, select
    from backend.app.database.base import session_scope
    from backend.app.database.models import Course, User, VMInstance, VMProfile, VMStatus
    from backend.app.vms.detect import host_summary
    console.print("[bold]Pwnforge status[/bold]")
    console.print(host_summary())
    try:
        with session_scope() as s:
            n = lambda m: s.execute(select(func.count()).select_from(m)).scalar_one()
            console.print(f"users={n(User)} courses={n(Course)} profiles={n(VMProfile)}")
            running = s.execute(select(func.count()).select_from(VMInstance)
                                .where(VMInstance.status == VMStatus.running)).scalar_one()
            console.print(f"running_vms={running}")
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]database not initialised? {e}[/red]")


@app.command()
def doctor() -> None:
    """Run diagnostics across host, database, images and storage."""
    from sqlalchemy import func, select
    from backend.app.database.base import session_scope
    from backend.app.database.models import BaseImage, Course, VMProfile
    from backend.app.images import service as images
    from backend.app.vms.detect import probe_host
    host = probe_host()
    ok = True
    console.print("[bold]Host[/bold]")
    for k, v in host.items():
        console.print(f"  {k}: {v}")
    try:
        with session_scope() as s:
            courses = s.execute(select(func.count()).select_from(Course)).scalar_one()
            profiles = s.execute(select(func.count()).select_from(VMProfile)).scalar_one()
            problems = images.validate_chain(s)
            console.print(f"[bold]Catalogue[/bold] courses={courses} profiles={profiles}")
            if courses < 50:
                console.print("[red]  FAIL: fewer than 50 courses[/red]"); ok = False
            if profiles < 1000:
                console.print("[red]  FAIL: fewer than 1000 profiles[/red]"); ok = False
            if problems:
                console.print(f"[red]  image chain problems: {problems}[/red]"); ok = False
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]database error: {e}[/red]"); ok = False
    console.print("[green]doctor: OK[/green]" if ok else "[red]doctor: problems found[/red]")
    raise typer.Exit(0 if ok else 1)


@app.command()
def init(admin_user: str = typer.Option(None), admin_password: str = typer.Option(None),
         profiles: bool = True) -> None:
    """Initialise the database, import the catalogue and create an admin."""
    from backend.app.auth import service as auth
    from backend.app.database import init_db
    from backend.app.database.base import session_scope
    from backend.app.database.models import UserRole
    console.print("Creating schema and importing catalogue…")
    counts = init_db.initialise(include_profiles=profiles)
    console.print(f"Imported: {json.dumps(counts)}")
    if auth.count_users_safe():
        console.print("[yellow]Users already exist; skipping admin creation.[/yellow]")
        return
    user = admin_user or input("Admin username: ")
    pw = admin_password or getpass.getpass("Admin password: ")
    with session_scope() as s:
        auth.create_user(s, username=user, password=pw, role=UserRole.administrator)
    console.print(f"[green]Administrator '{user}' created.[/green]")


@app.command()
def serve(host: str = None, port: int = None, reload: bool = False) -> None:
    """Run the web server (uvicorn)."""
    import uvicorn
    from sqlalchemy import select
    from backend.app.core import settings_service as cfg
    from backend.app.database.base import session_scope
    s = get_settings()
    # Resolve bind address from settings (LAN access toggle).
    bind_host = host
    bind_port = port
    try:
        with session_scope() as db:
            if bind_port is None:
                bind_port = int(cfg.get_setting(db, "server.port", s.port))
            if bind_host is None:
                lan = bool(cfg.get_setting(db, "server.lan_access", False))
                bind_host = "0.0.0.0" if lan else "127.0.0.1"
    except Exception:
        bind_host = bind_host or s.host
        bind_port = bind_port or s.port
    url = f"http://{'localhost' if bind_host in ('127.0.0.1','0.0.0.0') else bind_host}:{bind_port}"
    console.print(f"[bold green]Pwnforge serving at {url}[/bold green]")
    if bind_host == "0.0.0.0":
        console.print("[yellow]LAN access enabled — reachable from the local network.[/yellow]")
    uvicorn.run("backend.app.main:app", host=bind_host, port=bind_port, reload=reload)


# ---- courses / paths ----
courses_app = typer.Typer(help="Course catalogue")
app.add_typer(courses_app, name="courses")


@courses_app.command("list")
def courses_list() -> None:
    from sqlalchemy import select
    from backend.app.database.base import session_scope
    from backend.app.database.models import Course
    t = Table("id", "title", "difficulty", "category")
    with session_scope() as s:
        for c in s.execute(select(Course).order_by(Course.category, Course.title)).scalars():
            t.add_row(c.id, c.title, c.difficulty.value, c.category)
    console.print(t)


@courses_app.command("validate")
def courses_validate() -> None:
    from backend.app.catalog.content.courses import ALL_COURSES, validate_unique_ids
    from backend.app.catalog.content.competencies import all_competency_keys
    validate_unique_ids()
    keys = all_competency_keys()
    issues = 0
    for c in ALL_COURSES:
        for l in c["lessons"]:
            if l["competency"] and l["competency"] not in keys:
                console.print(f"[red]{c['id']}: unknown competency {l['competency']}[/red]"); issues += 1
    console.print(f"{len(ALL_COURSES)} courses, {issues} issues")
    raise typer.Exit(1 if issues else 0)


paths_app = typer.Typer(help="Learning paths")
app.add_typer(paths_app, name="paths")


@paths_app.command("list")
def paths_list() -> None:
    from backend.app.database.base import session_scope
    from backend.app.learning_paths import service as paths
    with session_scope() as s:
        for p in paths.list_paths(s):
            console.print(f"{p['id']:28} {p['title']} ({p['step_count']} steps)")


# ---- profiles ----
profiles_app = typer.Typer(help="VM profiles")
app.add_typer(profiles_app, name="profiles")


@profiles_app.command("stats")
def profiles_stats() -> None:
    from backend.app.database.base import session_scope
    from backend.app.profiles import service as profiles
    with session_scope() as s:
        console.print_json(json.dumps(profiles.stats(s)))


@profiles_app.command("search")
def profiles_search(term: str) -> None:
    from backend.app.database.base import session_scope
    from backend.app.profiles import service as profiles
    with session_scope() as s:
        r = profiles.list_profiles(s, q=term, limit=25)
    console.print(f"{r['total']} matches for '{term}':")
    for p in r["items"]:
        console.print(f"  {p['id']:40} {p['difficulty']:12} {p['readiness']}")


@profiles_app.command("validate")
def profiles_validate() -> None:
    from backend.app.catalog.content.profiles import generate_profiles
    from backend.app.profiles.service import validate_definition
    profs = generate_profiles()
    issues = 0
    for p in profs:
        errs = validate_definition(p)
        if errs:
            console.print(f"[red]{p['id']}: {errs}[/red]"); issues += 1
    console.print(f"{len(profs)} profiles, {issues} invalid")
    raise typer.Exit(1 if issues else 0)


# ---- images ----
images_app = typer.Typer(help="Base images")
app.add_typer(images_app, name="images")


@images_app.command("list")
def images_list() -> None:
    from backend.app.database.base import session_scope
    from backend.app.images import service as images
    t = Table("key", "os", "status", "parent")
    with session_scope() as s:
        for i in images.list_images(s):
            t.add_row(i.key, f"{i.os_family} {i.os_version}", i.status.value, i.parent_key or "-")
    console.print(t)


@images_app.command("fetch")
def images_fetch(key: str) -> None:
    """Download/build a base image ON THIS HOST (never automatic)."""
    from backend.app.database.base import session_scope
    from backend.app.images import service as images
    console.print(f"Fetching {key} (this runs only on the host, when you invoke it)…")
    with session_scope() as s:
        try:
            img = images.fetch_image(s, key, progress=lambda p: console.print(f"  {p}%", end="\r"))
            console.print(f"[green]{key}: {img.status.value}[/green]")
        except images.ImageError as e:
            console.print(f"[red]{e}[/red]"); raise typer.Exit(1)


@images_app.command("prune")
def images_prune(dry_run: bool = True) -> None:
    from backend.app.database.base import session_scope
    from backend.app.storage import service as storage
    with session_scope() as s:
        console.print_json(json.dumps(storage.cleanup(s, dry_run=dry_run)))


# ---- storage / backup ----
@app.command()
def storage() -> None:
    """Storage report (physical vs virtual)."""
    from backend.app.database.base import session_scope
    from backend.app.storage import service as storage_svc
    with session_scope() as s:
        console.print_json(json.dumps(storage_svc.report(s)))


@app.command()
def backup(output: str = typer.Option(None, help="Backup directory")) -> None:
    """Create a verified backup of the database and configuration."""
    from backend.app.maintenance import backup as backup_mod
    path = backup_mod.create_backup(output)
    console.print(f"[green]Backup created: {path}[/green]")


if __name__ == "__main__":
    app()
