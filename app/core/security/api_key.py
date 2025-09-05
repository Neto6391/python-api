from fastapi import Depends, Header, HTTPException, status
from typing import Optional
from app.core.config.settings import settings

async def api_key_auth(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    # Se não há chaves configuradas, autenticação desabilitada
    if not settings.api_keys:
        return
    if x_api_key is None or x_api_key not in settings.api_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
