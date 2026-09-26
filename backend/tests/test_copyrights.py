"""Tests droits d'auteur."""
from fastapi.testclient import TestClient

CR_PAYLOAD = {
    "title": "Algorithme de détection deepfake v2",
    "work_type": "literary",
    "description": "Code source de détection par intelligence artificielle",
    "authors": [{"name": "DeepfakeDetector Inc.", "country": "CA"}],
    "owners": [{"name": "DeepfakeDetector Inc.", "country": "CA"}],
    "is_published": True,
    "is_work_for_hire": False,
}


class TestCopyrightCRUD:
    def test_create_copyright(self, client: TestClient, auth_agent: dict):
        r = client.post("/copyrights", json=CR_PAYLOAD, headers=auth_agent)
        assert r.status_code == 201
        assert r.json()["title"] == CR_PAYLOAD["title"]
        assert r.json()["status"] == "active"
        assert r.json()["work_type"] == "literary"

    def test_list_copyrights(self, client: TestClient, auth_agent: dict):
        client.post("/copyrights", json=CR_PAYLOAD, headers=auth_agent)
        r = client.get("/copyrights", headers=auth_agent)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_copyright(self, client: TestClient, auth_agent: dict):
        created = client.post("/copyrights", json=CR_PAYLOAD, headers=auth_agent).json()
        r = client.get(f"/copyrights/{created['id']}", headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_update_copyright_registration(self, client: TestClient, auth_agent: dict):
        created = client.post("/copyrights", json=CR_PAYLOAD, headers=auth_agent).json()
        r = client.patch(f"/copyrights/{created['id']}", json={
            "registration_number": "1188857",
            "license_type": "MIT",
        }, headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["registration_number"] == "1188857"
        assert r.json()["license_type"] == "MIT"

    def test_get_copyright_not_found(self, client: TestClient, auth_agent: dict):
        r = client.get("/copyrights/99999", headers=auth_agent)
        assert r.status_code == 404

    def test_create_requires_auth(self, client: TestClient):
        r = client.post("/copyrights", json=CR_PAYLOAD)
        assert r.status_code == 401

    def test_list_requires_auth(self, client: TestClient):
        r = client.get("/copyrights")
        assert r.status_code == 401

    def test_viewer_cannot_create(self, client: TestClient, auth_viewer: dict):
        r = client.post("/copyrights", json=CR_PAYLOAD, headers=auth_viewer)
        assert r.status_code == 403
