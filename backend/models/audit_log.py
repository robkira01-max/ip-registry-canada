"""Journal d'audit — traçabilité des actions sur les titres PI."""
from __future__ import annotations
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class AuditAction(str, enum.Enum):
    # Auth
    USER_LOGIN        = "USER_LOGIN"
    USER_LOGOUT       = "USER_LOGOUT"
    USER_CREATED      = "USER_CREATED"
    LOGIN_FAILED      = "LOGIN_FAILED"
    # Brevets
    PATENT_CREATED    = "PATENT_CREATED"
    PATENT_UPDATED    = "PATENT_UPDATED"
    PATENT_PUBLISHED  = "PATENT_PUBLISHED"
    PATENT_GRANTED    = "PATENT_GRANTED"
    PATENT_ABANDONED  = "PATENT_ABANDONED"
    # Marques
    TRADEMARK_CREATED   = "TRADEMARK_CREATED"
    TRADEMARK_UPDATED   = "TRADEMARK_UPDATED"
    TRADEMARK_PUBLISHED = "TRADEMARK_PUBLISHED"
    TRADEMARK_REGISTERED = "TRADEMARK_REGISTERED"
    TRADEMARK_ABANDONED  = "TRADEMARK_ABANDONED"
    # Droits d'auteur
    COPYRIGHT_REGISTERED = "COPYRIGHT_REGISTERED"
    COPYRIGHT_UPDATED    = "COPYRIGHT_UPDATED"
    # Dessins industriels
    DESIGN_CREATED    = "DESIGN_CREATED"
    DESIGN_UPDATED    = "DESIGN_UPDATED"
    DESIGN_REGISTERED = "DESIGN_REGISTERED"
    # Documents
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_DELETED  = "DOCUMENT_DELETED"
    # Recherche
    SEARCH_PERFORMED  = "SEARCH_PERFORMED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    action: Mapped[AuditAction] = mapped_column(SAEnum(AuditAction), nullable=False, index=True)
    user_username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resource_id: Mapped[int | None] = mapped_column(nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} user={self.user_username}>"
