"""Iter 29 — DELETE /api/auth/account + textes trial 7 jours."""
import os, uuid, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://pro-mailer-2.preview.emergentagent.com").rstrip("/")


def _rand_email():
    return f"deltest_{uuid.uuid4().hex[:10]}@test.fr"


def test_delete_account_unauthenticated():
    r = requests.delete(f"{BASE}/api/auth/account")
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code} {r.text}"


def test_full_delete_account_flow():
    s = requests.Session()
    email = _rand_email()
    pw = "Testing1234!"
    # register
    r = s.post(f"{BASE}/api/auth/register", json={"name": "Del Test", "email": email, "password": pw, "cgv_accepted": True})
    assert r.status_code in (200, 201), f"register failed {r.status_code} {r.text}"
    # me
    r = s.get(f"{BASE}/api/auth/me")
    assert r.status_code == 200, f"me failed {r.status_code}"
    # optional project
    proj = s.post(f"{BASE}/api/projects", json={"name": "TEST_del_proj"})
    # not asserting since schema unknown; just log
    print("project create:", proj.status_code)
    # delete
    r = s.delete(f"{BASE}/api/auth/account")
    assert r.status_code == 200, f"delete failed {r.status_code} {r.text}"
    data = r.json()
    assert "message" in data
    # login should fail
    s2 = requests.Session()
    r = s2.post(f"{BASE}/api/auth/login", json={"email": email, "password": pw})
    assert r.status_code in (400, 401, 404), f"login of deleted account returned {r.status_code}"


def test_trial_texts_no_3_days_in_quota():
    # login as demo to get quota
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": "demo@beatcut.fr", "password": "Demo1234!"})
    assert r.status_code == 200
    r = s.get(f"{BASE}/api/export/quota")
    assert r.status_code == 200
    body = r.text
    # ensure no leftover "3 jours" / "3 days" mention
    assert "3 jours" not in body and "3 days" not in body, f"trial 3-day text still present: {body[:400]}"
