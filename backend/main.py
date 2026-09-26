"""Registre IP Canada — Point d'entrée FastAPI.

Plateforme de gestion de la propriété intellectuelle canadienne :
  - Brevets      (Loi sur les brevets L.R.C. 1985, ch. P-4 — 20 ans)
  - Marques      (Loi sur les marques de commerce L.R.C. 1985, ch. T-13 — 10 ans renouvelable)
  - Droits d'auteur (Loi sur le droit d'auteur L.R.C. 1985, ch. C-42 — vie + 70 ans)
  - Dessins industriels (Loi sur les dessins industriels L.R.C. 1985, ch. I-9 — 10 ans max)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import auth, patents, trademarks, copyrights, designs, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Registre IP Canada",
    version=settings.app_version,
    description=(
        "Plateforme de gestion des titres de propriété intellectuelle canadienne. "
        "Conformité OPIC (CIPO), Loi sur les brevets, Loi sur les marques de commerce, "
        "Loi sur le droit d'auteur, Loi sur les dessins industriels."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8083"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patents.router)
app.include_router(trademarks.router)
app.include_router(copyrights.router)
app.include_router(designs.router)
app.include_router(search.router)


@app.get("/health", tags=["infra"])
def health():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/", tags=["infra"])
def root():
    return {
        "service": "Registre IP Canada",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "auth":       "/auth",
            "brevets":    "/patents",
            "marques":    "/trademarks",
            "droits":     "/copyrights",
            "dessins":    "/designs",
            "recherche":  "/search",
        },
    }
