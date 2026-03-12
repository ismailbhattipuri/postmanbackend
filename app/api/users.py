from app.core.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.schemas.user_schema import UserUpdate
from app.core.security import hash_password
from sqlalchemy.orm import Session
from app.db.database import get_db

router = APIRouter(prefix="/users", tags=["Authentication"])

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    print(current_user)
    return current_user

@router.put("/me")
def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check for username uniqueness if updating
    if user_update.username and user_update.username != current_user.username:
        existing = db.query(User).filter(User.username == user_update.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

    # Check for email uniqueness if updating
    if user_update.email and user_update.email != current_user.email:
        existing = db.query(User).filter(User.email == user_update.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

    # Update fields
    if user_update.username:
        current_user.username = user_update.username
    if user_update.email:
        current_user.email = user_update.email
    if user_update.password:
        current_user.password_hash = hash_password(user_update.password)

    db.commit()
    db.refresh(current_user)
    return current_user

