from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.collection import Collection, CollectionType
from app.schemas.collection_schema import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
    CollectionMove,
    ApiRequestCreate,
    ApiRequestResponse,
    ApiRequestUpdate,
    ApiRequestExecute,
    EnvironmentVariableCreate,
    EnvironmentVariableResponse,
    EnvironmentVariableUpdate,
    PluginCreate,
    PluginUpdate,
    PluginResponse,
)
from app.models.api_request import ApiRequest
from app.models.environment import EnvironmentVariable
from app.models.plugin import Plugin
from app.core.dependencies import get_current_user

router = APIRouter(prefix="", tags=["Collections"])


def get_member_record(db: Session, workspace_id: str, user: User) -> Optional[WorkspaceMember]:
    if user.role == UserRole.admin:
        return None
    return (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )


def ensure_permission(
    db: Session,
    workspace_id: str,
    user: User,
    action: str,
) -> None:
    """Raise HTTPException if user lacks the given action permission."""
    if user.role == UserRole.admin:
        return
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # owner always allowed
    if str(workspace.owner_id) == str(user.id):
        return

    member = get_member_record(db, workspace_id, user)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    allowed = getattr(member, f"can_{action}", False)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"User cannot {action} in this workspace")


@router.get("/workspaces/{workspace_id}/collections", response_model=List[CollectionResponse])
def list_collections(
    workspace_id: str,
    parent_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_permission(db, workspace_id, current_user, "view")
    query = db.query(Collection).filter(Collection.workspace_id == workspace_id)
    if parent_id is None:
        query = query.filter(Collection.parent_id.is_(None))
    else:
        query = query.filter(Collection.parent_id == parent_id)
    items = query.all()
    return items


@router.post("/workspaces/{workspace_id}/collections", response_model=CollectionResponse)
def create_collection(
    workspace_id: str,
    payload: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ensure_permission(db, workspace_id, current_user, "create")
    # validation is done by pydantic
    new = Collection(
        workspace_id=workspace_id,
        parent_id=payload.parent_id,
        name=payload.name,
        type=CollectionType(payload.type),
        api_request_id=payload.api_request_id,
        description=payload.description,
        shared=payload.shared,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coll = db.query(Collection).filter(Collection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    ensure_permission(db, str(coll.workspace_id), current_user, "view")
    # optionally fetch children
    children = db.query(Collection).filter(Collection.parent_id == coll.id).all()
    coll.children = children
    return coll


@router.put("/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: str,
    payload: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coll = db.query(Collection).filter(Collection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    ensure_permission(db, str(coll.workspace_id), current_user, "update")
    if payload.name is not None:
        coll.name = payload.name
    if payload.description is not None:
        coll.description = payload.description
    if payload.shared is not None:
        coll.shared = payload.shared
    db.commit()
    db.refresh(coll)
    return coll


@router.post("/collections/{collection_id}/move", response_model=CollectionResponse)
def move_collection(
    collection_id: str,
    payload: CollectionMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coll = db.query(Collection).filter(Collection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    ensure_permission(db, str(coll.workspace_id), current_user, "update")
    # verify new parent belongs to same workspace
    if payload.new_parent_id:
        parent = db.query(Collection).filter(Collection.id == payload.new_parent_id).first()
        if not parent or str(parent.workspace_id) != str(coll.workspace_id):
            raise HTTPException(status_code=400, detail="Invalid new parent")
    coll.parent_id = payload.new_parent_id
    db.commit()
    db.refresh(coll)
    return coll


@router.delete("/collections/{collection_id}")
def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    coll = db.query(Collection).filter(Collection.id == collection_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    ensure_permission(db, str(coll.workspace_id), current_user, "delete")
    # cascade delete children
    def _delete_recursive(c):
        for child in db.query(Collection).filter(Collection.parent_id == c.id).all():
            _delete_recursive(child)
            db.delete(child)
        db.delete(c)
    _delete_recursive(coll)
    db.commit()
    return {"success": True}

# ApiRequest endpoints
@router.post("/api-requests", response_model=ApiRequestResponse)
def create_api_request(
    payload: ApiRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = ApiRequest(**payload.dict())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@router.get("/api-requests/{request_id}", response_model=ApiRequestResponse)
def get_api_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(ApiRequest).filter(ApiRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="API request not found")
    return req

@router.put("/api-requests/{request_id}", response_model=ApiRequestResponse)
def update_api_request(request_id: str, payload: ApiRequestUpdate, db: Session = Depends(get_db)):
    req = db.query(ApiRequest).filter(ApiRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="API request not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return req

@router.delete("/api-requests/{request_id}")
def delete_api_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(ApiRequest).filter(ApiRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="API request not found")
    db.delete(req)
    db.commit()
    return {"success": True}

@router.post("/api-requests/{request_id}/execute")
def execute_api_request(request_id: str, payload: ApiRequestExecute, db: Session = Depends(get_db)):
    # placeholder: simply return request details and given env
    req = db.query(ApiRequest).filter(ApiRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="API request not found")
    return {"success": True, "request": req, "env": payload.environment_variables}

# Environment endpoints
@router.get("/workspaces/{workspace_id}/environments", response_model=List[EnvironmentVariableResponse])
def list_environments(workspace_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_permission(db, workspace_id, current_user, "view")
    return db.query(EnvironmentVariable).filter(EnvironmentVariable.workspace_id == workspace_id).all()

@router.post("/workspaces/{workspace_id}/environments", response_model=EnvironmentVariableResponse)
def create_environment(workspace_id: str, payload: EnvironmentVariableCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_permission(db, workspace_id, current_user, "create")
    env = EnvironmentVariable(workspace_id=workspace_id, **payload.dict())
    db.add(env)
    db.commit()
    db.refresh(env)
    return env

@router.put("/environments/{env_id}", response_model=EnvironmentVariableResponse)
def update_environment(env_id: str, payload: EnvironmentVariableUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    env = db.query(EnvironmentVariable).filter(EnvironmentVariable.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    ensure_permission(db, str(env.workspace_id), current_user, "update")
    for f,v in payload.dict(exclude_unset=True).items(): setattr(env,f,v)
    db.commit(); db.refresh(env)
    return env

@router.delete("/environments/{env_id}")
def delete_environment(env_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    env = db.query(EnvironmentVariable).filter(EnvironmentVariable.id == env_id).first()
    if not env: raise HTTPException(status_code=404, detail="Environment not found")
    ensure_permission(db, str(env.workspace_id), current_user, "delete")
    db.delete(env); db.commit()
    return {"success": True}

# Plugin endpoints
@router.get("/workspaces/{workspace_id}/plugins", response_model=List[PluginResponse])
def list_plugins(workspace_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_permission(db, workspace_id, current_user, "view")
    return db.query(Plugin).filter(Plugin.workspace_id == workspace_id).all()

@router.post("/workspaces/{workspace_id}/plugins", response_model=PluginResponse)
def create_plugin(workspace_id: str, payload: PluginCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_permission(db, workspace_id, current_user, "create")
    plugin = Plugin(workspace_id=workspace_id, **payload.dict())
    db.add(plugin); db.commit(); db.refresh(plugin)
    return plugin

@router.put("/plugins/{plugin_id}", response_model=PluginResponse)
def update_plugin(plugin_id: str, payload: PluginUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin: raise HTTPException(status_code=404, detail="Plugin not found")
    ensure_permission(db, str(plugin.workspace_id), current_user, "update")
    for f,v in payload.dict(exclude_unset=True).items(): setattr(plugin,f,v)
    db.commit(); db.refresh(plugin)
    return plugin

@router.delete("/plugins/{plugin_id}")
def delete_plugin(plugin_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plugin = db.query(Plugin).filter(Plugin.id == plugin_id).first()
    if not plugin: raise HTTPException(status_code=404, detail="Plugin not found")
    ensure_permission(db, str(plugin.workspace_id), current_user, "delete")
    db.delete(plugin); db.commit()
    return {"success": True}