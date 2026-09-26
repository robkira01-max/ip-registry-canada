"""Tests brevets — CRUD complet."""
from fastapi.testclient import TestClient
from models.user import User


PATENT_PAYLOAD = {
    "title_fr": "Système de détection deepfake par réseau neuronal",
    "title_en": "Neural network deepfake detection system",
    "patent_type": "utility",
    "inventors": [{"name": "Jane Tremblay", "country": "CA"}],
    "owners": [{"name": "DeepfakeDetector Inc.", "country": "CA"}],
    "ipc_codes": ["G06N 3/04", "G06V 40/16"],
}


class TestPatentCRUD:
    def test_create_patent_as_agent(self, client: TestClient, auth_agent: dict):
        r = client.post("/patents", json=PATENT_PAYLOAD, headers=auth_agent)
        assert r.status_code == 201
        data = r.json()
        assert data["title_fr"] == PATENT_PAYLOAD["title_fr"]
        assert data["status"] == "draft"
        assert data["patent_type"] == "utility"

    def test_create_patent_as_readonly_forbidden(self, client: TestClient, db, readonly_user: User):
        from core.security import create_access_token
        token = create_access_token(readonly_user.username, readonly_user.role.value)
        r = client.post("/patents", json=PATENT_PAYLOAD,
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_list_patents(self, client: TestClient, auth_agent: dict):
        client.post("/patents", json=PATENT_PAYLOAD, headers=auth_agent)
        r = client.get("/patents", headers=auth_agent)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_get_patent(self, client: TestClient, auth_agent: dict):
        created = client.post("/patents", json=PATENT_PAYLOAD, headers=auth_agent).json()
        r = client.get(f"/patents/{created['id']}", headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_patent_not_found(self, client: TestClient, auth_agent: dict):
        r = client.get("/patents/99999", headers=auth_agent)
        assert r.status_code == 404

    def test_update_patent_status(self, client: TestClient, auth_agent: dict):
        created = client.post("/patents", json=PATENT_PAYLOAD, headers=auth_agent).json()
        r = client.patch(f"/patents/{created['id']}",
                         json={"status": "filed", "application_number": "CA3210001"},
                         headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["status"] == "filed"
        assert r.json()["application_number"] == "CA3210001"

    def test_abandon_patent_as_admin(self, client: TestClient, auth_agent: dict, auth_admin: dict):
        created = client.post("/patents", json=PATENT_PAYLOAD, headers=auth_agent).json()
        r = client.delete(f"/patents/{created['id']}", headers=auth_admin)
        assert r.status_code == 204
        # Vérifier que le statut est "abandoned" (pas supprimé physiquement)
        r2 = client.get(f"/patents/{created['id']}", headers=auth_agent)
        assert r2.json()["status"] == "abandoned"

    def test_filter_by_status(self, client: TestClient, auth_agent: dict):
        client.post("/patents", json=PATENT_PAYLOAD, headers=auth_agent)
        r = client.get("/patents?status=draft", headers=auth_agent)
        assert r.status_code == 200
        for p in r.json():
            assert p["status"] == "draft"
