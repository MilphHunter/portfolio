import os
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import HTMLResponse, FileResponse

from app.admin.func.files_func import get_file_info, get_file_count
from app.auth.models import User
from app.auth.routes import require_authentication, get_current_user
from app.database import get_db
from app.workspace.models import Tag, File, DownloadFilesHistory
from main import templates

router = APIRouter()


#  Provide the user with all available files and tags
@router.get("/workspace", response_class=HTMLResponse)
async def get_files(
        request: Request,
        db: Session = Depends(get_db),
        page: int = 1,
        per_page: int = 10,
        query: str = "",
        _: None = Depends(require_authentication)
):
    skip = (page - 1) * per_page

    if query:
        files_info = await get_file_info(db, skip=skip, limit=per_page, query=query, workspace=True)
        total_files = await get_file_count(db, query=query, workspace=True)
    else:
        files_info = await get_file_info(db, skip=skip, limit=per_page, workspace=True)
        total_files = await get_file_count(db, workspace=True)

    total_pages = (total_files + per_page - 1) // per_page

    tags = db.query(Tag).order_by(desc(Tag.count_files)).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "files_info": files_info,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
        "tags": tags
    })


# Return only files corresponding to the passed tags
@router.get("/workspace/tag", response_class=HTMLResponse)
async def get_files_by_tags(request: Request, tags: str = "", db: Session = Depends(get_db),
                            page: int = 1, per_page: int = 10, _: None = Depends(require_authentication)):
    skip = (page - 1) * per_page

    tag_titles = tags.split(',') if tags else []
    tag_titles = [i.split('\n')[0] for i in tag_titles]

    files_info = await get_file_info(db, skip=skip, limit=per_page, tag_titles=tag_titles, workspace=True)
    total_files = await get_file_count(db, tag_titles=tag_titles, workspace=True)

    total_pages = (total_files + per_page - 1) // per_page

    tags = db.query(Tag).order_by(desc(Tag.count_files)).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "files_info": files_info,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
        "tags": tags,
        "tag_name": f"{', '.join(tag_titles)} {'tags' if len(tag_titles) > 1 else 'tag'}"
    })


# Download file function
@router.get("/files/download/{file_id}", response_class=FileResponse)
async def download_file(
        file_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    file_path = file.path_to_file
    file_name = os.path.basename(file_path)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The file is not available on the server.")

    download_history_entry = DownloadFilesHistory(
        file_id=file.id,
        user_id=current_user.id,
        download_time=datetime.now()
    )
    db.add(download_history_entry)
    current_user.files_downloaded += 1
    file.downloaded_times += 1
    for tag in file.tags:
        tag.files_downloaded += 1

    db.commit()

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{file_name}"
    }

    return FileResponse(file_path, headers=headers, media_type="application/octet-stream")
