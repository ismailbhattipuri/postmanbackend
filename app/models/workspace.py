from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.db.database import Base

class WorkspaceType(str, enum.Enum):
    personal = "personal"
    team = "team"


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    type = Column(Enum(WorkspaceType), default=WorkspaceType.personal)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())