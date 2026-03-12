from app.db.database import Base
from fastapi import FastAPI
from app.api import auth, users, admin, workspace, collections

from app.db.database import engine
from app.db.init_db import init_db

# initialize database and ensure schema is up-to-date
init_db()

app = FastAPI(
    title="Own Postman Backend",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(workspace.router)
app.include_router(collections.router)

@app.get("/")
async def root():
    return {"message": "Own Postman backend running"}
