from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models.workspace import WorkspaceType

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    workspace_name: str
    workspace_type: WorkspaceType

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr

    class Config:
        from_attributes = True
