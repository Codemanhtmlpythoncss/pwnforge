"""Job handlers wiring long-running operations into the background runner."""
from __future__ import annotations

from backend.app.database.models import Job, LabInstance, VMInstance
from backend.app.images import service as images
from backend.app.jobs.runner import register
from backend.app.labs import service as labs
from backend.app.vms import service as vms


@register("vm.start")
def _vm_start(session, job: Job, params: dict, progress) -> dict:
    inst = session.get(VMInstance, params["instance_id"])
    if inst is None:
        raise ValueError("instance not found")
    vms.start_instance(session, inst, progress=progress)
    return {"instance_id": inst.id, "status": inst.status.value,
            "ip": inst.ip_address, "driver": inst.driver}


@register("vm.reset")
def _vm_reset(session, job: Job, params: dict, progress) -> dict:
    inst = session.get(VMInstance, params["instance_id"])
    vms.reset_instance(session, inst, progress=progress)
    return {"instance_id": inst.id, "status": inst.status.value}


@register("lab.start")
def _lab_start(session, job: Job, params: dict, progress) -> dict:
    li = session.get(LabInstance, params["lab_instance_id"])
    if li is None:
        raise ValueError("lab instance not found")
    labs.start_lab(session, li, progress=progress)
    return {"lab_instance_id": li.id, "status": li.status.value}


@register("image.fetch")
def _image_fetch(session, job: Job, params: dict, progress) -> dict:
    progress.update(stage="Downloading image", percent=1)
    img = images.fetch_image(session, params["key"],
                             progress=lambda p: progress.update(percent=p))
    return {"key": img.key, "status": img.status.value}


@register("admin.update")
def _admin_update(session, job: Job, params: dict, progress) -> dict:
    from backend.app.core import updater
    return updater.run_update(session, progress=progress)
