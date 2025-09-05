from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_name: str = "Docs IDE API"
    api_version: str = "v1"
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["http://localhost:3000"]
    enable_hsts: bool = False  # true somente atrás de TLS
    api_keys: List[str] = []   # se vazio, autenticação desabilitada
    gzip_min_size: int = 500

    model_config = {"env_file": ".env"}

settings = Settings()
