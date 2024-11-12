from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.admin.func.general import get_time
from app.workspace.models import File, Tag


# Define the path to save the file, depending on its type
async def path_to_save(file):
    img = ['.jpeg', '.jpg', '.jpe', '.jfif', '.ico', '.png', '.gif', '.svg', '.tiff', '.tif', '.webp', '.eps']
    video = ['.mov', '.mpeg4', '.mp4', '.MP4', '.avi', '.wmv', '.mpegps', '.flv', '.3gpp', 'webm']
    audio = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.m4r', '.aiff', '.wma', '.amr', '.midi']
    extension = file.filename[file.filename.rfind('.'):]

    if extension in img:
        path = Path("app/admin/file_uploads/image")
    elif extension in video:
        path = Path("app/admin/file_uploads/video")
    elif extension in audio:
        path = Path("app/admin/file_uploads/audio")
    else:
        path = Path("app/admin/file_uploads/other")

    path.mkdir(parents=True, exist_ok=True)
    return path


# Collect File Info
async def get_file_info(db: Session, skip: int = 0, limit: int = 10, query: str = "", tag_titles: list = None,
                        workspace: bool = False):
    # If response was sanded from workspace and it may have hidden files
    if workspace:
        base_query = db.query(File).filter(File.status == True)
    else:
        base_query = db.query(File)
    # If response sanded with tags
    if tag_titles:
        base_query = base_query.join(File.tags).filter(Tag.title.in_(tag_titles)) \
            .group_by(File.id).having(func.count(Tag.id) == len(tag_titles))
        files = base_query.offset(skip).limit(limit).all()
    else:
        # If response is search
        if query:
            files = base_query.filter(
                (File.title.ilike(f"%{query}%")) | (File.tags.any(Tag.title == query))
            ).offset(skip).limit(limit).all()
        else:
            files = base_query.offset(skip).limit(limit).all()

    file_id = [i.id for i in files]
    file_title = [i.title for i in files]
    downloaded_times = [i.downloaded_times for i in files]
    created_at = await get_time(files)
    size = [i.size for i in files]
    tags = [', '.join([tag.title for tag in i.tags]) for i in files]
    status = [i.status for i in files]
    type = [await file_type(i.title) for i in files]
    users_info = [n for n in zip(file_id, file_title, downloaded_times, created_at, size, tags, status, type)]
    return users_info


# Get files count
async def get_file_count(db: Session, query: str = None, tag_titles: list = None, workspace: bool = False) -> int:
    base_query = db.query(File.id)

    if workspace:
        base_query = base_query.filter(File.status == True)

    if tag_titles:
        base_query = base_query.join(File.tags).filter(Tag.title.in_(tag_titles))

    if query:
        base_query = base_query.filter(File.title.ilike(f"%{query}%"))

    return base_query.distinct().count()  # Используем distinct, чтобы подсчитать уникальные файлы


# Get file_type
async def file_type(filename):
    img = ['.jpeg', '.jpg', '.jpe', '.jfif', '.ico', '.png', '.gif', '.svg', '.tiff', '.tif', '.webp', '.eps']
    video = ['.mov', '.mpeg4', '.mp4', '.MP4', '.avi', '.wmv', '.mpegps', '.flv', '.3gpp', 'webm']
    audio = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.m4r', '.aiff', '.wma', '.amr', '.midi']
    extension = filename[filename.rfind('.'):]
    if extension in img:
        return 'image'
    elif extension in video:
        return 'video'
    elif extension in audio:
        return 'audio'
    else:
        return 'other'
