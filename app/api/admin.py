from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.core.security import hash_password, verify_password
from app.core.jwt_handler import create_access_token
from app.schemas.admin_schema import AdminLogin, UserResponse, UserUpdateRequest
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

# Project admin credentials (should be set in .env in production)
ADMIN_EMAIL = "admin@ownpostman.com"
ADMIN_PASSWORD_HASH = None  # Will be set on first login

admin_logged_in = False


@router.post("/login")
def admin_login(credentials: AdminLogin, db: Session = Depends(get_db)):
    """
    Project admin login - one time setup, then unlimited edits
    First login creates the admin user, subsequent logins use JWT
    """
    global admin_logged_in

    # Check if admin user exists
    admin_user = db.query(User).filter(User.email == ADMIN_EMAIL).first()

    if not admin_user:
        # First login - create admin user
        if credentials.email != ADMIN_EMAIL or credentials.password != "admin123":
            raise HTTPException(status_code=401, detail="Invalid admin credentials")

        admin_user = User(
            username="admin",
            email=ADMIN_EMAIL,
            password_hash=hash_password(credentials.password),
            role=UserRole.admin,
            is_deleted=False
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        admin_logged_in = True

    else:
        # Existing admin user - verify password
        if not verify_password(credentials.password, admin_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")

        if admin_user.is_deleted:
            raise HTTPException(status_code=403, detail="Admin account is deleted")

    token = create_access_token({"user_id": str(admin_user.id), "role": "admin"})

    return {
        "success": True,
        "message": "Admin login successful",
        "token": token,
        "user": {
            "id": str(admin_user.id),
            "username": admin_user.username,
            "email": admin_user.email,
            "role": admin_user.role.value
        }
    }


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users - only project admin can access
    Returns all users including soft-deleted ones
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admin can access this endpoint")

    users = db.query(User).filter(User.is_deleted == False).all()
    # fetch workspaces once and group by owner
    all_ws = db.query(Workspace).all()
    ws_by_owner = {}
    for w in all_ws:
        ws_by_owner.setdefault(str(w.owner_id), []).append(w)

    result = []
    for u in users:
        user_dict = u.__dict__.copy()
        user_dict.pop("_sa_instance_state", None)
        owner_id_str = str(u.id)
        user_dict["workspaces"] = ws_by_owner.get(owner_id_str, [])
        result.append(user_dict)

    return result


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific user - only admin can access"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admin can access this endpoint")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # attach workspaces
    workspaces = db.query(Workspace).filter(Workspace.owner_id == user.id).all()
    user_dict = user.__dict__.copy()
    user_dict.pop("_sa_instance_state", None)
    user_dict["workspaces"] = workspaces
    return user_dict


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    user_update: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user details - only admin can access"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admin can access this endpoint")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.username:
        existing = db.query(User).filter(User.username == user_update.username).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_update.username

    if user_update.email:
        existing = db.query(User).filter(User.email == user_update.email).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_update.email

    if user_update.role:
        user.role = UserRole[user_update.role]

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "User updated successfully",
        "user": user
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a user - only admin can access
    Prevents user from self-deletion
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admin can access this endpoint")

    # Prevent self-deletion
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_deleted:
        raise HTTPException(status_code=400, detail="User is already deleted")

    # Soft delete
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": "User deleted successfully",
        "user_id": user_id
    }
