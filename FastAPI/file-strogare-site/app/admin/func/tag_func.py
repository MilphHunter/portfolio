from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.workspace.models import Tag

from app.admin.func.general import get_time


# Collecting info about tags
async def get_tag_info(db: Session = Depends(get_db), skip: int = 0, limit: int = 10, query: str = ""):
    tag = db.query(Tag).filter(Tag.title.ilike(f"%{query}%")).offset(skip).limit(limit).all() if query else db.query(
        Tag).offset(skip).limit(limit).all()
    tags_title = [i.title for i in tag]
    tags_count_files = [i.count_files for i in tag]
    tags_created_at = await get_time(tag)
    tags_files_downloaded = [i.files_downloaded for i in tag]
    users_info = [n for n in zip(tags_title, tags_count_files, tags_created_at, tags_files_downloaded)]
    return users_info


# Get count of tags
async def get_tag_count(db: Session, query: str = "") -> int:
    base_query = db.query(func.count(Tag.id))
    if query:
        base_query = base_query.filter(Tag.title.ilike(f"%{query}%"))
    return base_query.scalar()
