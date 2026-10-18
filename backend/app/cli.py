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


# ---- training environments (for host tools such as a homelab dashboard) ----
env_app = typer.Typer(help="Training environments: list, start, stop, delete, clean up")
app.add_typer(env_app, name="env")


def _vm_row(s, inst) -> dict:
    """One VM as plain data: no credentials, no flags, no learner e-mail."""
    import os as _os
    from backend.app.database.models import User, VirtualNetwork
    owner = s.get(User, inst.owner_id)
    net = s.get(VirtualNetwork, inst.network_id) if inst.network_id else None
    disk = 0
    if inst.overlay_path:
        try:
            st = _os.stat(inst.overlay_path)
            disk = getattr(st, "st_blocks", 0) * 512 or st.st_size
        except OSError:
            disk = 0
    when = lambda d: d.isoformat() if d else None  # noqa: E731
    return {"kind": "vm", "id": inst.id, "name": inst.name, "status": inst.status.value, "driver": inst.driver,
            "domain": inst.driver_ref, "vcpu": inst.vcpu, "memory_mb": inst.memory_mb, "ip_address": inst.ip_address,
            "network": {"mode": net.mode.value, "external_access": bool(net.external_access), "cidr": net.cidr} if net else None,
            "lab_instance_id": inst.lab_instance_id, "persistent": inst.persistent, "disposable": inst.disposable,
            "owner": owner.username if owner else None, "disk_bytes": disk, "started_at": when(inst.started_at),
            "stopped_at": when(inst.stopped_at), "last_heartbeat": when(inst.last_heartbeat), "last_error": inst.last_error}


def _env_out(data, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(data) + "\n")
    else:
        console.print_json(json.dumps(data))


@env_app.command("list")
def env_list(as_json: bool = typer.Option(False, "--json", help="Plain JSON on stdout")) -> None:
    """Every VM and lab that hasn't been deleted, with its resources and network."""
    from sqlalchemy import select
    from backend.app.database.base import session_scope
    from backend.app.database.models import Lab, LabInstance, VMInstance, VMStatus
    with session_scope() as s:
        vms_ = [_vm_row(s, i) for i in s.execute(select(VMInstance).where(VMInstance.status != VMStatus.deleted)).scalars()]
        labs = []
        for li in s.execute(select(LabInstance).where(LabInstance.status != VMStatus.deleted)).scalars():
            lab = s.get(Lab, li.lab_id)
            labs.append({"kind": "lab", "id": li.id, "lab_id": li.lab_id, "title": getattr(lab, "title", None) or li.lab_id,
                         "status": li.status.value, "last_error": li.last_error,
                         "started_at": li.started_at.isoformat() if li.started_at else None,
                         "machines": [v["id"] for v in vms_ if v["lab_instance_id"] == li.id]})
    _env_out({"vms": vms_, "labs": labs}, as_json)


def _find(s, kind: str, ident: str):
    from backend.app.database.models import LabInstance, VMInstance
    obj = s.get(VMInstance if kind == "vm" else LabInstance, ident)
    if obj is None:
        console.print(f"[red]No such {kind}: {ident}[/red]")
        raise typer.Exit(2)
    return obj


def _check_kind(kind: str) -> None:
    if kind not in ("vm", "lab"):
        console.print("[red]KIND is vm or lab[/red]")
        raise typer.Exit(2)


@env_app.command("stop")
def env_stop(kind: str, ident: str, force: bool = False) -> None:
    """Stop a VM or a whole lab (its disks are kept)."""
    from backend.app.database.base import session_scope
    from backend.app.labs import service as labs
    from backend.app.vms import service as vms
    _check_kind(kind)
    with session_scope() as s:
        obj = _find(s, kind, ident)
        if kind == "vm":
            vms.stop_instance(s, obj, force=force)
        else:
            labs.stop_lab(s, obj)
        _env_out({"ok": True, "status": obj.status.value}, True)


@env_app.command("start")
def env_start(kind: str, ident: str) -> None:
    """Start a stopped VM or lab again (waits until it runs)."""
    from backend.app.database.base import session_scope
    from backend.app.labs import service as labs
    from backend.app.vms import service as vms
    _check_kind(kind)
    with session_scope() as s:
        obj = _find(s, kind, ident)
        try:
            if kind == "vm":
                vms.start_instance(s, obj)
            else:
                labs.start_lab(s, obj)
        except Exception as e:  # noqa: BLE001 -- the service records last_error; say it too
            _env_out({"ok": False, "error": str(e)}, True)
            raise typer.Exit(1)
        _env_out({"ok": True, "status": obj.status.value}, True)


@env_app.command("delete")
def env_delete(kind: str, ident: str) -> None:
    """Delete a VM or lab: its domain, overlay disk and (for a lab) its networks. Base images are kept."""
    from backend.app.database.base import session_scope
    from backend.app.labs import service as labs
    from backend.app.vms import service as vms
    _check_kind(kind)
    with session_scope() as s:
        obj = _find(s, kind, ident)
        if kind == "vm":
            vms.delete_instance(s, obj)
        else:
            labs.delete_lab_instance(s, obj)
    _env_out({"ok": True}, True)


@env_app.command("cleanup")
def env_cleanup(apply: bool = typer.Option(False, "--apply", help="Delete them (default: only list them)")) -> None:
    """Overlay disks no VM uses any more (a dry run unless --apply)."""
    from backend.app.database.base import session_scope
    from backend.app.storage import service as storage_svc
    with session_scope() as s:
        _env_out(storage_svc.cleanup(s, dry_run=not apply), True)


# ---- storage / backup ----
@app.command()
def storage(as_json: bool = typer.Option(False, "--json", help="Plain JSON on stdout")) -> None:
    """Storage report (physical vs virtual)."""
    from backend.app.database.base import session_scope
    from backend.app.storage import service as storage_svc
    with session_scope() as s:
        _env_out(storage_svc.report(s), as_json)


@app.command()
def backup(output: str = typer.Option(None, help="Backup directory")) -> None:
    """Create a verified backup of the database and configuration."""
    from backend.app.maintenance import backup as backup_mod
    path = backup_mod.create_backup(output)
    console.print(f"[green]Backup created: {path}[/green]")


if __name__ == "__main__":
    app()
