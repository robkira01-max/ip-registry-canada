"""Tests dessins industriels."""
from fastapi.testclient import TestClient

DESIGN_PAYLOAD = {
    "title": "Interface utilisateur OSINT Sentinelle",
    "description": "Disposition visuelle du tableau de bord d'analyse OSINT",
    "article_name": "Logiciel de tableau de bord",
    "locarno_classes": [{"class": "14-02", "description": "Interfaces graphiques"}],
    "creators": [{"name": "Robleh Hassan Abdi", "country": "CA"}],
    "owners": [{"name": "SentinelleNord Inc.", "country": "CA"}],
}


class TestDesignCRUD:
    def test_create_design(self, client: TestClient, auth_agent: dict):
        r = client.post("/designs", json=DESIGN_PAYLOAD, headers=auth_agent)
        assert r.status_code == 201
        assert r.json()["title"] == DESIGN_PAYLOAD["title"]
        assert r.json()["status"] == "draft"

    def test_list_designs(self, client: TestClient, auth_agent: dict):
        client.post("/designs", json=DESIGN_PAYLOAD, headers=auth_agent)
        r = client.get("/designs", headers=auth_agent)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_design(self, client: TestClient, auth_agent: dict):
        created = client.post("/designs", json=DESIGN_PAYLOAD, headers=auth_agent).json()
        r = client.get(f"/designs/{created['id']}", headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_register_design(self, client: TestClient, auth_agent: dict):
        created = client.post("/designs", json=DESIGN_PAYLOAD, headers=auth_agent).json()
        r = client.patch(f"/designs/{created['id']}", json={
            "status": "registered",
            "registration_number": "CA-166832",
        }, headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["status"] == "registered"
        assert r.json()["registration_number"] == "CA-166832"

    def test_update_design_notes(self, client: TestClient, auth_agent: dict):
        created = client.post("/designs", json=DESIGN_PAYLOAD, headers=auth_agent).json()
        r = client.patch(f"/designs/{created['id']}", json={
            "agent_notes": "Dossier en cours d'examen CIPO",
        }, headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_design_not_found(self, client: TestClient, auth_agent: dict):
        r = client.get("/designs/99999", headers=auth_agent)
        assert r.status_code == 404

    def test_create_requires_auth(self, client: TestClient):
        r = client.post("/designs", json=DESIGN_PAYLOAD)
        assert r.status_code == 401

    def test_viewer_cannot_create(self, client: TestClient, auth_viewer: dict):
        r = client.post("/designs", json=DESIGN_PAYLOAD, headers=auth_viewer)
        assert r.status_code == 403
