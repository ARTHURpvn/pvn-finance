"""Testes do healthcheck (CA-2) sem dependência de banco real."""

from fastapi.testclient import TestClient

from app.api import health
from app.main import app


class _FakeConn:
    def __init__(self, *, fail: bool) -> None:
        self._fail = fail

    def execute(self, *_args: object) -> None:
        if self._fail:
            raise RuntimeError("db down")

    def __enter__(self) -> "_FakeConn":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


class _FakeEngine:
    def __init__(self, *, fail: bool) -> None:
        self._fail = fail

    def connect(self) -> _FakeConn:
        return _FakeConn(fail=self._fail)


def test_health_ok(monkeypatch) -> None:
    monkeypatch.setattr(health, "get_engine", lambda: _FakeEngine(fail=False))
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "up"}


def test_health_db_down_returns_503(monkeypatch) -> None:
    monkeypatch.setattr(health, "get_engine", lambda: _FakeEngine(fail=True))
    resp = TestClient(app).get("/health")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "db_unavailable"
