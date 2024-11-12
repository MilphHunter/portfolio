import json

from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import HTMLResponse

from app.admin.func.admin_func import get_user_info, get_user_count
from app.admin.func.files_func import path_to_save, get_file_info, get_file_count
from app.admin.func.tag_func import get_tag_info, get_tag_count
from app.auth.models import User
from app.auth.routes import admin_required
from app.database import get_db
from app.workspace.models import Tag, File, DownloadFilesHistory
from app.workspace.schemas import TagResponse
from main import templates

router = APIRouter()


# Return list of users, including search, pagination
@router.get("/users", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def get_users_admin(request: Request, db: Session = Depends(get_db),
                          page: int = 1, per_page: int = 14,
                          query: str = ""):
    skip = (page - 1) * per_page
    # if search_response
    if query:
        users_info = await get_user_info(db, skip=skip, limit=per_page, query=query)
        total_users = await get_user_count(db, query=query)
    else:
        users_info = await get_user_info(db, skip=skip, limit=per_page)
        total_users = await get_user_count(db)

    total_pages = (total_users + per_page - 1) // per_page

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users_info": users_info,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
    })


# Ban user by email (unique)
@router.delete("/users/ban/{email}", status_code=200, dependencies=[Depends(admin_required)])
async def delete_user(email: str, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    last_user_email = data.get("last_user_email")

    user = db.query(User).filter(User.email == email).first()

    if last_user_email:
        last_user = db.query(User).filter(User.email == last_user_email).first()
        next_user = db.query(User).filter(User.id > last_user.id).order_by(User.id).first()
        if not user:
            user = db.query(User).filter(User.email == last_user_email).first()
    else:
        next_user = db.query(User).filter(User.id > user.id).order_by(User.id).first()

    if user:
        db.delete(user)
        db.commit()

        if next_user:
            return {
                "message": "User deleted",
                "next_user": {
                    "name": next_user.name,
                    "email": next_user.email,
                    "latest_activity": next_user.latest_activity,
                    "files_downloaded": next_user.files_downloaded,
                }
            }
        else:
            return {"message": "User deleted", "next_user": None}
    else:
        raise HTTPException(status_code=404, detail="User not found")


# Return list of tags, including search, pagination
@router.get("/tags", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def get_tags_admin(request: Request, db: Session = Depends(get_db),
                         page: int = 1, per_page: int = 14,
                         query: str = ""):
    skip = (page - 1) * per_page
    # if search_response
    if query:
        tags_info = await get_tag_info(db, skip=skip, limit=per_page, query=query)
        total_tags = await get_tag_count(db, query=query)
    else:
        tags_info = await get_tag_info(db, skip=skip, limit=per_page)
        total_tags = await get_tag_count(db)

    total_pages = (total_tags + per_page - 1) // per_page
    return templates.TemplateResponse("admin-tags.html", {
        "request": request,
        "tags_info": tags_info,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
    })


# Tag create response
@router.post("/tags/create-tag", response_model=TagResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(admin_required)])
def create_tag(
        title: str = Form(max_length=30),
        db: Session = Depends(get_db),
):
    db_tag = db.query(Tag).filter(Tag.title == title).first()
    if db_tag:
        raise HTTPException(status_code=422, detail="tag already created")

    new_tag = Tag(
        title=title
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return new_tag


# Tag upgrade response
@router.put("/tags/upgrade/{currentTagTitle}", dependencies=[Depends(admin_required)])
async def update_tag(currentTagTitle: str, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    new_title = data.get("title")

    tag = db.query(Tag).filter(Tag.title == currentTagTitle).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag.title = new_title
    db.commit()

    return {"message": "Tag updated"}


# Tag delete response
@router.delete("/tags/delete/{tagTitleToDelete}", status_code=200, dependencies=[Depends(admin_required)])
async def delete_tag(tagTitleToDelete: str, request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    last_tag_title = data.get("last_tag_title")

    tag = db.query(Tag).filter(Tag.title == tagTitleToDelete).first()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if last_tag_title:
        last_user = db.query(Tag).filter(Tag.title == last_tag_title).first()
        next_tag = db.query(Tag).filter(Tag.id > last_user.id).order_by(Tag.id).first()
    else:
        next_tag = db.query(Tag).filter(Tag.id > tag.id).order_by(Tag.id).first()

    db.delete(tag)
    db.commit()

    if next_tag:
        return {
            "message": "Tag deleted",
            "next_tag": {
                "title": next_tag.title,
                "count_files": next_tag.count_files,
                "created_at": next_tag.created_at.strftime("%Y-%m-%d at %H:%M"),
                "files_downloaded": next_tag.files_downloaded,
            }
        }
    else:
        return {"message": "Tag deleted", "next_tag": None}


# Return list of files, including search, pagination
@router.get("/files", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def get_files_admin(request: Request, db: Session = Depends(get_db),
                          page: int = 1, per_page: int = 14,
                          query: str = ""):
    skip = (page - 1) * per_page
    if query:
        files_info = await get_file_info(db, skip=skip, limit=per_page, query=query)
        total_files = await get_file_count(db, query=query)
    else:
        files_info = await get_file_info(db, skip=skip, limit=per_page)
        total_files = await get_file_count(db)

    download_history = {}
    for file in files_info:
        file_id = file[0]
        history = db.query(DownloadFilesHistory).filter(DownloadFilesHistory.file_id == file_id).all()
        if history:
            download_history[file_id] = [
                [h.file.title, h.user.email, h.download_time.strftime("%Y-%m-%d at %H:%M")]
                for h in history
            ]
        else:
            download_history[file_id] = []

    total_pages = (total_files + per_page - 1) // per_page
    return templates.TemplateResponse("admin-files.html", {
        "request": request,
        "files_info": files_info,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page,
        "download_histories": json.dumps(download_history),  # Передаем как строку
    })


# File create
@router.post("/files/create-file", status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
async def create_file(
        title: str = Form(...),
        tags: str = Form(...),
        status: str = Form(...),
        file: UploadFile = Form(...),
        db: Session = Depends(get_db)
):
    db_file = db.query(File).filter(File.title == title).first()
    if db_file:
        raise HTTPException(status_code=422, detail="File with this title already exists")

    tag_titles = [tag.strip() for tag in tags.split(",")]
    # If new tags were mentioned during creation - we create them automatically
    db_tags = []
    for tag_title in tag_titles:
        if len(tag_title) >= 3:
            db_tag = db.query(Tag).filter(Tag.title == tag_title).first()
            if not db_tag:
                new_tag = Tag(title=tag_title, count_files=1)
                db.add(new_tag)
                db.commit()
                db.refresh(new_tag)
                db_tag = new_tag
            else:
                db_tag.count_files += 1
                db.commit()
            db_tags.append(db_tag)
    file_path = await path_to_save(file) / file.filename
    new_file = File(
        title=title,
        file=file.filename,
        path_to_file=str(file_path),
        downloaded_times=0,
        size=round(file.size / 1_048_576.0, 1),
        tags=db_tags,
        status=(status == 'active')
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"message": "File uploaded successfully", "file_id": new_file.id}


# File update
@router.post('/files/update-file', dependencies=[Depends(admin_required)])
async def update_file(request: Request, file: UploadFile = None, db: Session = Depends(get_db)):
    try:
        file_data = await request.json()
        file_record = db.query(File).filter(File.id == int(file_data['id'])).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")

        if file_data['title']:
            file_record.title = file_data['title']

        if file_data['tags']:
            tag_titles = [tag.strip() for tag in file_data['tags']]
            db_tags = []
            for tag_title in tag_titles:
                if len(tag_title) >= 3:
                    db_tag = db.query(Tag).filter(Tag.title == tag_title).first()
                    if not db_tag:
                        new_tag = Tag(title=tag_title, count_files=1)
                        db.add(new_tag)
                        db.commit()
                        db.refresh(new_tag)
                        db_tag = new_tag
                    else:
                        db_tag.count_files += 1
                        db.commit()
                    db_tags.append(db_tag)
            file_record.tags = db_tags

        if file_data['status'] is not None:
            file_record.status = file_data['status']

        if file:
            file_path = await path_to_save(file) / file.filename
            file_record.path_to_file = str(file_path)
            file_record.size = round(file.size / 1_048_576.0, 1)

            with open(file_path, "wb") as f:
                f.write(await file.read())

        db.commit()
        db.refresh(file_record)

        return {"success": True, "message": "File updated successfully", "id": file_record.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# File delete from db
@router.delete('/files/delete-file/{file_id}', dependencies=[Depends(admin_required)])
async def delete_file(file_id: int, db: Session = Depends(get_db)):
    file_record = db.query(File).filter(File.id == file_id).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        db.delete(file_record)
        db.commit()

        return {"success": True, "message": "File deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
