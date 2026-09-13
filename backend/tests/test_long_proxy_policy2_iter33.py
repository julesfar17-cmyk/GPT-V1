"""Policy2 proxy regression tests (iteration 33).

Modules/features covered:
- /api/media/proxy lazy generation + reuse semantics
- long 720p now requires separate proxy (policy2)
- >720p long source still proxied
- short <=720p H264 stays skipped (retention)
- auth guard (401)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
import pytest
import requests
from dotenv import load_dotenv


load_dotenv(Path("/app/frontend/.env"))


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
DEMO_EMAIL = "demo@beatcut.fr"
DEMO_PASSWORD = "Demo1234!"
ASSET_MANIFEST = Path("/root/beatcut-test-assets/manifest.json")
ITER32_MEDIA = Path("/app/test_reports/iter32_backend_media_ids.json")
SHORT_720 = Path("/root/beatcut-test-assets/h264_short_1280x720_20s.mp4")


def _run(cmd: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _probe_video_basic(path: Path) -> dict:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    proc = _run([ffmpeg, "-hide_banner", "-i", str(path)], timeout=60)
    out = (proc.stderr or "") + "\n" + (proc.stdout or "")
    m_v = re.search(r"Video:\s*(\w+).*?(\d{2,5})x(\d{2,5}).*?(\d+(?:\.\d+)?)\s*fps", out)
    m_d = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", out)
    if not m_v or not m_d:
        raise AssertionError(f"Unable to parse ffmpeg probe output for {path}")
    duration = int(m_d.group(1)) * 3600 + int(m_d.group(2)) * 60 + float(m_d.group(3))
    return {
        "codec": m_v.group(1).lower(),
        "width": int(m_v.group(2)),
        "height": int(m_v.group(3)),
        "fps": float(m_v.group(4)),
        "duration": duration,
    }


def _keyframe_gaps(path: Path) -> list[float]:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    # ffprobe may be unavailable in runtime; use ffmpeg showinfo for I-frame timestamps.
    proc = _run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(path),
            "-vf",
            "select='eq(pict_type\\,I)',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        timeout=180,
    )
    out = (proc.stderr or "") + "\n" + (proc.stdout or "")
    pts = [float(x) for x in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", out)]
    if len(pts) < 2:
        return []
    return [round(pts[i] - pts[i - 1], 3) for i in range(1, len(pts))]


def _poll_status(session: requests.Session, media_id: str, timeout_s: int = 360) -> dict:
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = session.get(f"{BASE_URL}/api/media/{media_id}/status", timeout=25)
        if r.status_code == 404:
            pytest.skip(f"media not found: {media_id}")
        assert r.status_code == 200, f"status={r.status_code} {r.text[:200]}"
        last = r.json()
        if not last.get("processing"):
            return last
        time.sleep(2)
    pytest.fail(f"Timed out waiting /status for {media_id}, last={last}")


def _poll_proxy(session: requests.Session, media_id: str, timeout_s: int = 360) -> dict:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        r = session.post(f"{BASE_URL}/api/media/proxy/{media_id}", timeout=35)
        assert r.status_code == 200, f"proxy={r.status_code} {r.text[:200]}"
        last = r.json()
        if last.get("proxy_id") or last.get("status") == "failed":
            return last
        time.sleep(2)
    pytest.fail(f"Timed out waiting /proxy for {media_id}, last={last}")


def _download_media(session: requests.Session, media_id: str) -> Path:
    r = session.get(f"{BASE_URL}/api/media/{media_id}", timeout=120)
    assert r.status_code == 200, f"download={r.status_code} {r.text[:200]}"
    fd, tmp = tempfile.mkstemp(prefix=f"proxy_{media_id}_", suffix=".mp4")
    os.close(fd)
    p = Path(tmp)
    p.write_bytes(r.content)
    return p


def _ensure_short_720_asset() -> Path:
    if SHORT_720.exists():
        return SHORT_720
    SHORT_720.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    proc = _run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1280x720:rate=24:duration=20",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "26",
            "-g",
            "48",
            "-keyint_min",
            "48",
            "-sc_threshold",
            "0",
            str(SHORT_720),
        ],
        timeout=240,
    )
    assert proc.returncode == 0 and SHORT_720.exists(), proc.stderr[-500:]
    return SHORT_720


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
def manifest() -> dict:
    assert ASSET_MANIFEST.exists(), "Missing /root/beatcut-test-assets/manifest.json"
    return json.loads(ASSET_MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def uploaded_media(demo_session: requests.Session, manifest: dict) -> dict:
    out = {}
    for key, path in (("h264_720", manifest["h264_720"]), ("h264_800", manifest["h264_800"])):
        p = Path(path)
        assert p.exists(), f"asset missing: {p}"
        with p.open("rb") as fh:
            r = demo_session.post(
                f"{BASE_URL}/api/media/upload",
                files={"file": (p.name, fh, "video/mp4")},
                timeout=300,
            )
        assert r.status_code == 200, f"upload {key}: {r.status_code} {r.text[:200]}"
        out[key] = r.json()["media_id"]

    short = _ensure_short_720_asset()
    with short.open("rb") as fh:
        r = demo_session.post(
            f"{BASE_URL}/api/media/upload",
            files={"file": (short.name, fh, "video/mp4")},
            timeout=180,
        )
    assert r.status_code == 200, f"upload short720: {r.status_code} {r.text[:200]}"
    out["short_720"] = r.json()["media_id"]
    return out


def test_existing_iter32_long720_now_gets_separate_proxy_lazily(demo_session: requests.Session):
    """Policy2 migration check on known prior media ID from iteration 32."""
    if not ITER32_MEDIA.exists():
        pytest.skip("iter32 media snapshot missing")
    media_id = json.loads(ITER32_MEDIA.read_text(encoding="utf-8")).get("h264_720")
    if not media_id:
        pytest.skip("iter32 h264_720 media_id missing")

    _poll_status(demo_session, media_id)
    proxy = _poll_proxy(demo_session, media_id)
    assert proxy.get("status") != "failed", f"proxy failed: {proxy}"
    assert proxy.get("proxy_id"), f"no proxy_id returned: {proxy}"
    assert proxy["proxy_id"] != media_id, "policy2 expected generated proxy for long 720p"


@pytest.mark.parametrize("retry", [False, True])
def test_failed_proxy_retry_clears_failure_only_on_explicit_request(monkeypatch, retry):
    """Fault-state unit test; the real HTTP/media regression remains above/below."""
    import asyncio
    from unittest.mock import AsyncMock
    from bson import ObjectId
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from backend import server

    oid = ObjectId()
    user = {"user_id": "qa-proxy-retry"}
    store = AsyncMock()
    store.find_one.side_effect = [
        {"_id": oid, "filename": "retry.mp4", "metadata": {
            "content_type": "video/mp4", "user_id": user["user_id"], "proxy_failed": True}},
        None,
    ]
    worker = AsyncMock()
    monkeypatch.setattr(server, "db", {"media.files": store})
    monkeypatch.setattr(server, "_auto_proxy", worker)

    async def scenario():
        result = await server.media_proxy(str(oid), retry=retry, user=user)
        await asyncio.sleep(0)
        return result

    result = asyncio.run(scenario())
    if retry:
        assert result == {"status": "processing"}
        store.update_one.assert_awaited_once_with(
            {"_id": oid, "metadata.user_id": user["user_id"]},
            {"$unset": {"metadata.proxy_failed": ""}})
        worker.assert_awaited_once_with(oid)
    else:
        assert result == {"status": "failed"}
        store.update_one.assert_not_awaited()
        worker.assert_not_awaited()


def test_long_720_generates_proxy_and_reuses_same_proxy(demo_session: requests.Session, uploaded_media: dict):
    media_id = uploaded_media["h264_720"]
    _poll_status(demo_session, media_id)

    first = _poll_proxy(demo_session, media_id)
    assert first.get("status") != "failed", f"proxy failed: {first}"
    assert first.get("proxy_id"), f"no proxy_id: {first}"
    assert first["proxy_id"] != media_id, "long 720p should no longer be skipped"

    second = _poll_proxy(demo_session, media_id)
    assert second.get("proxy_id") == first.get("proxy_id"), "repeat proxy call must reuse existing proxy"


def test_long_above_720_generates_proxy(demo_session: requests.Session, uploaded_media: dict):
    media_id = uploaded_media["h264_800"]
    _poll_status(demo_session, media_id)
    proxy = _poll_proxy(demo_session, media_id)
    assert proxy.get("status") != "failed", f"proxy failed: {proxy}"
    assert proxy.get("proxy_id"), f"missing proxy_id: {proxy}"
    assert proxy["proxy_id"] != media_id


def test_short_720_retains_skip_behavior(demo_session: requests.Session, uploaded_media: dict):
    media_id = uploaded_media["short_720"]
    _poll_status(demo_session, media_id)
    proxy = _poll_proxy(demo_session, media_id)
    assert proxy.get("proxy_id") == media_id, f"short <=720 should be skipped, got: {proxy}"


def test_proxy_media_shape_duration_and_keyframe_spacing(demo_session: requests.Session, uploaded_media: dict):
    src_id = uploaded_media["h264_720"]
    proxy = _poll_proxy(demo_session, src_id)
    proxy_id = proxy.get("proxy_id")
    assert proxy_id and proxy_id != src_id, f"expected generated proxy for checks, got: {proxy}"

    src_path = _download_media(demo_session, src_id)
    proxy_path = _download_media(demo_session, proxy_id)
    try:
        src_info = _probe_video_basic(src_path)
        proxy_info = _probe_video_basic(proxy_path)
        assert proxy_info["codec"] == "h264"
        assert min(proxy_info["width"], proxy_info["height"]) <= 720
        assert abs(proxy_info["duration"] - src_info["duration"]) <= 1.2

        gaps = _keyframe_gaps(proxy_path)
        assert gaps, "Could not compute keyframe gaps from ffmpeg output"
        max_gap = max(gaps)
        frame_tol = 1.0 / max(proxy_info["fps"], 1.0)
        assert max_gap <= (0.5 + frame_tol + 0.02), (
            f"proxy keyframe gap too high: {max_gap}s (fps={proxy_info['fps']}, tol={0.5 + frame_tol + 0.02})"
        )
    finally:
        src_path.unlink(missing_ok=True)
        proxy_path.unlink(missing_ok=True)


def test_proxy_requires_auth(uploaded_media: dict):
    media_id = uploaded_media["h264_720"]
    r = requests.post(f"{BASE_URL}/api/media/proxy/{media_id}", timeout=30)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text[:200]}"
