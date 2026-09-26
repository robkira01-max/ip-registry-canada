"""Droit d'auteur — Loi sur le droit d'auteur (L.R.C. 1985, ch. C-42)."""
from __future__ import annotations
import enum
from datetime import date, datetime, timezone
from sqlalchemy import String, Text, Date, DateTime, Boolean, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class CopyrightWorkType(str, enum.Enum):
    literary       = "literary"      # Œuvre littéraire (livre, logiciel, base de données)
    artistic       = "artistic"      # Œuvre artistique (peinture, sculpture, photo)
    musical        = "musical"       # Œuvre musicale
    dramatic       = "dramatic"      # Œuvre dramatique (film, scénario)
    sound_recording = "sound_recording"
    performance    = "performance"
    communication_signal = "communication_signal"


class CopyrightStatus(str, enum.Enum):
    active   = "active"    # Protection en vigueur
    expired  = "expired"   # Domaine public
    disputed = "disputed"  # Litige en cours


class Copyright(Base):
    """Droit d'auteur — enregistrement volontaire à Patrimoine canadien / CIPO.

    Durée de protection : vie de l'auteur + 70 ans (depuis 2022, Loi de mise en œuvre
    de l'ACEUM — anciennement 50 ans).
    L'enregistrement n'est pas obligatoire mais crée une présomption légale.
    """
    __tablename__ = "copyrights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ── Identifiants officiels ────────────────────────────────────────────────
    registration_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    # ── Type et statut ────────────────────────────────────────────────────────
    work_type: Mapped[CopyrightWorkType] = mapped_column(
        SAEnum(CopyrightWorkType), nullable=False, default=CopyrightWorkType.literary
    )
    status: Mapped[CopyrightStatus] = mapped_column(
        SAEnum(CopyrightStatus), nullable=False, default=CopyrightStatus.active, index=True
    )

    # ── Contenu de l'œuvre ────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Auteurs et titulaires ─────────────────────────────────────────────────
    authors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"name": "...", "country": "CA", "year_of_death": null}]
    owners: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_work_for_hire: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Dates clés ────────────────────────────────────────────────────────────
    creation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # Calculé

    # ── Licences ──────────────────────────────────────────────────────────────
    license_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Ex. : "CC BY 4.0", "Tous droits réservés", "Propriétaire"
    license_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
            f"<Copyright id={self.id} reg={self.registration_number} "
            f"type={self.work_type} title={self.title[:40]}>"
        )
