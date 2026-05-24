import uuid
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Permission:
    SECRET_CREATE = "secret:create"
    SECRET_READ   = "secret:read"
    SECRET_UPDATE = "secret:update"
    SECRET_DELETE = "secret:delete"
    USER_MANAGE   = "user:manage"
    AUDIT_VIEW    = "audit:view"
    ROLE_ASSIGN   = "role:assign"

ROLE_DEFAULTS = {
    "admin": ["secret:create","secret:read","secret:update","secret:delete","user:manage","audit:view","role:assign"],
    "editor": ["secret:create","secret:read","secret:update","secret:delete"],
    "viewer": ["secret:read"],
}

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    permissions: Mapped[list] = mapped_column(JSON, default=list)
    users: Mapped[list["User"]] = relationship("User", back_populates="role")

    def has_permission(self, permission: str) -> bool:
        return permission in (self.permissions or [])
