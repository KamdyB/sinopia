from datetime import timedelta

from backend.api import retention as retention_api
from backend.timeutil import service_date


class FakeTeamStore:
    def list_team_ids(self):
        return ["team-a", "team-b"]


class FakeRetentionStore:
    def __init__(self, per_team):
        self.per_team = per_team
        self.calls = []

    def purge_before(self, cutoff_date, team_id):
        self.calls.append((cutoff_date, team_id))
        return self.per_team[team_id]


def test_retention_endpoint_requires_cron_secret(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "retention-test-secret-which-is-long-enough-123456")
    monkeypatch.setenv("SINOPIA_RETENTION_DAYS", "90")
    response = client.get("/internal/retention/purge")
    assert response.status_code == 403


def test_retention_endpoint_fails_closed_without_policy(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "retention-test-secret-which-is-long-enough-123456")
    monkeypatch.delenv("SINOPIA_RETENTION_DAYS", raising=False)
    response = client.get(
        "/internal/retention/purge",
        headers={"Authorization": "Bearer retention-test-secret-which-is-long-enough-123456"},
    )
    assert response.status_code == 503


def test_retention_endpoint_purges_expired_records_team_by_team(client, monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "retention-test-secret-which-is-long-enough-123456")
    monkeypatch.setenv("SINOPIA_RETENTION_DAYS", "90")
    sessions = FakeRetentionStore({"team-a": 2, "team-b": 1})
    checkins = FakeRetentionStore({"team-a": 1, "team-b": 4})
    monkeypatch.setattr(retention_api, "auth_store", FakeTeamStore())
    monkeypatch.setattr(retention_api, "session_store", sessions)
    monkeypatch.setattr(retention_api, "checkin_store", checkins)

    response = client.get(
        "/internal/retention/purge",
        headers={"Authorization": "Bearer retention-test-secret-which-is-long-enough-123456"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "cutoff_date": (service_date() - timedelta(days=90)).isoformat(),
        "deleted_sessions": 3,
        "deleted_checkins": 5,
    }
    assert [team for _, team in sessions.calls] == ["team-a", "team-b"]
    assert [team for _, team in checkins.calls] == ["team-a", "team-b"]
