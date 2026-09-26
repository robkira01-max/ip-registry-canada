"""Dessin industriel — Loi sur les dessins industriels (L.R.C. 1985, ch. I-9)."""
from __future__ import annotations
import enum
from datetime import date, datetime, timezone
from sqlalchemy import String, Text, Date, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class DesignStatus(str, enum.Enum):
    draft      = "draft"
    filed      = "filed"
    registered = "registered"
    abandoned  = "abandoned"
    expired    = "expired"    # 10 ans, non renouvelable


class IndustrialDesign(Base):
    """Dessin ou modèle industriel enregistré auprès de l'OPIC.

    Protège l'apparence visuelle d'un objet (forme, configuration, motif, ornement).
    Durée : 10 ans maximum (5 ans + 5 ans de renouvellement).
    Classification de Locarno.
    """
    __tablename__ = "industrial_designs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Identifiants officiels ────────────────────────────────────────────────
    application_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    # ── Statut ────────────────────────────────────────────────────────────────
    status: Mapped[DesignStatus] = mapped_column(
        SAEnum(DesignStatus), nullable=False, default=DesignStatus.draft, index=True
    )

    # ── Contenu ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    article_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    locarno_classes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"class": "12-16", "subclass": "...", "description": "..."}]

    # ── Titulaires ────────────────────────────────────────────────────────────
    creators: Mapped[list | None] = mapped_column(JSON, nullable=True)
    owners: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ── Dates clés ────────────────────────────────────────────────────────────
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Fichiers de représentation ────────────────────────────────────────────
    image_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ── Métadonnées ───────────────────────────────────────────────────────────
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

    def __repr__(self) -> str:
        return (
            f"<IndustrialDesign id={self.id} app={self.application_number} "
            f"status={self.status} title={self.title[:40]}>"
        )
