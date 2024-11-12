from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.models import User
from app.database import get_db


# Function for get user information
async def get_user_info(db: Session = Depends(get_db), skip: int = 0, limit: int = 10, query: str = ""):
    # Check is it search response
    user = db.query(User).filter(User.name.ilike(f"%{query}%")).offset(skip).limit(limit).all() if query else db.query(
        User).offset(skip).limit(limit).all()
    users_name = [i.name for i in user]
    users_email = [i.email for i in user]
    users_latest_activity = []
    for i in user:
        minute = i.latest_activity.minute if i.latest_activity.minute > 9 else f'0{i.latest_activity.minute}'
        hour = i.latest_activity.hour if i.latest_activity.hour > 9 else f'0{i.latest_activity.hour}'
        day = i.latest_activity.day if i.latest_activity.day > 9 else f'0{i.latest_activity.day}'
        month = i.latest_activity.month if i.latest_activity.month > 9 else f'0{i.latest_activity.month}'
        year = i.latest_activity.year if i.latest_activity.year > 9 else f'0{i.latest_activity.year}'
        users_latest_activity.append(f"{day}-{month}-{year} at {hour}:{minute}")
    users_files_downloaded = [i.files_downloaded for i in user]
    users_info = [n for n in zip(users_name, users_email, users_latest_activity, users_files_downloaded)]
    return users_info


# Get count of users
async def get_user_count(db: Session, query: str = "") -> int:
    base_query = db.query(func.count(User.id))
    if query:
        base_query = base_query.filter(User.name.ilike(f"%{query}%"))
    return base_query.scalar()
