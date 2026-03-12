from sqlalchemy import Column, String, Enum, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.db.database import Base


class VariableType(str, enum.Enum):
    string = "string"
    secret = "secret"
    number = "number"
    bool = "bool"


class EnvironmentVariable(Base):
    __tablename__ = "environment_variables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    name = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)
    type = Column(Enum(VariableType), default=VariableType.string)

    desc = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())