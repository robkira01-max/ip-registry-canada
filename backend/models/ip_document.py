"""Document associé à un titre PI (mémoire descriptif, dessin, certificat...)."""
from __future__ import annotations
import enum
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class DocumentCategory(str, enum.Enum):
    specification    = "specification"   # Mémoire descriptif
    drawing          = "drawing"         # Dessin / plan
    certificate      = "certificate"     # Certificat officiel
    correspondence   = "correspondence"  # Correspondance OPIC
    fee_receipt      = "fee_receipt"     # Reçu de taxe
    assignment       = "assignment"      # Acte de cession
    other            = "other"


class IPDocument(Base):
    """Fichier joint à un titre PI (brevet, marque, droit d'auteur, dessin)."""
    __tablename__ = "ip_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Référence polymorphique — resource_type ∈ {"patent","trademark","copyright","design"}
    resource_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    resource_id: Mapped[int] = mapped_column(nullable=False, index=True)

    category: Mapped[DocumentCategory] = mapped_column(
        SAEnum(DocumentCategory), nullable=False, default=DocumentCategory.other
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<IPDocument id={self.id} type={self.resource_type}/{self.resource_id} "
            f"cat={self.category} file={self.filename}>"
        )
