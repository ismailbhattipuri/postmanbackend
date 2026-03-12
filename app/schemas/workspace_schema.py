from app.schemas.user_schema import UserResponse
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class WorkspaceBase(BaseModel):
    name: str
    type: str

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    type: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

class WorkspaceDeleteResponse(BaseModel):
    message: str

class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]

class SignupResponse(BaseModel):
    user: UserResponse
    workspace: WorkspaceResponse
