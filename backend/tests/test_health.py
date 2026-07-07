import pytest


@pytest.mark.django_db(transaction=True)
def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
