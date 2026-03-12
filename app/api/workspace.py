from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember, WorkspaceRole
from app.models.user import UserRole
from app.core.dependencies import get_current_user
from app.schemas.admin_schema import UserResponse, WorkspaceMemberRequest

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/{workspace_id}/members", response_model=List[dict])
def get_workspace_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all members of a workspace - only workspace admin can access
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Only workspace owner or project admin can view members
    if str(workspace.owner_id) != str(current_user.id):
        if current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Only workspace admin can view members")

    # Personal workspaces have no members other than owner
    if workspace.type.value == "personal":
        return [{
            "user_id": str(workspace.owner_id),
            "username": current_user.username,
            "email": current_user.email,
            "role": "admin",
            "permissions": {
                "can_create": True,
                "can_update": True,
                "can_delete": True,
                "can_view": True
            }
        }]

    # Get all members for team workspace
    members = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id).all()
    
    # Add owner as implicit member
    result = [{
        "user_id": str(workspace.owner_id),
        "username": current_user.username,
        "email": current_user.email,
        "role": "admin",
        "permissions": {
            "can_create": True,
            "can_update": True,
            "can_delete": True,
            "can_view": True
        }
    }]

    for member in members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            result.append({
                "user_id": str(member.user_id),
                "username": user.username,
                "email": user.email,
                "role": member.role.value,
                "permissions": {
                    "can_create": member.can_create,
                    "can_update": member.can_update,
                    "can_delete": member.can_delete,
                    "can_view": member.can_view
                }
            })

    return result


@router.post("/{workspace_id}/members")
def add_workspace_member(
    workspace_id: str,
    payload: WorkspaceMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a member to workspace - only workspace admin can do this
    Accepts JSON body with user_id and optional role.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if current user is workspace owner
    if str(workspace.owner_id) != str(current_user.id) and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only workspace admin can add members")

    # Prevent adding members to personal workspace
    if workspace.type.value == "personal":
        raise HTTPException(status_code=400, detail="Cannot add members to personal workspace")

    # Check if user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is already a member
    existing_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == payload.user_id
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")

    # Validate role
    try:
        workspace_role = WorkspaceRole[payload.role]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Default permissions for new members
    can_create = payload.role == "admin"
    can_update = payload.role == "admin"
    can_delete = False  # Members cannot delete by default
    can_view = True

    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=payload.user_id,
        role=workspace_role,
        can_create=can_create,
        can_update=can_update,
        can_delete=can_delete,
        can_view=can_view
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return {
        "success": True,
        "message": f"User {user.username} added to workspace",
        "member": {
            "user_id": str(new_member.user_id),
            "username": user.username,
            "email": user.email,
            "role": new_member.role.value,
            "permissions": {
                "can_create": new_member.can_create,
                "can_update": new_member.can_update,
                "can_delete": new_member.can_delete,
                "can_view": new_member.can_view
            }
        }
    }


@router.put("/{workspace_id}/members/{user_id}")
def update_member_permissions(
    workspace_id: str,
    user_id: str,
    can_create: bool = None,
    can_update: bool = None,
    can_delete: bool = None,
    can_view: bool = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update member permissions - only workspace admin can do this
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if str(workspace.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only workspace admin can update member permissions")

    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")

    # Update permissions only if provided
    if can_create is not None:
        member.can_create = can_create
    if can_update is not None:
        member.can_update = can_update
    if can_delete is not None:
        member.can_delete = can_delete
    if can_view is not None:
        member.can_view = can_view

    db.commit()
    db.refresh(member)

    return {
        "success": True,
        "message": "Member permissions updated",
        "member": {
            "user_id": str(member.user_id),
            "role": member.role.value,
            "permissions": {
                "can_create": member.can_create,
                "can_update": member.can_update,
                "can_delete": member.can_delete,
                "can_view": member.can_view
            }
        }
    }


@router.delete("/{workspace_id}/members/{user_id}")
def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from workspace - only workspace admin can do this
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if str(workspace.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Only workspace admin can remove members")

    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")

    db.delete(member)
    db.commit()

    return {
        "success": True,
        "message": "Member removed from workspace",
        "user_id": user_id
    }
