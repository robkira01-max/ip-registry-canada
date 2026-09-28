.PHONY: help keys env build up down logs test migrate admin

help:
	@echo "Registre IP Canada — commandes disponibles"
	@echo ""
	@echo "  make keys     Générer les clés RSA-4096 JWT"
	@echo "  make env      Créer .env depuis .env.example"
	@echo "  make build    Construire l'image Docker"
	@echo "  make up       Démarrer tous les services"
	@echo "  make down     Arrêter tous les services"
	@echo "  make logs     Voir les logs (api)"
	@echo "  make migrate  Appliquer les migrations Alembic"
	@echo "  make test     Lancer la suite de tests"
	@echo "  make admin    Créer le compte administrateur"

keys:
	@mkdir -p keys
	openssl genrsa -traditional -out keys/private.pem 2048
	openssl rsa -in keys/private.pem -pubout -out keys/public.pem
	@echo "Clés PKCS#1 RSA-2048 générées dans keys/"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env créé — modifie les mots de passe avant de démarrer"; \
	else \
		echo ".env existe déjà"; \
	fi

build:
	docker compose build

up: env
	docker compose up -d
	@echo "API disponible sur http://localhost:8083"
	@echo "Docs     : http://localhost:8083/docs"
	@echo "Nginx    : http://localhost:80"

down:
	docker compose down

logs:
	docker compose logs -f api

migrate:
	docker compose exec api alembic upgrade head

test:
	cd backend && source ../.venv/bin/activate && python -m pytest tests/ -q

admin:
	docker compose exec api python scripts/create_admin.py
