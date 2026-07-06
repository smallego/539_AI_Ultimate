from fastapi.testclient import TestClient

from web.app import app


def client():
    return TestClient(app)


def assert_ok(response):
    assert response.status_code == 200, response.text
    return response.json()
