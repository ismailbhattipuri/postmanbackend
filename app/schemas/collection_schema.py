from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class CollectionBase(BaseModel):
    name: str
    type: str  # "folder" or "file"
    description: Optional[str] = None
    shared: Optional[bool] = False


class CollectionCreate(CollectionBase):
    parent_id: Optional[UUID] = None
    api_request_id: Optional[UUID] = None  # Only for files


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    shared: Optional[bool] = None


class CollectionResponse(CollectionBase):
    id: UUID
    workspace_id: UUID
    parent_id: Optional[UUID] = None
    api_request_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: Optional[List['CollectionResponse']] = None

    class Config:
        orm_mode = True


class CollectionMove(BaseModel):
    new_parent_id: Optional[UUID] = None  # None means move to root


class ApiRequestBase(BaseModel):
    name: str
    method: str
    url: str
    headers: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None


class ApiRequestCreate(ApiRequestBase):
    pass


class ApiRequestUpdate(BaseModel):
    name: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None


class ApiRequestResponse(ApiRequestBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_run_result: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class ApiRequestExecute(BaseModel):
    environment_variables: Optional[Dict[str, str]] = None


class EnvironmentVariableBase(BaseModel):
    name: str
    value: str
    type: Optional[str] = "string"
    desc: Optional[str] = None


class EnvironmentVariableCreate(EnvironmentVariableBase):
    pass


class EnvironmentVariableUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    type: Optional[str] = None
    desc: Optional[str] = None


class EnvironmentVariableResponse(EnvironmentVariableBase):
    id: UUID
    workspace_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class PluginBase(BaseModel):
    name: str
    module_path: str
    enabled: Optional[bool] = True
    config: Optional[Dict[str, Any]] = None
    desc: Optional[str] = None


class PluginCreate(PluginBase):
    workspace_id: Optional[UUID] = None


class PluginUpdate(BaseModel):
    name: Optional[str] = None
    module_path: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    desc: Optional[str] = None


class PluginResponse(PluginBase):
    id: UUID
    workspace_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True