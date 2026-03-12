from uuid import uuid4
from app.schemas.workspace_schema import SignupResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.user_schema import UserCreate, UserLogin
from app.core.security import hash_password, verify_password
from app.core.jwt_handler import create_access_token
from app.models.user import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):

    existing_user = (
        db.query(User)
        .filter((User.email == user_data.email) | (User.username == user_data.username))
        .first()
    )

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        if existing_user.username == user_data.username:
            raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        id=uuid4(),
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password)
    )

    db.add(new_user)
    db.flush()  # get user id without committing

    workspace = Workspace(
        id=uuid4(),
        name=user_data.workspace_name or f"{user_data.username}'s workspace",
        owner_id=new_user.id,
        type=user_data.workspace_type
    )

    db.add(workspace)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"user_id": str(new_user.id)})

    return {
        "success": True,
        "message": "Signup successful",
        "token": token,
        "user": new_user,
        "workspace": workspace
    }
# Admin credentials (could later be moved to env)
ADMIN_EMAIL = "ibhattipuri@gmail.com"
ADMIN_PASSWORD = "adminji@123"


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # if the login attempt is for the project admin email
    if user.email == ADMIN_EMAIL:
        admin_user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        # create the admin if it doesn't exist yet
        if not admin_user:
            if user.password != ADMIN_PASSWORD:
                raise HTTPException(status_code=401, detail="Invalid admin credentials")

            admin_user = User(
                username="admin",
                email=ADMIN_EMAIL,
                password_hash=hash_password(user.password),
                role=UserRole.admin,
                is_deleted=False
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            token = create_access_token({"user_id": str(admin_user.id), "role": "admin"})
            return {"success": True, "message": "Admin created", "token": token, "user": admin_user}
        # admin already exists, just verify password
        if not verify_password(user.password, admin_user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email/password")

        token = create_access_token({"user_id": str(admin_user.id), "role": "admin"})
        return {"success": True, "message": "Admin login successful", "token": token, "user": admin_user}

    # regular user login path
    db_user = (
        db.query(User)
        .filter(User.email == user.email, User.is_deleted == False)
        .first()
    )
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not found or account deleted")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email/password")

    token = create_access_token({"user_id": str(db_user.id)})

    db_workspace = db.query(Workspace).filter(Workspace.owner_id == db_user.id).all()

    res = {"success": True, "token": token, "user": db_user}
    if db_workspace:
        res["workspace"] = db_workspace

    return res
