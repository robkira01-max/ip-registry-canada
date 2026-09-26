"""Tests recherche unifiée."""
from fastapi.testclient import TestClient


class TestSearch:
    def test_search_finds_patent(self, client: TestClient, auth_agent: dict):
        client.post("/patents", json={
            "title_fr": "Procédé de chiffrement quantique avancé",
            "patent_type": "utility",
        }, headers=auth_agent)
        r = client.get("/search?q=chiffrement", headers=auth_agent)
        assert r.status_code == 200
        results = r.json()
        types = [x["type"] for x in results]
        assert "patent" in types

    def test_search_finds_trademark(self, client: TestClient, auth_agent: dict):
        client.post("/trademarks", json={
            "mark_text": "QUANTUMSHIELD",
            "trademark_type": "word",
        }, headers=auth_agent)
        r = client.get("/search?q=QUANTUMSHIELD", headers=auth_agent)
        assert r.status_code == 200
        types = [x["type"] for x in r.json()]
        assert "trademark" in types

    def test_search_requires_auth(self, client: TestClient):
        r = client.get("/search?q=test")
        assert r.status_code == 401

    def test_search_min_length(self, client: TestClient, auth_agent: dict):
        r = client.get("/search?q=a", headers=auth_agent)
        assert r.status_code == 422

    def test_search_no_results(self, client: TestClient, auth_agent: dict):
        r = client.get("/search?q=xyzabc123_inexistant", headers=auth_agent)
        assert r.status_code == 200
        assert r.json() == []
