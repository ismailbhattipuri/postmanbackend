from fastapi import  Depends, HTTPException
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.models.workspace_member import WorkspaceMember

def require_workspace_permission(permission: str):
    def checker(workspace_id: str, user=Depends(get_db), db: Session = Depends(get_db)):
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Not a workspace member")

        if not getattr(member, permission):
            raise HTTPException(status_code=403, detail="Permission denied")

        return member

    return checker