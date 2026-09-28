from fastapi.testclient import TestClient

from parqueadero.interfaces.cloud.main import create_app as create_cloud_app
from parqueadero.interfaces.local.main import create_app as create_local_app


def test_local_health() -> None:
    client = TestClient(create_local_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "backend": "local"}


def test_cloud_health() -> None:
    client = TestClient(create_cloud_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "backend": "cloud"}
