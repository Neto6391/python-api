import multiprocessing
import os

bind = "0.0.0.0:8080"
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
threads = int(os.getenv("GUNICORN_THREADS", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
