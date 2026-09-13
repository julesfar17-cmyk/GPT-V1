"""Iteration 36 — project persistence checks for Tap Lyrics timing payloads."""

import os
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv('/app/frontend/.env')
BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')

DEMO_EMAIL = 'demo@beatcut.fr'
DEMO_PASSWORD = 'Demo1234!'


@pytest.fixture(scope='module')
def demo_session():
    """Authenticated demo session reused across project persistence tests."""
    session = requests.Session()
    login = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        timeout=20,
    )
    assert login.status_code == 200, login.text
    yield session


@pytest.fixture
def disposable_project(demo_session):
    """Disposable project lifecycle for create/get/update/delete assertions."""
    state = {
        "format": "916",
        "ext": {"start": 3.0, "dur": 2.0},
        "words": [
            {"text": "Avant", "start": 1.0, "end": 2.0, "hardEnd": True},
            {
                "text": "salut",
                "start": 3.1,
                "end": 3.55,
                "hardEnd": True,
                "emphasis": {"color": "#ff2d55", "weight": 700},
            },
            {"text": "monde", "start": 3.55, "end": 4.2, "hardEnd": True},
            {"text": "Après", "start": 7.0, "end": 8.0, "hardEnd": True},
        ],
        "cuts": [{"time": 3.0, "source": "manual"}, {"time": 3.55, "source": "manual"}],
        "plans": [
            {"start": 3.0, "end": 3.55, "clip": None, "seek": 0, "locked": False},
            {"start": 3.55, "end": 5.0, "clip": None, "seek": 0, "locked": False},
        ],
    }
    create = demo_session.post(
        f"{BASE_URL}/api/projects",
        json={
            "title": f"QA_DISPOSABLE_TAPLYRICS_{uuid.uuid4().hex[:8]}",
            "state": state,
            "client_id": 'iter36-persistence',
            "seq": 1,
        },
        timeout=30,
    )
    assert create.status_code == 200, create.text
    project_id = create.json()['project_id']
    try:
        yield project_id, state
    finally:
        demo_session.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=30)


def test_create_then_get_project_persists_taplyrics_state(disposable_project, demo_session):
    project_id, initial_state = disposable_project
    got = demo_session.get(f"{BASE_URL}/api/projects/{project_id}", timeout=20)
    assert got.status_code == 200, got.text
    payload = got.json()
    assert payload['project_id'] == project_id
    assert payload['state']['ext']['start'] == initial_state['ext']['start']
    assert payload['state']['words'][1]['text'] == 'salut'
    assert payload['state']['words'][1]['emphasis']['color'] == '#ff2d55'
    assert payload['state']['words'][2]['hardEnd'] is True


def test_update_then_get_project_preserves_outside_excerpt_words(disposable_project, demo_session):
    project_id, _ = disposable_project
    updated_words = [
        {"text": "Avant", "start": 1.0, "end": 2.0, "hardEnd": True},
        {
            "text": "salut",
            "start": 3.12,
            "end": 3.62,
            "hardEnd": True,
            "emphasis": {"color": "#ff2d55", "weight": 700},
        },
        {"text": "monde", "start": 3.62, "end": 4.9, "hardEnd": True},
        {"text": "Après", "start": 7.0, "end": 8.0, "hardEnd": True},
    ]
    update_state = {
        "format": "916",
        "ext": {"start": 3.0, "dur": 2.0},
        "words": updated_words,
        "cuts": [{"time": 3.12, "source": "manual"}, {"time": 3.62, "source": "manual"}],
        "plans": [
            {"start": 3.12, "end": 3.62, "clip": None, "seek": 0, "locked": False},
            {"start": 3.62, "end": 5.0, "clip": None, "seek": 0, "locked": False},
        ],
    }
    save = demo_session.post(
        f"{BASE_URL}/api/projects",
        json={
            "project_id": project_id,
            "title": 'QA_DISPOSABLE_TAPLYRICS_UPDATED',
            "state": update_state,
            "client_id": 'iter36-persistence',
            "seq": 2,
        },
        timeout=30,
    )
    assert save.status_code == 200, save.text

    got = demo_session.get(f"{BASE_URL}/api/projects/{project_id}", timeout=20)
    assert got.status_code == 200, got.text
    words = got.json()['state']['words']
    assert words[0]['text'] == 'Avant'
    assert words[0]['start'] == 1.0
    assert words[-1]['text'] == 'Après'
    assert words[-1]['start'] == 7.0
    assert words[1]['emphasis']['weight'] == 700
    assert all(w['end'] > w['start'] for w in words)


def test_delete_then_get_returns_404(demo_session):
    create = demo_session.post(
        f"{BASE_URL}/api/projects",
        json={
            "title": f"QA_DISPOSABLE_DELETE_{uuid.uuid4().hex[:8]}",
            "state": {"words": [], "plans": [], "cuts": []},
            "client_id": 'iter36-delete',
            "seq": 1,
        },
        timeout=30,
    )
    assert create.status_code == 200, create.text
    project_id = create.json()['project_id']

    deleted = demo_session.delete(f"{BASE_URL}/api/projects/{project_id}", timeout=20)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()['message'] == 'Projet supprimé'

    got = demo_session.get(f"{BASE_URL}/api/projects/{project_id}", timeout=20)
    assert got.status_code == 404
