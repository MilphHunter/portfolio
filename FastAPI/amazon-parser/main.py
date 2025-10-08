import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from amazon_dp_extract import JSON_FOLDER_NAME
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


RESULT_RE = re.compile(r"^results_(\d+)\.json$")

def _get_latest_json_file() -> Optional[Path]:
    """Возвращает путь к последнему JSON-файлу (по числу в имени results_<n>.json).
       Если по шаблону ничего не найдено — пробует взять самый свежий *.json по mtime.
    """
    folder = Path(JSON_FOLDER_NAME)
    if not folder.exists() or not folder.is_dir():
        return None

    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".json"]

    numbered: list[tuple[int, Path]] = []
    for f in files:
        m = RESULT_RE.match(f.name)
        if m:
            try:
                n = int(m.group(1))
                numbered.append((n, f))
            except ValueError:
                pass

    if numbered:
        numbered.sort(key=lambda t: t[0])
        return numbered[-1][1]

    if files:
        files.sort(key=lambda p: p.stat().st_mtime)
        return files[-1]

    return None


def get_data_from_file() -> Any:
    """Читает данные из последнего JSON-файла. Если ничего нет — возвращает пустой список."""
    latest = _get_latest_json_file()
    if latest is None:
        return []
    try:
        with latest.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@app.get("/")
async def profile_page(request: Request):
    """
    Рендерит главную страницу с товарами.
    Подставляет дату последнего обновления на основе имени файла.
    """
    data = get_data_from_file()
    file = _get_latest_json_file()
    dt = '2025-09-13 23:34:22+03:00'
    if file:
        file_time = str(file).split('_')[2].split('.')[0]
        dt = datetime.fromtimestamp(int(file_time), tz=ZoneInfo("Europe/Kyiv"))
    return templates.TemplateResponse(
        "main.html",
        {"request": request, "dt": dt, "products": data},
    )


@app.get("/download_json")
async def download_json():
    """
    Отправляет пользователю последний JSON-файл для скачивания.
    Если файла нет — возвращает 404.
    """
    latest = _get_latest_json_file()
    if latest is None or not latest.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(
        path=str(latest),
        media_type="application/json",
        filename=latest.name,
    )

@app.get("/get_category/{category_name}")
async def get_category(category_name: str):
    """
     Возвращает список товаров для указанной категории.
     """
    data = get_data_from_file()
    return {"products": data[category_name]}

@app.on_event("startup")
async def start_scheduler():
    """
    Хук запуска при старте приложения.
    """
    pass
