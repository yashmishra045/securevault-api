import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Secret(Base):
    __tablename__ = "secrets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_value: Mapped[str] = mapped_column(String, nullable=False)
    iv: Mapped[str] = mapped_column(String(24), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner: Mapped["User"] = relationship("User", back_populates="secrets")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="secret", primaryjoin="AuditLog.secret_name == foreign(Secret.name)", viewonly=True)
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_secret_name"), Index("ix_secrets_user_id_name", "user_id", "name"),)
