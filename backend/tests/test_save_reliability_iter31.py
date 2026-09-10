"""Quick regression on save reliability (client_id/seq, empty overwrite, admin telemetry)."""
import os
import uuid
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE}/api"

DEMO = ("demo@beatcut.fr", "Demo1234!")
ADMIN = ("julesfar17@gmail.com", "Carnageproduction1704*")


def _login(email, pwd):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=20)
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    return s


def test_client_seq_stale_and_empty_overwrite():
    s = _login(*DEMO)
    cid = f"testcli-{uuid.uuid4().hex[:8]}"
    # Create a non-empty project
    payload = {
        "title": "TEST_save_reliab",
        "state": {
            "plans": [{"id": "p1", "duration": 2}],
            "clipRefs": [{"id": "c1", "mediaId": "fake"}],
            "audioMediaId": "audio-x",
            "words": [{"text": "hello", "start": 0, "end": 1}],
        },
        "client_id": cid,
        "seq": 10,
    }
    r = s.post(f"{API}/projects", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    pid = body.get("id") or body.get("project_id") or body.get("_id")
    assert pid, body
    print("created", pid)

    # Same client_id lower seq -> stale
    r2 = s.post(f"{API}/projects", json={
        "id": pid, "project_id": pid, "title": "should-not-apply",
        "state": payload["state"], "client_id": cid, "seq": 5,
    }, timeout=30)
    assert r2.status_code == 200, r2.text
    assert r2.json().get("stale") is True, f"expected stale, got {r2.json()}"

    # Empty state overwrite -> 409
    r3 = s.post(f"{API}/projects", json={
        "id": pid, "project_id": pid, "title": "TEST_save_reliab",
        "state": {"plans": [], "clipRefs": [], "words": [], "audioMediaId": None},
        "client_id": cid, "seq": 20,
    }, timeout=30)
    assert r3.status_code == 409, f"expected 409 got {r3.status_code} {r3.text}"

    # Force flag bypass -> 200
    r4 = s.post(f"{API}/projects", json={
        "id": pid, "project_id": pid, "title": "TEST_save_reliab",
        "state": {"plans": [], "clipRefs": [], "words": [], "audioMediaId": None},
        "client_id": cid, "seq": 21, "force": True,
    }, timeout=30)
    assert r4.status_code == 200, r4.text

    # Cleanup
    s.delete(f"{API}/projects/{pid}", timeout=20)


def test_admin_save_failures():
    s = _login(*ADMIN)
    r = s.get(f"{API}/admin/telemetry/save-failures?days=7", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "total" in data
    assert "by_reason" in data
    assert "users" in data
    print("save-failures", data.get("total"), "reasons", list((data.get("by_reason") or {}).keys())[:5])


if __name__ == "__main__":
    test_client_seq_stale_and_empty_overwrite()
    print("OK client/seq/empty")
    test_admin_save_failures()
    print("OK admin telemetry")
