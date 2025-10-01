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
