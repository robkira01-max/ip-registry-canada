"""CRUD Droits d'auteur — Loi sur le droit d'auteur L.R.C. 1985, ch. C-42."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.security import get_current_user, require_role
from database import get_db
from models.copyright_ import Copyright, CopyrightStatus, CopyrightWorkType
from models.user import User, UserRole
from models.audit_log import AuditLog, AuditAction

router = APIRouter(prefix="/copyrights", tags=["copyrights"])


class CopyrightCreate(BaseModel):
    title: str
    work_type: CopyrightWorkType = CopyrightWorkType.literary
    description: str | None = None
    authors: list[dict] | None = None
    owners: list[dict] | None = None
    creation_date: str | None = None
    publication_date: str | None = None
    is_published: bool = False
    is_work_for_hire: bool = False
    license_type: str | None = None


class CopyrightUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: CopyrightStatus | None = None
    registration_number: str | None = None
    registration_date: str | None = None
    expiry_date: str | None = None
    license_type: str | None = None
    license_notes: str | None = None
    agent_notes: str | None = None


class CopyrightResponse(BaseModel):
    id: int
    registration_number: str | None
    work_type: CopyrightWorkType
    status: CopyrightStatus
    title: str
    description: str | None
    authors: list | None
    owners: list | None
    creation_date: str | None
    registration_date: str | None
    expiry_date: str | None
    license_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=CopyrightResponse, status_code=201)
def create_copyright(
    payload: CopyrightCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    cr = Copyright(**payload.model_dump(), created_by_id=user.id)
    db.add(cr)
    db.add(AuditLog(
        action=AuditAction.COPYRIGHT_REGISTERED,
        user_username=user.username,
        resource_type="copyright",
        details={"title": payload.title},
    ))
    db.commit()
    db.refresh(cr)
    return cr


@router.get("", response_model=list[CopyrightResponse])
def list_copyrights(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    status: CopyrightStatus | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(Copyright)
    if status:
        q = q.filter(Copyright.status == status)
    return q.order_by(Copyright.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{cr_id}", response_model=CopyrightResponse)
def get_copyright(
    cr_id: int,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    cr = db.get(Copyright, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Droit d'auteur introuvable")
    return cr


@router.patch("/{cr_id}", response_model=CopyrightResponse)
def update_copyright(
    cr_id: int,
    payload: CopyrightUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    cr = db.get(Copyright, cr_id)
    if not cr:
        raise HTTPException(status_code=404, detail="Droit d'auteur introuvable")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(cr, field, value)
    cr.updated_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        action=AuditAction.COPYRIGHT_UPDATED,
        user_username=user.username,
        resource_type="copyright",
        resource_id=cr_id,
    ))
    db.commit()
    db.refresh(cr)
    return cr
