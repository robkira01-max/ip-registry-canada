"""Recherche unifiée à travers tous les types de PI."""
from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.security import get_current_user
from database import get_db
from models.patent import Patent
from models.trademark import Trademark
from models.copyright_ import Copyright
from models.industrial_design import IndustrialDesign
from models.user import User
from models.audit_log import AuditLog, AuditAction

router = APIRouter(prefix="/search", tags=["recherche"])


class SearchResult(BaseModel):
    type: str          # "patent" | "trademark" | "copyright" | "design"
    id: int
    title: str
    status: str
    application_number: str | None = None
    registration_number: str | None = None


@router.get("", response_model=list[SearchResult])
def search_all(
    q: str = Query(..., min_length=2, description="Texte à rechercher"),
    db: Annotated[Session, Depends(get_db)] = ...,
    user: Annotated[User, Depends(get_current_user)] = ...,
    limit: int = Query(20, le=100),
):
    """Recherche plein-texte sur les titres FR/EN de tous les types de PI."""
    results: list[SearchResult] = []
    term = f"%{q}%"

    patents = db.query(Patent).filter(
        or_(Patent.title_fr.ilike(term), Patent.title_en.ilike(term))
    ).limit(limit).all()
    for p in patents:
        results.append(SearchResult(
            type="patent", id=p.id,
            title=p.title_fr,
            status=p.status.value,
            application_number=p.application_number,
            registration_number=p.patent_number,
        ))

    tms = db.query(Trademark).filter(
        or_(Trademark.mark_text.ilike(term), Trademark.description_fr.ilike(term))
    ).limit(limit).all()
    for t in tms:
        results.append(SearchResult(
            type="trademark", id=t.id,
            title=t.mark_text or "(design)",
            status=t.status.value,
            application_number=t.application_number,
            registration_number=t.registration_number,
        ))

    crs = db.query(Copyright).filter(Copyright.title.ilike(term)).limit(limit).all()
    for c in crs:
        results.append(SearchResult(
            type="copyright", id=c.id,
            title=c.title,
            status=c.status.value,
            registration_number=c.registration_number,
        ))

    designs = db.query(IndustrialDesign).filter(IndustrialDesign.title.ilike(term)).limit(limit).all()
    for d in designs:
        results.append(SearchResult(
            type="design", id=d.id,
            title=d.title,
            status=d.status.value,
            application_number=d.application_number,
            registration_number=d.registration_number,
        ))

    db.add(AuditLog(
        action=AuditAction.SEARCH_PERFORMED,
        user_username=user.username,
        details={"query": q, "results": len(results)},
    ))
    db.commit()

    return results[:limit]
