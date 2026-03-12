from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.db.database import Base


class CollectionType(str, enum.Enum):
    folder = "folder"
    file = "file"


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    # Hierarchical structure
    parent_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=True)

    name = Column(String(100), nullable=False)
    type = Column(Enum(CollectionType), nullable=False)

    # For files: links to API request
    api_request_id = Column(UUID(as_uuid=True), ForeignKey("api_requests.id"), nullable=True)

    description = Column(Text, nullable=True)
    shared = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())