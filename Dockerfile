FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional minimal)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY gunicorn_conf.py ./gunicorn_conf.py

EXPOSE 8080

# gunicorn + uvicorn workers
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
