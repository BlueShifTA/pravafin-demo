from fastapi.testclient import TestClient

from coresat.main import app


def test_echo_endpoint() -> None:
    client = TestClient(app)
    response = client.post("/api/example/echo", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json() == {"message": "hello", "length": 5}
