import pytest
from api.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture(params=[True, False], ids=["mock", "real"])
def client(request, monkeypatch):
    """Test client fixture.

    Currently only tests MockEngine. When matcher is implemented,
    change params to [True, False] to test both engines.

    Tests both MockEngine and RealEngine.
    """
    use_mock = request.param
    monkeypatch.setenv("USE_MOCK_ENGINE", "1" if use_mock else "0")
    app = create_app()
    return TestClient(app), use_mock


def test_health(client):
    cli, _ = client
    resp = cli.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_match(client):
    cli, use_mock = client
    resp = cli.post(
        "/regex/match",
        json={"pattern": r"\d+", "text": "abc 123 xyz", "flags": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["span"] == [4, 7]


def test_replace(client):
    cli, use_mock = client
    resp = cli.post(
        "/regex/replace",
        json={
            "pattern": r"\d+",
            "text": "abc 123 xyz",
            "flags": "",
            "repl": "#",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"output": "abc # xyz", "count": 1}


def test_split(client):
    cli, use_mock = client
    resp = cli.post(
        "/regex/split",
        json={"pattern": " ", "text": "a b c", "flags": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pieces"] == ["a", "b", "c"]


def test_split_multiple_spaces(client):
    cli, use_mock = client
    resp = cli.post(
        "/regex/split",
        json={"pattern": r"\s+", "text": "a  b   c", "flags": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pieces"] == ["a", "b", "c"]


def test_invalid_pattern_error(client):
    """Test that invalid patterns return proper error responses."""
    cli, use_mock = client
    # Skip for mock engine (it uses Python's re which has different error messages)
    if use_mock:
        return

    # Unmatched parenthesis
    resp = cli.post(
        "/regex/match",
        json={"pattern": "(abc", "text": "abc", "flags": ""},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data["detail"]
    assert "position" in data["detail"]

    # Invalid quantifier
    resp = cli.post(
        "/regex/match",
        json={"pattern": "*abc", "text": "abc", "flags": ""},
    )
    assert resp.status_code == 400


def test_invalid_pattern_in_replace(client):
    """Test that invalid patterns in replace endpoint return errors."""
    cli, use_mock = client
    if use_mock:
        return

    resp = cli.post(
        "/regex/replace",
        json={"pattern": "[abc", "text": "test", "flags": "", "repl": "x"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data["detail"]


def test_invalid_pattern_in_split(client):
    """Test that invalid patterns in split endpoint return errors."""
    cli, use_mock = client
    if use_mock:
        return

    resp = cli.post(
        "/regex/split",
        json={"pattern": "{3,2}", "text": "test", "flags": ""},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data["detail"]
