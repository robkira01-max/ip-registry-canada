"""Marque de commerce — Loi sur les marques de commerce (L.R.C. 1985, ch. T-13)."""
from __future__ import annotations
import enum
from datetime import date, datetime, timezone
from sqlalchemy import String, Text, Date, DateTime, Boolean, ForeignKey, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class TrademarkStatus(str, enum.Enum):
    draft       = "draft"
    filed       = "filed"
    advertised  = "advertised"   # Annoncé dans le Journal des marques
    registered  = "registered"   # Enregistré
    abandoned   = "abandoned"
    expired     = "expired"      # 10 ans, renouvelable


class TrademarkType(str, enum.Enum):
    word         = "word"          # Marque verbale
    design       = "design"        # Marque figurative
    word_design  = "word_design"   # Marque mixte
    certification = "certification" # Marque de certification
    distinguishing_guise = "distinguishing_guise"


class Trademark(Base):
    """Marque de commerce enregistrée auprès de l'OPIC.

    Durée de protection : 10 ans à partir de la date d'enregistrement, renouvelable indéfiniment.
    Système de Madrid : couverture internationale via WIPO.
    """
    __tablename__ = "trademarks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Identifiants officiels ────────────────────────────────────────────────
    application_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    madrid_number: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # ── Type et statut ────────────────────────────────────────────────────────
    trademark_type: Mapped[TrademarkType] = mapped_column(
        SAEnum(TrademarkType), nullable=False, default=TrademarkType.word
    )
    status: Mapped[TrademarkStatus] = mapped_column(
        SAEnum(TrademarkStatus), nullable=False, default=TrademarkStatus.draft, index=True
    )

    # ── Contenu ───────────────────────────────────────────────────────────────
    mark_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    nice_classes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Classification de Nice : [{"class": 9, "goods_services": "..."}]
    colors_claimed: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # ── Titulaires ────────────────────────────────────────────────────────────
    owners: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"name": "...", "address": "...", "country": "CA"}]

    # ── Dates clés ────────────────────────────────────────────────────────────
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    advertisement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Uso et distintivité ───────────────────────────────────────────────────
    use_in_canada_since: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_used_in_canada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Métadonnées ───────────────────────────────────────────────────────────
    agent_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cipo_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    design_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

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
        Index("ix_trademarks_status_filing", "status", "filing_date"),
    )

    def __repr__(self) -> str:
        mark = self.mark_text or "(design)"
        return (
            f"<Trademark id={self.id} app={self.application_number} "
            f"status={self.status} mark={mark[:40]}>"
        )
