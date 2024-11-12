from pathlib import Path

UPLOAD_DIR = Path("app/admin/file_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = 'gV64m9aIzFG4qpgVphvQbPQrtAO0nM-7YwwOvu0XPt5KJOjAy4AfgLkqJXYEt'
ALGORITHM = 'HS256'
