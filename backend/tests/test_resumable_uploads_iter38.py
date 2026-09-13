"""Iteration 38 — resumable upload API regression suite.

Modules/features covered:
- /api/media/uploads init/status/chunk/complete/cancel lifecycle
- 4 MiB chunk rules, duplicate/idempotent behavior, owner isolation
- unknown/expired sessions, TTL index presence, max 300 MB guard
"""

from __future__ import annotations

import hashlib
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv(Path("/app/frontend/.env"))
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")

CHUNK = 4 * 1024 * 1024
DEMO_EMAIL = "demo@beatcut.fr"
DEMO_PASSWORD = "Demo1234!"
ADMIN_EMAIL = "admin@beatcut.fr"
ADMIN_PASSWORD = "Admin123!"


def _auth_session(email: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text[:200]}"
    return s


def _init_upload(s: requests.Session, upload_id: uuid.UUID, size: int, filename: str = "qa.bin"):
    return s.post(
        f"{BASE_URL}/api/media/uploads",
        json={
            "upload_id": str(upload_id),
            "filename": filename,
            "size": size,
            "content_type": "application/octet-stream",
        },
        timeout=30,
    )


def _put_chunk(s: requests.Session, upload_id: uuid.UUID, index: int, data: bytes):
    return s.put(
        f"{BASE_URL}/api/media/uploads/{upload_id}/chunks/{index}",
        data=data,
        headers={"Content-Type": "application/octet-stream"},
        timeout=120,
    )


def _status(s: requests.Session, upload_id: uuid.UUID):
    return s.get(f"{BASE_URL}/api/media/uploads/{upload_id}", timeout=30)


def _complete(s: requests.Session, upload_id: uuid.UUID):
    return s.post(f"{BASE_URL}/api/media/uploads/{upload_id}/complete", timeout=180)


def _cancel(s: requests.Session, upload_id: uuid.UUID):
    return s.delete(f"{BASE_URL}/api/media/uploads/{upload_id}", timeout=30)


@pytest.fixture(scope="module")
def owner_session() -> requests.Session:
    return _auth_session(DEMO_EMAIL, DEMO_PASSWORD)


@pytest.fixture(scope="module")
def second_owner_session() -> requests.Session:
    return _auth_session(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def mongo_db():
    load_dotenv(Path("/app/backend/.env"))
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        pytest.skip("MONGO_URL/DB_NAME missing for TTL/expiry checks")
    client = MongoClient(mongo_url)
    try:
        yield client[db_name]
    finally:
        client.close()


def test_init_rejects_300000001_without_upload_body(owner_session: requests.Session):
    upload_id = uuid.uuid4()
    r = _init_upload(owner_session, upload_id, 300_000_001, filename="too_big.bin")
    assert r.status_code == 413, r.text
    detail = (r.json() or {}).get("detail", "")
    assert "300" in detail


def test_auth_required_for_upload_init():
    r = requests.post(
        f"{BASE_URL}/api/media/uploads",
        json={
            "upload_id": str(uuid.uuid4()),
            "filename": "unauth.bin",
            "size": 123,
            "content_type": "application/octet-stream",
        },
        timeout=30,
    )
    assert r.status_code == 401


def test_out_of_order_duplicate_idempotent_complete_and_download_hash(owner_session: requests.Session):
    upload_id = uuid.uuid4()
    size = CHUNK * 2 + 12_345
    r_init = _init_upload(owner_session, upload_id, size, filename="out_of_order.bin")
    assert r_init.status_code == 200, r_init.text
    init_data = r_init.json()
    assert init_data["total_chunks"] == 3
    assert init_data["chunk_size"] == CHUNK

    c0 = b"A" * CHUNK
    c1 = b"B" * CHUNK
    c2 = b"C" * (size - 2 * CHUNK)

    r2 = _put_chunk(owner_session, upload_id, 2, c2)
    assert r2.status_code == 200, r2.text
    assert r2.json()["index"] == 2

    r2_dup = _put_chunk(owner_session, upload_id, 2, c2)
    assert r2_dup.status_code == 200, r2_dup.text

    r0 = _put_chunk(owner_session, upload_id, 0, c0)
    r1 = _put_chunk(owner_session, upload_id, 1, c1)
    assert r0.status_code == 200 and r1.status_code == 200

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_complete, owner_session, upload_id)
        f2 = pool.submit(_complete, owner_session, upload_id)
        rc1, rc2 = f1.result(), f2.result()

    assert rc1.status_code == 200 and rc2.status_code == 200
    b1, b2 = rc1.json(), rc2.json()
    assert b1["status"] in ("finalizing", "complete")
    assert b2["status"] in ("finalizing", "complete")

    final = _complete(owner_session, upload_id)
    assert final.status_code == 200, final.text
    final_data = final.json()
    assert final_data["status"] == "complete"
    assert isinstance(final_data.get("media_id"), str) and final_data["media_id"]

    st = _status(owner_session, upload_id)
    assert st.status_code == 200
    st_data = st.json()
    assert st_data["status"] == "complete"
    assert st_data["received"] == []  # staged parts removed

    media_id = final_data["media_id"]
    dl = owner_session.get(f"{BASE_URL}/api/media/{media_id}", timeout=180)
    assert dl.status_code == 200, dl.text[:200]
    full = c0 + c1 + c2
    assert len(dl.content) == len(full)
    assert hashlib.sha256(dl.content).hexdigest() == hashlib.sha256(full).hexdigest()


