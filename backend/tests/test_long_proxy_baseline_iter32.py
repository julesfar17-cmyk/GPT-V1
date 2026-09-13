"""Baseline backend tests for long-video proxy behavior (iteration 32).
Covers long GOP upload, processing status, and proxy skip/generation decisions.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

pytestmark = pytest.mark.skip(reason="Baseline avant correction ; régression active : test_long_proxy_policy2_iter33.py")


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
DEMO_EMAIL = "demo@beatcut.fr"
DEMO_PASSWORD = "Demo1234!"
ASSET_MANIFEST = Path("/root/beatcut-test-assets/manifest.json")
RESULT_SNAPSHOT = Path("/app/test_reports/iter32_backend_media_ids.json")


def _poll_status(session: requests.Session, media_id: str, timeout_s: int = 240) -> dict:
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = session.get(f"{BASE_URL}/api/media/{media_id}/status", timeout=20)
        assert r.status_code == 200, f"status={r.status_code} {r.text[:200]}"
        last = r.json()
        if not last.get("processing"):
            return last
        time.sleep(2)
    pytest.fail(f"Timed out waiting /status for {media_id}, last={last}")


def _poll_proxy(session: requests.Session, media_id: str, timeout_s: int = 210) -> dict:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        r = session.post(f"{BASE_URL}/api/media/proxy/{media_id}", timeout=30)
        assert r.status_code == 200, f"proxy={r.status_code} {r.text[:200]}"
        last = r.json()
        if last.get("proxy_id") or last.get("status") == "failed":
            return last
        time.sleep(3)
    return last


@pytest.fixture(scope="module")
def media_manifest() -> dict:
    assert ASSET_MANIFEST.exists(), (
        "Missing /root/beatcut-test-assets/manifest.json. "
        "Run /app/frontend/tests/generate_long_gop_assets.py before pytest."
    )
    return json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def demo_session() -> requests.Session:
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return s


@pytest.fixture(scope="module")
def uploaded_media(demo_session: requests.Session, media_manifest: dict) -> dict:
    ids = {}
    for key, path in (
        ("h264_720", media_manifest["h264_720"]),
        ("h264_800", media_manifest["h264_800"]),
    ):
        p = Path(path)
        assert p.exists(), f"asset missing: {p}"
        with p.open("rb") as fh:
            r = demo_session.post(
                f"{BASE_URL}/api/media/upload",
                files={"file": (p.name, fh, "video/mp4")},
                timeout=300,
            )
        assert r.status_code == 200, f"upload {key}: {r.status_code} {r.text[:200]}"
        body = r.json()
        assert isinstance(body.get("media_id"), str)
        ids[key] = body["media_id"]

    RESULT_SNAPSHOT.write_text(json.dumps(ids, indent=2), encoding="utf-8")
    return ids


def test_asset_manifest_shows_long_gop(media_manifest: dict):
    for key in ("h264_720", "h264_800"):
        gaps = media_manifest.get("keyframe_gaps", {}).get(key, [])
        if not gaps:
            pytest.skip("ffprobe unavailable in environment; keyframe-gap check skipped")
        # Long GOP expected around 8-10s; generator is set to 10s keyframe cadence.
        assert any(g >= 8.0 for g in gaps), f"{key} is not long-GOP enough: {gaps}"


def test_proxy_skipped_for_720p_h264_long_gop(demo_session: requests.Session, uploaded_media: dict):
    media_id = uploaded_media["h264_720"]
    status = _poll_status(demo_session, media_id)
    assert status.get("failed") is False

    proxy = _poll_proxy(demo_session, media_id)
    assert proxy.get("proxy_id") == media_id, (
        "Expected proxy skip for <=720p H264, but got different proxy behavior"
    )


def test_proxy_generated_for_above_720p_h264_long_gop(demo_session: requests.Session, uploaded_media: dict):
    media_id = uploaded_media["h264_800"]
    status = _poll_status(demo_session, media_id)
    assert status.get("failed") is False

    proxy = _poll_proxy(demo_session, media_id)
    assert proxy.get("status") != "failed", f"proxy failed for {media_id}: {proxy}"
    assert proxy.get("proxy_id"), f"Expected proxy_id for >720p source, got: {proxy}"
    assert proxy["proxy_id"] != media_id, "Expected a generated proxy_id for >720p source"


def test_proxy_endpoint_returns_401_without_auth(uploaded_media: dict):
    media_id = uploaded_media["h264_720"]
    r = requests.post(f"{BASE_URL}/api/media/proxy/{media_id}", timeout=30)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text[:200]}"
