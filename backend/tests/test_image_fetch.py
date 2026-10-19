"""fetch_image is idempotent: a present image is not re-downloaded (so setup/update don't re-pull GBs)."""
from __future__ import annotations

import pytest

from backend.app.images import service as images


def _some_qcow2_key(session):
    for img in images.list_images(session):
        if img.source_kind == "qcow2" and img.source:
            return img.key
    pytest.skip("no downloadable image in the catalogue")


def test_present_image_is_not_refetched(admin, monkeypatch):
    from backend.app.database.base import session_scope

    calls = {"n": 0}

    def _boom(*a, **k):
        calls["n"] += 1
        raise AssertionError("fetch_image tried to download a present image")

    # Any network attempt would call urlopen; a present image must never reach it.
    monkeypatch.setattr(images.urllib.request, "urlopen", _boom)
    with session_scope() as s:
        key = _some_qcow2_key(s)
        img = images.get_image(s, key)
        p = images.image_path(img)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"QFI\xfb present image bytes")
        img.checksum = None   # catalogue images are verified at fetch time; none pinned here
        s.flush()

        out = images.fetch_image(s, key)   # should short-circuit, no download
        assert out.status.value == "present"
        assert calls["n"] == 0
        p.unlink()
