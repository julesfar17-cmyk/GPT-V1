"""Tests for server-side thumbnails (veed.io model) - sprite filmstrip."""
import os
import time
import subprocess
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://pro-mailer-2.preview.emergentagent.com").rstrip("/")
DEMO_EMAIL = "demo@beatcut.fr"
DEMO_PWD = "Demo1234!"
VID_PATH = "/tmp/testvid.mp4"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PWD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def audio_path(tmp_path_factory):
    p = str(tmp_path_factory.mktemp("aud") / "beep.mp3")
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = "ffmpeg"
    subprocess.run(
        [ff, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-b:a", "64k", p],
        check=True, capture_output=True,
    )
    return p


def _poll_thumbs(sess, media_id, timeout=25):
    """Poll /thumbs endpoint until 200 or timeout. Returns final response."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = sess.get(f"{BASE_URL}/api/media/{media_id}/thumbs", timeout=30)
        last = r
        if r.status_code == 200:
            return r
        if r.status_code not in (202, 404, 500):
            return r
        if r.status_code == 404:
            # not-a-video final state
            return r
        time.sleep(1.5)
    return last


def test_video_upload_and_thumbs_sprite(session):
    """Upload testvid → verify sprite JPEG 16 frames + correct headers."""
    with open(VID_PATH, "rb") as f:
        r = session.post(
            f"{BASE_URL}/api/media/upload",
            files={"file": ("testvid.mp4", f, "video/mp4")},
            timeout=60,
        )
    assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    media_id = data.get("id") or data.get("media_id") or data.get("_id")
    assert media_id, f"No media id in {data}"

    r2 = _poll_thumbs(session, media_id, timeout=25)
    assert r2.status_code == 200, f"Thumbs never ready: {r2.status_code} {r2.text[:200]}"
    assert r2.headers.get("Content-Type", "").startswith("image/jpeg"), r2.headers
    count = int(r2.headers.get("X-Thumb-Count", "0"))
    duration = float(r2.headers.get("X-Thumb-Duration", "0"))
    assert count == 16, f"expected 16 frames, got {count}"
    assert 7.0 <= duration <= 9.5, f"expected ~8s, got {duration}"
    # Content length sanity — sprite JPEG should be > 5KB
    assert len(r2.content) > 5000


def test_thumbs_unauthenticated_returns_401():
    r = requests.get(f"{BASE_URL}/api/media/000000000000000000000000/thumbs", timeout=15)
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


def test_thumbs_on_audio_media_returns_404(session, audio_path):
    with open(audio_path, "rb") as f:
        r = session.post(
            f"{BASE_URL}/api/media/upload",
            files={"file": ("beep.mp3", f, "audio/mpeg")},
            timeout=60,
        )
    assert r.status_code == 200, r.text
    mid = r.json().get("id") or r.json().get("media_id")
    assert mid
    # Poll — should eventually 404 (not a video)
    r2 = _poll_thumbs(session, mid, timeout=15)
    assert r2.status_code == 404, f"expected 404 for audio, got {r2.status_code} {r2.text[:200]}"


def test_thumbs_on_existing_video_media_auto_generates(session):
    """Trouver un ancien média vidéo du compte démo et vérifier auto-génération."""
    r = session.get(f"{BASE_URL}/api/media/mine", timeout=30)
    assert r.status_code == 200, r.text
    items = r.json()
    if isinstance(items, dict):
        items = items.get("items") or items.get("media") or []
    video_items = [m for m in items if (m.get("kind") == "video" or (m.get("mime") or m.get("content_type") or "").startswith("video/"))]
    if not video_items:
        pytest.skip("Aucun média vidéo existant sur le compte demo")
    # pick one that's not the freshly uploaded testvid (any will work)
    mid = video_items[0].get("id") or video_items[0].get("_id") or video_items[0].get("media_id")
    assert mid
    r2 = _poll_thumbs(session, mid, timeout=25)
    assert r2.status_code == 200, f"Auto-thumbs failed: {r2.status_code} {r2.text[:200]}"
    assert r2.headers.get("Content-Type", "").startswith("image/jpeg")
    assert int(r2.headers.get("X-Thumb-Count", "0")) >= 8
