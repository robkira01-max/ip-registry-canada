"""CRUD Brevets — Loi sur les brevets L.R.C. 1985, ch. P-4."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.security import get_current_user, require_role
from database import get_db
from models.patent import Patent, PatentStatus, PatentType
from models.user import User, UserRole
from models.audit_log import AuditLog, AuditAction

router = APIRouter(prefix="/patents", tags=["patents"])


# ── Schémas ───────────────────────────────────────────────────────────────────

class PatentCreate(BaseModel):
    title_fr: str
    title_en: str | None = None
    abstract_fr: str | None = None
    abstract_en: str | None = None
    patent_type: PatentType = PatentType.utility
    inventors: list[dict] | None = None
    owners: list[dict] | None = None
    ipc_codes: list[str] | None = None
    filing_date: str | None = None
    priority_date: str | None = None
    priority_country: str | None = None
    application_number: str | None = None
    pct_number: str | None = None


class PatentUpdate(BaseModel):
    title_fr: str | None = None
    title_en: str | None = None
    abstract_fr: str | None = None
    abstract_en: str | None = None
    status: PatentStatus | None = None
    application_number: str | None = None
    patent_number: str | None = None
    grant_date: str | None = None
    expiry_date: str | None = None
    ipc_codes: list[str] | None = None
    claims: str | None = None
    agent_notes: str | None = None


class PatentResponse(BaseModel):
    id: int
    application_number: str | None
    patent_number: str | None
    pct_number: str | None
    patent_type: PatentType
    status: PatentStatus
    title_fr: str
    title_en: str | None
    abstract_fr: str | None
    inventors: list | None
    owners: list | None
    ipc_codes: list | None
    filing_date: str | None
    grant_date: str | None
    expiry_date: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=PatentResponse, status_code=201)
def create_patent(
    payload: PatentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    patent = Patent(**payload.model_dump(), created_by_id=user.id)
    db.add(patent)
    db.add(AuditLog(
        action=AuditAction.PATENT_CREATED,
        user_username=user.username,
        resource_type="patent",
        details={"title": payload.title_fr},
    ))
    db.commit()
    db.refresh(patent)
    return patent


@router.get("", response_model=list[PatentResponse])
def list_patents(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    status: PatentStatus | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(Patent)
    if status:
        q = q.filter(Patent.status == status)
    return q.order_by(Patent.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{patent_id}", response_model=PatentResponse)
def get_patent(
    patent_id: int,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    patent = db.get(Patent, patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail="Brevet introuvable")
    return patent


@router.patch("/{patent_id}", response_model=PatentResponse)
def update_patent(
    patent_id: int,
    payload: PatentUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    patent = db.get(Patent, patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail="Brevet introuvable")

    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(patent, field, value)
    patent.updated_at = datetime.now(timezone.utc)

    action = AuditAction.PATENT_GRANTED if payload.status == PatentStatus.granted else AuditAction.PATENT_UPDATED
    db.add(AuditLog(
        action=action,
        user_username=user.username,
        resource_type="patent",
        resource_id=patent_id,
        details={"changes": list(changes.keys())},
    ))
    db.commit()
    db.refresh(patent)
    return patent


@router.delete("/{patent_id}", status_code=204)
def abandon_patent(
    patent_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin))],
):
    patent = db.get(Patent, patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail="Brevet introuvable")
    patent.status = PatentStatus.abandoned
    patent.updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        action=AuditAction.PATENT_ABANDONED,
        user_username=user.username,
        resource_type="patent",
        resource_id=patent_id,
    ))
    db.commit()
