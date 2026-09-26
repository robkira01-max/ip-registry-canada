"""Brevet — Loi sur les brevets (L.R.C. 1985, ch. P-4) + PCT."""
from __future__ import annotations
import enum
from datetime import date, datetime, timezone
from sqlalchemy import String, Text, Date, DateTime, Boolean, ForeignKey, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class PatentStatus(str, enum.Enum):
    draft      = "draft"       # Brouillon — non déposé
    filed      = "filed"       # Déposé à l'OPIC
    published  = "published"   # Publié (18 mois après dépôt)
    examination = "examination" # En examen
    granted    = "granted"     # Accordé
    abandoned  = "abandoned"   # Abandonné
    expired    = "expired"     # Expiré (20 ans)


class PatentType(str, enum.Enum):
    utility     = "utility"      # Brevet d'invention standard
    divisional  = "divisional"   # Divisionnaire
    continuation = "continuation" # Continuation
    pct         = "pct"          # PCT (Patent Cooperation Treaty)


class Patent(Base):
    """Brevet déposé auprès de l'OPIC.

    Durée de protection : 20 ans à partir de la date de dépôt (art. 44 Loi sur les brevets).
    """
    __tablename__ = "patents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Identifiants officiels ────────────────────────────────────────────────
    application_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    patent_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    pct_number: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # ── Type et statut ────────────────────────────────────────────────────────
    patent_type: Mapped[PatentType] = mapped_column(
        SAEnum(PatentType), nullable=False, default=PatentType.utility
    )
    status: Mapped[PatentStatus] = mapped_column(
        SAEnum(PatentStatus), nullable=False, default=PatentStatus.draft, index=True
    )

    # ── Contenu ───────────────────────────────────────────────────────────────
    title_fr: Mapped[str] = mapped_column(String(512), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(512), nullable=True)
    abstract_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    claims: Mapped[str | None] = mapped_column(Text, nullable=True)
    ipc_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Classification IPC

    # ── Inventeurs et titulaires ──────────────────────────────────────────────
    inventors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"name": "...", "address": "...", "country": "CA"}]
    owners: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ── Dates clés ────────────────────────────────────────────────────────────
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    grant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority_country: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # ── Taxes de maintien ─────────────────────────────────────────────────────
    maintenance_fees_paid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance_fee_due: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Métadonnées ───────────────────────────────────────────────────────────
    is_canadian_origin: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    agent_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cipo_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Traçabilité ───────────────────────────────────────────────────────────
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_patents_status_filing", "status", "filing_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Patent id={self.id} app={self.application_number} "
            f"status={self.status} title={self.title_fr[:40]}>"
        )
