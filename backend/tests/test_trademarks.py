"""Tests marques de commerce."""
from fastapi.testclient import TestClient

TM_PAYLOAD = {
    "mark_text": "DEEPDETECT",
    "trademark_type": "word",
    "description_fr": "Services de détection de contenu numérique falsifié",
    "nice_classes": [{"class": 42, "goods_services": "Services informatiques et technologiques"}],
    "owners": [{"name": "DeepfakeDetector Inc.", "country": "CA"}],
}


class TestTrademarkCRUD:
    def test_create_trademark(self, client: TestClient, auth_agent: dict):
        r = client.post("/trademarks", json=TM_PAYLOAD, headers=auth_agent)
        assert r.status_code == 201
        assert r.json()["mark_text"] == "DEEPDETECT"
        assert r.json()["status"] == "draft"

    def test_list_trademarks(self, client: TestClient, auth_agent: dict):
        client.post("/trademarks", json=TM_PAYLOAD, headers=auth_agent)
        r = client.get("/trademarks", headers=auth_agent)
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_register_trademark(self, client: TestClient, auth_agent: dict):
        created = client.post("/trademarks", json=TM_PAYLOAD, headers=auth_agent).json()
        r = client.patch(f"/trademarks/{created['id']}", json={
            "status": "registered",
            "registration_number": "TMA123456",
        }, headers=auth_agent)
        assert r.status_code == 200
        assert r.json()["status"] == "registered"
        assert r.json()["registration_number"] == "TMA123456"

    def test_get_trademark_not_found(self, client: TestClient, auth_agent: dict):
        r = client.get("/trademarks/99999", headers=auth_agent)
        assert r.status_code == 404
