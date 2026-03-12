from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AdminLogin(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: str
    message: str


from uuid import UUID

class WorkspaceInfo(BaseModel):
    id: UUID
    name: str
    type: Optional[str] = None
    owner_id: Optional[UUID] = None

    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    is_deleted: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    workspaces: Optional[list[WorkspaceInfo]] = None

    class Config:
        orm_mode = True


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserDeleteResponse(BaseModel):
    success: bool
    message: str
    user_id: str


class WorkspaceMemberRequest(BaseModel):
    user_id: str
    role: Optional[str] = "member"
