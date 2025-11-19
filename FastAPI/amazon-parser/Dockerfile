FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Kyiv

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install

COPY . .

RUN mkdir -p /app/static /app/templates

EXPOSE 8000

CMD ["/bin/sh","-lc","uvicorn main:app --host 0.0.0.0 --port 8080"]
