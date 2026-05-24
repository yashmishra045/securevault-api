import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class AuditAction(str, Enum):
    SECRET_CREATED = "SECRET_CREATED"
    SECRET_READ    = "SECRET_READ"
    SECRET_UPDATED = "SECRET_UPDATED"
    SECRET_DELETED = "SECRET_DELETED"
    USER_LOGIN     = "USER_LOGIN"
    USER_LOGOUT    = "USER_LOGOUT"
    USER_CREATED   = "USER_CREATED"
    ROLE_ASSIGNED  = "ROLE_ASSIGNED"
    AUTH_FAILED    = "AUTH_FAILED"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    secret_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
    secret: Mapped["Secret | None"] = relationship("Secret", back_populates="audit_logs", primaryjoin="AuditLog.secret_name == foreign(Secret.name)", viewonly=True)
