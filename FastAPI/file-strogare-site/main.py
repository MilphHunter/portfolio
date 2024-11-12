from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic.v1 import BaseSettings
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

from app.auth.routes import router as auth_router
from app.workspace.routes import router as workspace_router
from app.admin.routes import router as admin_router
from app.database import get_db

from config import UPLOAD_DIR as UD

app = FastAPI(title="My Project", version="1.0.0")

UPLOAD_DIR = UD

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(workspace_router, prefix="", tags=["workspace"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup():
    get_db()


@app.on_event("shutdown")
async def shutdown():
    pass
