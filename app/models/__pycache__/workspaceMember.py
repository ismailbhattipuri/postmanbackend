from sqlalchemy import Column, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base

class WorkspaceRole(str, enum.Enum):
    admin = "admin"
    member = "member"

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.member)

    can_create = Column(Boolean, default=True)
    can_update = Column(Boolean, default=True)
    can_delete = Column(Boolean, default=True)
    can_view = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())