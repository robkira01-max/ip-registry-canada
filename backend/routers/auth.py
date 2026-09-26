"""Authentification — login / logout / utilisateurs."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.security import (
    create_access_token, hash_password, verify_password,
    get_current_user, require_role,
)
from database import get_db
from models.user import User, UserRole
from models.audit_log import AuditLog, AuditAction

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schémas ───────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.readonly


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        db.add(AuditLog(
            action=AuditAction.LOGIN_FAILED,
            user_username=form.username,
            details={"reason": "invalid credentials"},
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    user.last_login = datetime.now(timezone.utc)
    db.add(AuditLog(
        action=AuditAction.USER_LOGIN,
        user_username=user.username,
    ))
    db.commit()

    token = create_access_token(user.username, user.role.value)
    return TokenResponse(access_token=token, role=user.role.value)


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role(UserRole.admin))],
):
    if db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first():
        raise HTTPException(status_code=409, detail="Nom d'utilisateur ou email déjà utilisé")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.add(AuditLog(
        action=AuditAction.USER_CREATED,
        user_username=_admin.username,
        details={"new_user": payload.username, "role": payload.role.value},
    ))
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_role(UserRole.admin))],
):
    return db.query(User).all()
