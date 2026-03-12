import enum

from sqlalchemy import Column, String, Enum, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.database import Base

class HttpMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ApiRequest(Base):
    __tablename__ = "api_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    method = Column(Enum(HttpMethod), default=HttpMethod.GET, nullable=False)
    url = Column(Text, nullable=False)
    headers = Column(JSON, nullable=True)
    body = Column(Text, nullable=True)
    auth = Column(JSON, nullable=True)
    script = Column(JSON, nullable=True)
    doc = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_result = Column(JSON, nullable=True)