def test_conflicting_duplicate_returns_409(owner_session: requests.Session):
    upload_id = uuid.uuid4()
    size = CHUNK
    r_init = _init_upload(owner_session, upload_id, size, filename="conflict.bin")
    assert r_init.status_code == 200

    ok = _put_chunk(owner_session, upload_id, 0, b"X" * CHUNK)
    assert ok.status_code == 200
    conflict = _put_chunk(owner_session, upload_id, 0, b"Y" * CHUNK)
    assert conflict.status_code == 409
    assert "diff" in conflict.text.lower() or "différent" in conflict.text.lower()

    _cancel(owner_session, upload_id)


def test_wrong_size_oversize_invalid_index(owner_session: requests.Session):
    upload_id = uuid.uuid4()
    size = CHUNK + 10
    r_init = _init_upload(owner_session, upload_id, size, filename="sizes.bin")
    assert r_init.status_code == 200

    invalid_neg = _put_chunk(owner_session, upload_id, -1, b"abc")
    invalid_big = _put_chunk(owner_session, upload_id, 9, b"abc")
    assert invalid_neg.status_code == 416
    assert invalid_big.status_code == 416

    oversize = _put_chunk(owner_session, upload_id, 0, b"O" * (CHUNK + 1))
    assert oversize.status_code == 413

    ok_first = _put_chunk(owner_session, upload_id, 0, b"A" * CHUNK)
    assert ok_first.status_code == 200

    short_last = _put_chunk(owner_session, upload_id, 1, b"B" * 9)
    assert short_last.status_code == 400

    _cancel(owner_session, upload_id)


def test_complete_missing_parts_409(owner_session: requests.Session):
    upload_id = uuid.uuid4()
    size = CHUNK * 2
    r_init = _init_upload(owner_session, upload_id, size, filename="missing.bin")
    assert r_init.status_code == 200

    r0 = _put_chunk(owner_session, upload_id, 0, b"M" * CHUNK)
    assert r0.status_code == 200

    done = _complete(owner_session, upload_id)
    assert done.status_code == 409
    assert "manque" in done.text.lower() or "missing" in done.text.lower()

    _cancel(owner_session, upload_id)


def test_unknown_upload_returns_404(owner_session: requests.Session):
    unknown = uuid.uuid4()
    for r in (
        _status(owner_session, unknown),
        _complete(owner_session, unknown),
        _cancel(owner_session, unknown),
        _put_chunk(owner_session, unknown, 0, b"abc"),
    ):
        assert r.status_code == 404


def test_cross_owner_denied_with_404(owner_session: requests.Session, second_owner_session: requests.Session):
    upload_id = uuid.uuid4()
    size = CHUNK
    r_init = _init_upload(owner_session, upload_id, size, filename="owner_only.bin")
    assert r_init.status_code == 200

    foreign_status = _status(second_owner_session, upload_id)
    foreign_put = _put_chunk(second_owner_session, upload_id, 0, b"Z" * CHUNK)
    foreign_complete = _complete(second_owner_session, upload_id)
    foreign_cancel = _cancel(second_owner_session, upload_id)

    assert foreign_status.status_code == 404
    assert foreign_put.status_code == 404
    assert foreign_complete.status_code == 404
    assert foreign_cancel.status_code == 404

    _cancel(owner_session, upload_id)


def test_expired_upload_rejected_and_ttl_indexes_present(owner_session: requests.Session, mongo_db):
    upload_id = uuid.uuid4()
    r_init = _init_upload(owner_session, upload_id, 1024, filename="expired.bin")
    assert r_init.status_code == 200

    # Force expiry and verify API treats it as unknown/expired.
    mongo_db.media_uploads.update_one(
        {"_id": str(upload_id)},
        {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)}},
    )

    assert _status(owner_session, upload_id).status_code == 404
    assert _put_chunk(owner_session, upload_id, 0, b"a").status_code == 404
    assert _cancel(owner_session, upload_id).status_code == 404

    up_idx = mongo_db.media_uploads.index_information()
    part_idx = mongo_db["upload_stage.chunks"].index_information()

    assert any(v.get("expireAfterSeconds") == 0 for v in up_idx.values())
    assert any(v.get("expireAfterSeconds") == 0 for v in part_idx.values())
