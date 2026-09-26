"""CRUD Dessins industriels — Loi sur les dessins industriels L.R.C. 1985, ch. I-9."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.security import get_current_user, require_role
from database import get_db
from models.industrial_design import IndustrialDesign, DesignStatus
from models.user import User, UserRole
from models.audit_log import AuditLog, AuditAction

router = APIRouter(prefix="/designs", tags=["designs industriels"])


class DesignCreate(BaseModel):
    title: str
    description: str | None = None
    article_name: str | None = None
    locarno_classes: list[dict] | None = None
    creators: list[dict] | None = None
    owners: list[dict] | None = None
    filing_date: str | None = None
    application_number: str | None = None


class DesignUpdate(BaseModel):
    title: str | None = None
    status: DesignStatus | None = None
    registration_number: str | None = None
    registration_date: str | None = None
    first_renewal_date: str | None = None
    expiry_date: str | None = None
    agent_notes: str | None = None


class DesignResponse(BaseModel):
    id: int
    application_number: str | None
    registration_number: str | None
    status: DesignStatus
    title: str
    article_name: str | None
    locarno_classes: list | None
    creators: list | None
    owners: list | None
    filing_date: str | None
    registration_date: str | None
    expiry_date: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=DesignResponse, status_code=201)
def create_design(
    payload: DesignCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    design = IndustrialDesign(**payload.model_dump(), created_by_id=user.id)
    db.add(design)
    db.add(AuditLog(
        action=AuditAction.DESIGN_CREATED,
        user_username=user.username,
        resource_type="design",
        details={"title": payload.title},
    ))
    db.commit()
    db.refresh(design)
    return design


@router.get("", response_model=list[DesignResponse])
def list_designs(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    status: DesignStatus | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(IndustrialDesign)
    if status:
        q = q.filter(IndustrialDesign.status == status)
    return q.order_by(IndustrialDesign.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{design_id}", response_model=DesignResponse)
def get_design(
    design_id: int,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    design = db.get(IndustrialDesign, design_id)
    if not design:
        raise HTTPException(status_code=404, detail="Dessin industriel introuvable")
    return design


@router.patch("/{design_id}", response_model=DesignResponse)
def update_design(
    design_id: int,
    payload: DesignUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    design = db.get(IndustrialDesign, design_id)
    if not design:
        raise HTTPException(status_code=404, detail="Dessin industriel introuvable")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(design, field, value)
    design.updated_at = datetime.now(timezone.utc)
    action = (
        AuditAction.DESIGN_REGISTERED
        if payload.status == DesignStatus.registered
        else AuditAction.DESIGN_UPDATED
    )
    db.add(AuditLog(
        action=action,
        user_username=user.username,
        resource_type="design",
        resource_id=design_id,
    ))
    db.commit()
    db.refresh(design)
    return design
