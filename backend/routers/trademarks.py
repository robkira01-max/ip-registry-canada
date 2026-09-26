"""CRUD Marques de commerce — Loi sur les marques de commerce L.R.C. 1985, ch. T-13."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.security import get_current_user, require_role
from database import get_db
from models.trademark import Trademark, TrademarkStatus, TrademarkType
from models.user import User, UserRole
from models.audit_log import AuditLog, AuditAction

router = APIRouter(prefix="/trademarks", tags=["trademarks"])


class TrademarkCreate(BaseModel):
    mark_text: str | None = None
    trademark_type: TrademarkType = TrademarkType.word
    description_fr: str | None = None
    description_en: str | None = None
    nice_classes: list[dict] | None = None
    owners: list[dict] | None = None
    filing_date: str | None = None
    application_number: str | None = None
    use_in_canada_since: str | None = None


class TrademarkUpdate(BaseModel):
    mark_text: str | None = None
    status: TrademarkStatus | None = None
    registration_number: str | None = None
    registration_date: str | None = None
    renewal_date: str | None = None
    expiry_date: str | None = None
    nice_classes: list[dict] | None = None
    agent_notes: str | None = None


class TrademarkResponse(BaseModel):
    id: int
    application_number: str | None
    registration_number: str | None
    madrid_number: str | None
    trademark_type: TrademarkType
    status: TrademarkStatus
    mark_text: str | None
    description_fr: str | None
    nice_classes: list | None
    owners: list | None
    filing_date: str | None
    registration_date: str | None
    expiry_date: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=TrademarkResponse, status_code=201)
def create_trademark(
    payload: TrademarkCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    tm = Trademark(**payload.model_dump(), created_by_id=user.id)
    db.add(tm)
    db.add(AuditLog(
        action=AuditAction.TRADEMARK_CREATED,
        user_username=user.username,
        resource_type="trademark",
        details={"mark": payload.mark_text},
    ))
    db.commit()
    db.refresh(tm)
    return tm


@router.get("", response_model=list[TrademarkResponse])
def list_trademarks(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    status: TrademarkStatus | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(Trademark)
    if status:
        q = q.filter(Trademark.status == status)
    return q.order_by(Trademark.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{tm_id}", response_model=TrademarkResponse)
def get_trademark(
    tm_id: int,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
):
    tm = db.get(Trademark, tm_id)
    if not tm:
        raise HTTPException(status_code=404, detail="Marque introuvable")
    return tm


@router.patch("/{tm_id}", response_model=TrademarkResponse)
def update_trademark(
    tm_id: int,
    payload: TrademarkUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.admin, UserRole.agent))],
):
    tm = db.get(Trademark, tm_id)
    if not tm:
        raise HTTPException(status_code=404, detail="Marque introuvable")

    changes = payload.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(tm, field, value)
    tm.updated_at = datetime.now(timezone.utc)

    action = (
        AuditAction.TRADEMARK_REGISTERED
        if payload.status == TrademarkStatus.registered
        else AuditAction.TRADEMARK_UPDATED
    )
    db.add(AuditLog(
        action=action,
        user_username=user.username,
        resource_type="trademark",
        resource_id=tm_id,
        details={"changes": list(changes.keys())},
    ))
    db.commit()
    db.refresh(tm)
    return tm
